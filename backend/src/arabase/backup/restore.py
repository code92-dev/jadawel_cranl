"""Restore a backup into a *separate* database, never over the live one.

The restore offered from the admin page is deliberately non-destructive. A
button that overwrites the production database has no undo — the restore
destroys the very rows you would need to recover from a wrong choice — and the
one moment anyone reaches for it is a moment of panic. So this downloads the
dump, restores it into a target database the operator supplies, and stops. The
switch-over stays a human decision made with the restored copy in front of them.

`docs/BACKUP_RESTORE.md` describes the same procedure by hand; this runs it, and
uses the same `--no-owner --no-privileges` the dump was taken with, so it
restores under whatever role the target URL connects as.
"""

import base64
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from urllib.parse import urlparse

from django.utils.crypto import salted_hmac

import psycopg2
from cryptography.fernet import Fernet, InvalidToken
from psycopg2.extensions import make_dsn, parse_dsn

from arabase.backup.config import BackupConfig
from arabase.backup.runner import BackupError, _client, client_binary

logger = logging.getLogger(__name__)

RESTORE_TIMEOUT_SECONDS = 3600


class RestoreError(Exception):
    """Raised when a restore cannot be completed."""


@dataclass(frozen=True)
class RestoreResult:
    key: str
    target: str
    """The target database, with any password stripped."""


def _pg_restore_path() -> str:
    # Resolved the same way as pg_dump, and for the same reason: /usr/bin is
    # pg_wrapper, which picks a major version from the embedded cluster rather
    # than from the dump being restored. A dump written by a newer pg_dump is
    # unreadable by an older pg_restore, so the two must agree — taking the
    # newest installed version in both places is what makes them agree.
    path = client_binary("pg_restore")
    if path is None:
        raise RestoreError(
            "pg_restore is not installed. It ships with the postgresql-client "
            "package, which the all-in-one image installs in its base stage "
            "at the version in POSTGRES_CLIENT_VERSION."
        )
    return path


def redact(database_url: str) -> str:
    """A connection string safe to show in an API response or a log line."""

    return re.sub(r"://([^:/@]+):[^@]*@", r"://\1:***@", database_url)


LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}

TARGET_PARAMETERS = {
    "host",
    "port",
    "dbname",
    "user",
    "password",
    "sslmode",
    "connect_timeout",
    "application_name",
}
"""Connection parameters a restore target may carry.

An allowlist because libpq reads more than the URL's authority and path: a
query string such as ``?host=…&dbname=…`` overrides both, ``hostaddr`` replaces
the address ``host`` resolves to, and ``service`` pulls parameters from a file.
Any of those would let the target that is checked differ from the target that
pg_restore connects to."""

SEAL_TTL_SECONDS = 24 * 3600
"""How long a queued restore can wait for a worker before its target expires."""


def _normalised_host(host: str) -> str:
    host = host.strip().lower()
    return "localhost" if host in LOOPBACK_HOSTS else host


def _target_parameters(database_url: str) -> dict:
    """The connection parameters libpq will actually use for ``database_url``.

    Parsed by libpq itself (through psycopg2), so query-string overrides are
    resolved exactly as pg_restore will resolve them, then restricted to
    ``TARGET_PARAMETERS`` and a single TCP host.
    """

    parsed = urlparse(database_url)
    if parsed.scheme not in ("postgres", "postgresql"):
        raise RestoreError("The target must be a postgresql:// connection string.")

    try:
        params = parse_dsn(database_url)
    except psycopg2.ProgrammingError as exc:
        raise RestoreError("The target is not a valid connection string.") from exc

    unsupported = sorted(set(params) - TARGET_PARAMETERS)
    if unsupported:
        raise RestoreError(
            "The target may not set " + ", ".join(unsupported) + ". Put the host "
            "and database name in the URL itself."
        )

    host = params.get("host", "")
    if not host or not params.get("dbname"):
        raise RestoreError("The target must include a host and a database name.")
    if "," in host or "," in params.get("port", ""):
        raise RestoreError("The target must name a single host.")
    if host.startswith("/"):
        raise RestoreError("The target must be reached over TCP, not a socket.")

    return params


def target_dsn(database_url: str) -> str:
    """``database_url`` rebuilt from its validated parameters only."""

    return make_dsn(**_target_parameters(database_url))


def validate_target(database_url: str, config: BackupConfig | None = None) -> None:
    """Refuse anything that is not a plausible, non-live Postgres target.

    The live database is rejected by comparing against the running connection.
    That check is the difference between this being a rehearsal tool and being
    an undoable production wipe with extra steps.

    This is the check that needs no network, so the admin page can answer
    straight away. It cannot see through a DNS alias or an IP address written
    for a hostname; ``ensure_not_live`` closes that before pg_restore runs.
    """

    from django.conf import settings

    params = _target_parameters(database_url)

    live = settings.DATABASES["default"]
    same_host = _normalised_host(params["host"]) == _normalised_host(
        live.get("HOST") or ""
    )
    same_name = params["dbname"] == live.get("NAME")
    if same_host and same_name:
        raise RestoreError(
            "That is the live database. Restore into a separate database and "
            "switch over once you have verified it."
        )


