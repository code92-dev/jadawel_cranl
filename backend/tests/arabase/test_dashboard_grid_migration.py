"""Migration dashboard.0005: the 3-column board's widgets keep their layout on
the 12-column one, and going back restores them (docs/DASHBOARD_REDESIGN.md).

The migration's functions run against the live app registry here rather than
through the `migrator` fixture, so the check runs on every test run."""

from importlib import import_module

from django.apps import apps

import pytest

from jadawel.contrib.dashboard.widgets.models import Widget

migration = import_module(
    "jadawel.contrib.dashboard.migrations.0005_widget_grid_12_appearance"
)


@pytest.mark.django_db
def test_0005_scales_widget_sizes_and_back(data_fixture):
    dashboard = data_fixture.create_dashboard_application()
    legacy = {"third": (1, 1), "two thirds": (2, 3), "full": (3, 2)}
    for title, (width, height) in legacy.items():
        data_fixture.create_summary_widget(
            dashboard=dashboard, title=title, width=width, height=height
        )

    def sizes():
        return {w.title: (w.width, w.height) for w in Widget.objects.all()}

    migration.forwards(apps, None)
    assert sizes() == {"third": (4, 2), "two thirds": (8, 6), "full": (12, 4)}

    migration.backwards(apps, None)
    assert sizes() == legacy


@pytest.mark.django_db
def test_0005_backwards_rounds_new_sizes_into_the_old_grid(data_fixture):
    dashboard = data_fixture.create_dashboard_application()
    for title, width, height in [("quarter", 3, 2), ("half", 6, 5), ("tiny", 1, 1)]:
        data_fixture.create_summary_widget(
            dashboard=dashboard, title=title, width=width, height=height
        )

    migration.backwards(apps, None)

    assert {w.title: (w.width, w.height) for w in Widget.objects.all()} == {
        "quarter": (1, 1),
        "half": (2, 2),
        "tiny": (1, 1),
    }
