"""The Backup admin section: schedule, health and the guarded restore."""

import socket
from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.shortcuts import reverse
from django.utils import timezone

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

from arabase.backup.handler import (
    HEALTH_DISABLED,
    HEALTH_LAST_FAILED,
    HEALTH_MISCONFIGURED,
    HEALTH_NEVER_RUN,
    HEALTH_OK,
    HEALTH_OVERDUE,
    get_health,
)
from arabase.backup.models import (
    FREQUENCY_HOURLY,
    FREQUENCY_WEEKLY,
    BackupRun,
    BackupSchedule,
)
from arabase.backup.restore import (
    RestoreError,
    ensure_not_live,
    redact,
    seal_target,
    unseal_target,
    validate_target,
)


def overview_url():
    return reverse("api:arabase:admin_backup")


def runs_url():
    return reverse("api:arabase:admin_backup_runs")


def run_now_url():
    return reverse("api:arabase:admin_backup_run_now")


def restore_url():
    return reverse("api:arabase:admin_backup_restore")


@pytest.fixture
def configured(monkeypatch):
    """A usable backup configuration in the environment."""

    monkeypatch.setenv("JADAWEL_BACKUP_ENABLED", "true")
    monkeypatch.setenv("JADAWEL_BACKUP_S3_BUCKET", "jadawel-backups")
    monkeypatch.setenv("JADAWEL_BACKUP_S3_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("JADAWEL_BACKUP_S3_SECRET_ACCESS_KEY", "secret")


# --- permissions ------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    [
        "admin_backup",
        "admin_backup_runs",
        "admin_backup_run_now",
        "admin_backup_restore",
    ],
)
def test_every_endpoint_refuses_a_signed_in_non_admin(
    api_client, data_fixture, url_name
):
    """The run history names object keys and can carry a storage error message,
    and the restore endpoint runs pg_restore. An ordinary account gets none of
    it."""

    _, token = data_fixture.create_user_and_token(is_staff=False)
    url = reverse(f"api:arabase:{url_name}")
    auth = {"HTTP_AUTHORIZATION": f"JWT {token}"}

    assert api_client.get(url, **auth).status_code == HTTP_403_FORBIDDEN
    assert api_client.post(url, **auth).status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    [
        "admin_backup",
        "admin_backup_runs",
        "admin_backup_run_now",
        "admin_backup_restore",
    ],
)
def test_every_endpoint_refuses_an_anonymous_visitor(api_client, url_name):
    url = reverse(f"api:arabase:{url_name}")

    assert api_client.get(url).status_code == HTTP_401_UNAUTHORIZED
    assert api_client.post(url).status_code == HTTP_401_UNAUTHORIZED


# --- schedule ---------------------------------------------------------------


@pytest.mark.django_db
def test_the_schedule_defaults_to_daily(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token(is_staff=True)

    body = api_client.get(
        overview_url(), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    ).json()

    assert body["schedule"]["frequency"] == "daily"
    # 23:00 UTC is 02:00 in Riyadh.
    assert body["schedule"]["crontab"] == "0 23 * * *"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "frequency,crontab",
    [("hourly", "0 * * * *"), ("daily", "0 23 * * *"), ("weekly", "0 23 * * 5")],
)
def test_an_admin_can_change_the_frequency(
    api_client, data_fixture, frequency, crontab
):
    _, token = data_fixture.create_user_and_token(is_staff=True)

    with patch("arabase.api.backup.views.republish_schedule") as republish:
        response = api_client.patch(
            overview_url(),
            {"frequency": frequency},
            format="json",
            **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        )

    assert response.status_code == HTTP_200_OK
    assert response.json()["schedule"]["crontab"] == crontab
    assert BackupSchedule.get_solo().frequency == frequency
    # Applied now rather than on the next redeploy — an admin toggle that only
    # takes effect after a deploy is worse than no toggle.
    republish.assert_called_once()