IDENTITY_SQL = (
    "SELECT current_database(), pg_postmaster_start_time(), current_setting('port')"
)
"""Identifies a database on a running server without any special privilege.

Two servers do not share a postmaster start time to the microsecond, so equal
answers mean the same server whatever name or address reached it."""


def ensure_not_live(database_url: str) -> None:
    """Connect to the target and refuse it if it is the live database."""

    from django.db import connection

    try:
        target = psycopg2.connect(target_dsn(database_url), connect_timeout=10)
    except psycopg2.Error as exc:
        raise RestoreError(f"Could not connect to the target: {exc}") from exc
    try:
        with target.cursor() as cursor:
            cursor.execute(IDENTITY_SQL)
            target_identity = cursor.fetchone()
    finally:
        target.close()

    with connection.cursor() as cursor:
        cursor.execute(IDENTITY_SQL)
        live_identity = cursor.fetchone()

    if tuple(target_identity) == tuple(live_identity):
        raise RestoreError(
            "That is the live database. Restore into a separate database and "
            "switch over once you have verified it."
        )


def _fernet() -> Fernet:
    from django.conf import settings

    key = salted_hmac(
        "arabase.backup.restore.target",
        "restore-target",
        secret=settings.SECRET_KEY,
        algorithm="sha256",
    ).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def seal_target(database_url: str) -> str:
    """Encrypt a target URL for the task queue.

    The URL carries the target's password, and a task's arguments sit in the
    broker, and in the result backend and worker logs on failure. Sealed, they
    are useless without ``SECRET_KEY``.
    """

    return _fernet().encrypt(database_url.encode("utf-8")).decode("ascii")


def unseal_target(sealed: str) -> str:
    try:
        return (
            _fernet()
            .decrypt(sealed.encode("ascii"), ttl=SEAL_TTL_SECONDS)
            .decode("utf-8")
        )
    except (InvalidToken, UnicodeError) as exc:
        raise RestoreError(
            "The queued restore target could not be read. It expires after a "
            "day and is bound to SECRET_KEY; start the restore again."
        ) from exc


def restore_backup(key: str, target_database_url: str) -> RestoreResult:
    """Download ``key`` and restore it into ``target_database_url``."""

    config = BackupConfig.from_env()
    errors = config.validation_errors()
    if errors:
        raise RestoreError("Backup is not configured: " + " ".join(errors))

    validate_target(target_database_url, config)
    ensure_not_live(target_database_url)

    if not key.startswith(config.prefix):
        raise RestoreError(
            f"{key!r} is not under the configured backup prefix {config.prefix!r}."
        )

    handle, path = tempfile.mkstemp(prefix="jadawel-restore-", suffix=".dump")
    os.close(handle)
    try:
        client = _client(config)
        try:
            client.download_file(config.bucket, key, path)
        except Exception as exc:
            raise RestoreError(f"Could not download {key}: {exc}") from exc

        env = os.environ.copy()
        argv = [
            _pg_restore_path(),
            # Rebuilt from the validated parameters, so pg_restore connects to
            # exactly the target that was checked.
            f"--dbname={target_dsn(target_database_url)}",
            "--no-owner",
            "--no-privileges",
            # Repeatable: restoring twice into the same target is a normal thing
            # to do while rehearsing.
            "--clean",
            "--if-exists",
            path,
        ]
        try:
            # S603: argv is a resolved absolute path plus constant flags; the
            # only variable is the target URL, which validate_target has checked
            # and which is passed as a single argument, not through a shell.
            process = subprocess.run(  # noqa: S603
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                timeout=RESTORE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RestoreError(
                f"pg_restore did not finish within {RESTORE_TIMEOUT_SECONDS}s."
            ) from exc
        except OSError as exc:
            raise RestoreError(f"Could not run pg_restore: {exc}") from exc

        if process.returncode != 0:
            stderr = process.stderr.decode("utf-8", errors="replace").strip()
            # pg_restore exits non-zero for warnings too, so the message matters
            # more than the code when this reaches an operator.
            raise RestoreError(
                f"pg_restore exited with {process.returncode}: {stderr[:2000]}"
            )
    except BackupError as exc:
        raise RestoreError(str(exc)) from exc
    finally:
        try:
            os.remove(path)
        except OSError:
            logger.warning("Could not remove the temporary dump at %s.", path)

    redacted = redact(target_database_url)
    logger.info("Restored %s into %s.", key, redacted)
    return RestoreResult(key=key, target=redacted)
