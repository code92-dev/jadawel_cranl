from unittest.mock import patch

from django.conf import settings
from django.test import override_settings

import pytest

from arabase.template_catalog import (
    ARABIC_TEMPLATE_CATEGORY,
    ENGLISH_TEMPLATE_CATEGORY,
    LOCAL_TEMPLATE_CATALOG,
    LOCAL_TEMPLATE_PATTERN,
    LocalTemplateCatalogIncomplete,
    _local_template_export_hashes,
    local_template_catalog_is_current,
    reconcile_local_template_catalog,
    reconcile_local_template_catalog_after_migrate,
)
from jadawel.core.models import Template, TemplateCategory, Workspace


def create_template(data_fixture, slug, category, export_hash=None):
    if export_hash is None and slug in LOCAL_TEMPLATE_CATALOG:
        export_hash = _local_template_export_hashes()[slug]
    return data_fixture.create_template(
        slug=slug, category=category, export_hash=export_hash or ""
    )


@pytest.mark.django_db
@patch("arabase.template_catalog.CoreHandler.sync_templates")
def test_reconcile_local_template_catalog_imports_then_prunes(
    sync_templates, data_fixture
):
    old_category = data_fixture.create_template_category(name="Old templates")
    old_template = create_template(data_fixture, "obsolete-template", old_category)
    old_workspace_id = old_template.workspace_id

    def install_missing_templates(*args, **kwargs):
        for slug in LOCAL_TEMPLATE_CATALOG:
            if not Template.objects.filter(slug=slug).exists():
                create_template(data_fixture, slug, old_category)

    sync_templates.side_effect = install_missing_templates

    result = reconcile_local_template_catalog()

    assert result == {
        "changed": True,
        "removed": 1,
        "templates": len(LOCAL_TEMPLATE_CATALOG),
    }
    assert set(Template.objects.values_list("slug", flat=True)) == set(
        LOCAL_TEMPLATE_CATALOG
    )
    assert not Workspace.objects.filter(id=old_workspace_id).exists()
    assert set(TemplateCategory.objects.values_list("name", flat=True)) == {
        ARABIC_TEMPLATE_CATEGORY,
        ENGLISH_TEMPLATE_CATEGORY,
    }
    for slug, expected_category in LOCAL_TEMPLATE_CATALOG.items():
        assert set(
            Template.objects.get(slug=slug).categories.values_list("name", flat=True)
        ) == {expected_category}
    assert local_template_catalog_is_current()


@pytest.mark.django_db
@patch("arabase.template_catalog.CoreHandler.sync_templates")
def test_reconcile_local_template_catalog_does_not_prune_when_import_is_incomplete(
    sync_templates, data_fixture
):
    old_template = data_fixture.create_template(slug="obsolete-template")

    with pytest.raises(LocalTemplateCatalogIncomplete):
        reconcile_local_template_catalog()

    sync_templates.assert_called_once()
    assert Template.objects.filter(id=old_template.id).exists()


@pytest.mark.django_db
@patch("arabase.template_catalog.CoreHandler.sync_templates")
def test_reconcile_local_template_catalog_is_noop_when_current(
    sync_templates, data_fixture
):
    categories = {
        ARABIC_TEMPLATE_CATEGORY: data_fixture.create_template_category(
            name=ARABIC_TEMPLATE_CATEGORY
        ),
        ENGLISH_TEMPLATE_CATEGORY: data_fixture.create_template_category(
            name=ENGLISH_TEMPLATE_CATEGORY
        ),
    }
    for slug, category_name in LOCAL_TEMPLATE_CATALOG.items():
        create_template(data_fixture, slug, categories[category_name])

    assert reconcile_local_template_catalog() == {
        "changed": False,
        "removed": 0,
        "templates": len(LOCAL_TEMPLATE_CATALOG),
    }
    sync_templates.assert_not_called()


@pytest.mark.django_db
@patch("arabase.template_catalog.CoreHandler.sync_templates")
def test_reconcile_local_template_catalog_refreshes_changed_template(
    sync_templates, data_fixture
):
    categories = {
        ARABIC_TEMPLATE_CATEGORY: data_fixture.create_template_category(
            name=ARABIC_TEMPLATE_CATEGORY
        ),
        ENGLISH_TEMPLATE_CATEGORY: data_fixture.create_template_category(
            name=ENGLISH_TEMPLATE_CATEGORY
        ),
    }
    changed_slug = "performance-reviews"
    for slug, category_name in LOCAL_TEMPLATE_CATALOG.items():
        create_template(
            data_fixture,
            slug,
            categories[category_name],
            export_hash="stale" if slug == changed_slug else None,
        )

    def refresh_changed_template(*args, **kwargs):
        Template.objects.filter(slug=changed_slug).update(
            export_hash=_local_template_export_hashes()[changed_slug]
        )

    sync_templates.side_effect = refresh_changed_template

    assert reconcile_local_template_catalog() == {
        "changed": True,
        "removed": 0,
        "templates": len(LOCAL_TEMPLATE_CATALOG),
    }
    sync_templates.assert_called_once_with(pattern=LOCAL_TEMPLATE_PATTERN)
    assert local_template_catalog_is_current()


def test_local_catalog_disables_core_broad_template_sync():
    assert settings.JADAWEL_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION is False
    assert settings.JADAWEL_SYNC_TEMPLATES_PATTERN == LOCAL_TEMPLATE_PATTERN


def test_local_catalog_contains_the_default_application_template():
    assert settings.DEFAULT_APPLICATION_TEMPLATES == ["project-management-en"]
    assert settings.DEFAULT_APPLICATION_TEMPLATES[0] in LOCAL_TEMPLATE_CATALOG


@override_settings(TESTS=False)
@patch("arabase.template_catalog.reconcile_local_template_catalog")
def test_reconcile_local_template_catalog_after_migrate_runs_synchronously(reconcile):
    reconcile.return_value = {
        "changed": True,
        "removed": 151,
        "templates": len(LOCAL_TEMPLATE_CATALOG),
    }

    result = reconcile_local_template_catalog_after_migrate(sender=None)

    reconcile.assert_called_once_with()
    assert result == {
        "changed": True,
        "removed": 151,
        "templates": len(LOCAL_TEMPLATE_CATALOG),
    }


@override_settings(TESTS=True)
@patch("arabase.template_catalog.reconcile_local_template_catalog")
def test_reconcile_local_template_catalog_after_migrate_skips_tests(reconcile):
    assert reconcile_local_template_catalog_after_migrate(sender=None) is None

    reconcile.assert_not_called()


@pytest.mark.django_db
@patch("arabase.template_catalog.CoreHandler.sync_templates")
def test_reconcile_local_template_catalog_prunes_a_full_legacy_catalog(
    sync_templates, data_fixture
):
    legacy_category = data_fixture.create_template_category(name="Legacy templates")
    for index in range(151):
        create_template(data_fixture, f"legacy-template-{index}", legacy_category)

    def install_local_templates(*args, **kwargs):
        for slug in LOCAL_TEMPLATE_CATALOG:
            create_template(data_fixture, slug, legacy_category)

    sync_templates.side_effect = install_local_templates

    result = reconcile_local_template_catalog()

    assert result == {
        "changed": True,
        "removed": 151,
        "templates": len(LOCAL_TEMPLATE_CATALOG),
    }
    assert set(Template.objects.values_list("slug", flat=True)) == set(
        LOCAL_TEMPLATE_CATALOG
    )
    assert local_template_catalog_is_current()