@pytest.mark.django_db
def test_an_unknown_frequency_is_rejected(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.patch(
        overview_url(),
        {"frequency": "fortnightly"},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_400_BAD_REQUEST


# --- health -----------------------------------------------------------------


@pytest.mark.django_db
class TestHealth:
    def test_disabled_when_the_feature_is_off(self, monkeypatch):
        monkeypatch.delenv("JADAWEL_BACKUP_ENABLED", raising=False)

        assert get_health().status == HEALTH_DISABLED

    def test_misconfigured_is_distinct_from_disabled(self, monkeypatch):
        """Enabled but unusable is the worse state of the two: the task is
        scheduled and will fail every time it fires."""

        monkeypatch.setenv("JADAWEL_BACKUP_ENABLED", "true")
        monkeypatch.delenv("JADAWEL_BACKUP_S3_BUCKET", raising=False)

        health = get_health()

        assert health.status == HEALTH_MISCONFIGURED
        assert health.configuration_errors

    def test_never_run_when_nothing_has_succeeded(self, configured):
        assert get_health().status == HEALTH_NEVER_RUN

    def test_ok_after_a_recent_success(self, configured):
        BackupRun.objects.create(status=BackupRun.STATUS_SUCCESS)

        health = get_health()

        assert health.status == HEALTH_OK
        assert health.healthy is True
        assert health.next_run_on is not None

    def test_last_failed_is_surfaced(self, configured):
        BackupRun.objects.create(
            status=BackupRun.STATUS_SUCCESS,
            started_on=timezone.now() - timedelta(hours=2),
        )
        BackupRun.objects.create(status=BackupRun.STATUS_FAILED, error="boom")

        assert get_health().status == HEALTH_LAST_FAILED

    def test_overdue_when_the_last_success_is_too_old(self, configured):
        """The failure this whole section exists to catch: backups that quietly
        stopped happening look exactly like backups that are working."""

        BackupRun.objects.create(
            status=BackupRun.STATUS_SUCCESS,
            started_on=timezone.now() - timedelta(days=30),
        )

        assert get_health().status == HEALTH_OVERDUE

    def test_overdue_wins_over_a_failed_last_run(self, configured):
        BackupRun.objects.create(
            status=BackupRun.STATUS_SUCCESS,
            started_on=timezone.now() - timedelta(days=30),
        )
        BackupRun.objects.create(status=BackupRun.STATUS_FAILED, error="boom")

        # Being a month stale is the more urgent fact.
        assert get_health().status == HEALTH_OVERDUE

    def test_the_grace_period_follows_the_frequency(self, configured):
        schedule = BackupSchedule.get_solo()
        schedule.frequency = FREQUENCY_HOURLY
        schedule.save()
        BackupRun.objects.create(
            status=BackupRun.STATUS_SUCCESS,
            started_on=timezone.now() - timedelta(hours=6),
        )

        # Six hours is fine for a weekly schedule and long overdue for an hourly.
        assert get_health().status == HEALTH_OVERDUE

        schedule.frequency = FREQUENCY_WEEKLY
        schedule.save()

        assert get_health().status == HEALTH_OK


# --- run history ------------------------------------------------------------


@pytest.mark.django_db
def test_failed_runs_appear_in_the_history(api_client, data_fixture):
    """A failed run uploads nothing, so listing the bucket would not show it.
    That is the whole reason runs are rows."""

    _, token = data_fixture.create_user_and_token(is_staff=True)
    BackupRun.objects.create(status=BackupRun.STATUS_FAILED, error="pg_dump exited 1")

    body = api_client.get(runs_url(), **{"HTTP_AUTHORIZATION": f"JWT {token}"}).json()

    assert len(body) == 1
    assert body[0]["status"] == "failed"
    assert "pg_dump exited 1" in body[0]["error"]


@pytest.mark.django_db
def test_a_manual_run_is_queued(api_client, data_fixture):
    _, token = data_fixture.create_user_and_token(is_staff=True)

    with patch("arabase.tasks.backup_database.delay") as delay:
        response = api_client.post(
            run_now_url(), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
        )

    assert response.status_code == HTTP_202_ACCEPTED
    delay.assert_called_once_with(trigger=BackupRun.TRIGGER_MANUAL)


@pytest.mark.django_db
def test_a_run_records_its_outcome(configured):
    """`record_run` writes the row before the dump and updates it either way."""

    from arabase.backup.runner import BackupError
    from arabase.tasks import backup_database

    with patch(
        "arabase.tasks.run_backup", side_effect=BackupError("pg_dump exited with 1")
    ):
        with pytest.raises(BackupError):
            backup_database()

    run = BackupRun.objects.first()
    assert run.status == BackupRun.STATUS_FAILED
    assert "pg_dump exited with 1" in run.error
    assert run.finished_on is not None


# --- restore ----------------------------------------------------------------


@pytest.mark.django_db
class TestRestoreTarget:
    """The restore is a rehearsal tool. There is no code path that writes over
    the running database, because a restore has no undo: it destroys the rows
    you would need to recover from a wrong choice."""

    def test_the_live_database_is_refused(self, settings):
        live = settings.DATABASES["default"]
        url = (
            f"postgresql://u:p@{live['HOST']}:5432/{live['NAME']}"
            if live.get("HOST")
            else None
        )
        if url is None:
            pytest.skip("The test database is not configured with a host.")

        with pytest.raises(RestoreError, match="live database"):
            validate_target(url)

    def test_a_different_database_on_the_same_host_is_allowed(self, settings):
        live = settings.DATABASES["default"]
        if not live.get("HOST"):
            pytest.skip("The test database is not configured with a host.")

        validate_target(f"postgresql://u:p@{live['HOST']}:5432/jadawel_restore_test")

    @pytest.mark.parametrize(
        "url",
        [
            "mysql://u:p@host:3306/db",
            "postgresql://u:p@host:5432/",
            "not-a-url",
        ],
    )
    def test_an_implausible_target_is_refused(self, url):
        with pytest.raises(RestoreError):
            validate_target(url)

    def test_query_parameters_cannot_redirect_the_target_to_the_live_database(
        self, settings
    ):
        # libpq lets the query string override the authority and the path, so
        # this URL connects to the live database while *looking* like "decoy".
        live = settings.DATABASES["default"]
        url = (
            "postgresql://u:p@decoy:5432/other"
            f"?host={live.get('HOST') or 'localhost'}&dbname={live['NAME']}"
        )

        with pytest.raises(RestoreError, match="live database"):
            validate_target(url)

    @pytest.mark.parametrize(
        "url",
        [
            "postgresql://u:p@scratch:5432/copy?hostaddr=10.0.0.5",
            "postgresql://u:p@scratch:5432/copy?service=live",
            "postgresql://u:p@scratch:5432/copy?options=-csearch_path%3Dx",
            "postgresql://u:p@scratch,other:5432/copy",
            "postgresql://%2Fvar%2Frun%2Fpostgresql/copy",
        ],
    )
    def test_a_target_that_could_resolve_elsewhere_is_refused(self, url):
        with pytest.raises(RestoreError):
            validate_target(url)

    def test_a_loopback_alias_of_the_live_host_is_refused(self, settings):
        live = settings.DATABASES["default"]
        if live.get("HOST") not in ("localhost", "127.0.0.1", "::1"):
            pytest.skip("The test database is not on a loopback host.")

        for host in ("localhost", "127.0.0.1", "LOCALHOST"):
            with pytest.raises(RestoreError, match="live database"):
                validate_target(f"postgresql://u:p@{host}:5432/{live['NAME']}")

    def test_the_password_never_leaves_the_server(self):
        assert (
            redact("postgresql://jadawel:hunter2@db:5432/x")
            == "postgresql://jadawel:***@db:5432/x"
        )


@pytest.mark.django_db
def test_restoring_over_the_live_database_is_a_400(api_client, data_fixture, settings):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    live = settings.DATABASES["default"]
    if not live.get("HOST"):
        pytest.skip("The test database is not configured with a host.")

    with patch("arabase.tasks.restore_backup_task.delay") as delay:
        response = api_client.post(
            restore_url(),
            {
                "key": "postgres/jadawel-20260815T230000Z.dump",
                "target_database_url": (
                    f"postgresql://u:p@{live['HOST']}:5432/{live['NAME']}"
                ),
            },
            format="json",
            **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_RESTORE_TARGET"
    # Rejected before anything was queued.
    delay.assert_not_called()


@pytest.mark.django_db
def test_a_restore_into_a_separate_database_is_queued_without_the_password(
    api_client, data_fixture
):
    _, token = data_fixture.create_user_and_token(is_staff=True)
    key = "postgres/jadawel-20260815T230000Z.dump"

    with patch("arabase.tasks.restore_backup_task.delay") as delay:
        response = api_client.post(
            restore_url(),
            {
                "key": key,
                "target_database_url": "postgresql://u:hunter2@scratch:5432/copy",
            },
            format="json",
            **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        )

    assert response.status_code == HTTP_202_ACCEPTED
    body = response.json()
    assert body["key"] == key
    assert "hunter2" not in body["target"]
    delay.assert_called_once()
    # The task arguments sit in the broker, so the password is sealed there too.
    queued_key, sealed_target = delay.call_args.args
    assert queued_key == key
    assert "hunter2" not in sealed_target
    assert unseal_target(sealed_target) == "postgresql://u:hunter2@scratch:5432/copy"


def test_a_tampered_sealed_target_is_refused():
    sealed = seal_target("postgresql://u:p@scratch:5432/copy")

    with pytest.raises(RestoreError, match="could not be read"):
        unseal_target(sealed[:-4] + "AAAA")


def _live_url(host: str, dbname: str) -> str:
    live = connection.settings_dict
    return (
        f"postgresql://{live['USER']}:{live['PASSWORD']}@{host}:"
        f"{live.get('PORT') or 5432}/{dbname}"
    )


@pytest.mark.django_db
def test_the_live_database_is_refused_however_its_host_is_spelled():
    live = connection.settings_dict
    if not live.get("HOST"):
        pytest.skip("The test database is not configured with a host.")

    # An IP address for a hostname is invisible to the syntactic check; only
    # asking the server who it is catches it.
    address = socket.gethostbyname(live["HOST"])

    with pytest.raises(RestoreError, match="live database"):
        ensure_not_live(_live_url(address, live["NAME"]))


@pytest.mark.django_db
def test_another_database_on_the_live_server_is_allowed():
    live = connection.settings_dict
    if not live.get("HOST"):
        pytest.skip("The test database is not configured with a host.")

    ensure_not_live(_live_url(live["HOST"], "postgres"))
