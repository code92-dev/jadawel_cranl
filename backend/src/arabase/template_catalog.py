"""Keep the hosted Jadawel template picker limited to the local catalog."""

import hashlib
import json
import logging
import re
from pathlib import Path

from django.conf import settings
from django.db import transaction

from jadawel.core.handler import CoreHandler
from jadawel.core.models import Template, TemplateCategory
from jadawel.core.trash.handler import TrashHandler

logger = logging.getLogger(__name__)

ARABIC_TEMPLATE_CATEGORY = "قوالب عربية"
ENGLISH_TEMPLATE_CATEGORY = "English Templates"

# Saudi editions of upstream templates, built by tools/saudi_templates: each
# slug is the Arabic edition and "<slug>-en" its English counterpart.
SAUDI_EDITIONS = [
    # Databases
    "saudi-restaurant-management",
    "saudi-business-expenses",
    "saudi-employee-onboarding",
    "saudi-school-management",
    "saudi-nonprofit-management",
    # Automations
    "saudi-inspections-compliance",
    "saudi-intake-qualification",
    "saudi-work-management",
    "saudi-password-reset",
    "saudi-leave-management",
    # Applications
    "saudi-compliance-assessment",
    "saudi-property-management",
    "saudi-order-kiosk",
    "saudi-crm",
    "saudi-purchase-orders",
]

LOCAL_TEMPLATE_CATALOG = {
    "arabic-performance-review": ARABIC_TEMPLATE_CATEGORY,
    "arabic-project-management": ARABIC_TEMPLATE_CATEGORY,
    "saudi-budget-consolidation": ARABIC_TEMPLATE_CATEGORY,
    "performance-reviews": ENGLISH_TEMPLATE_CATEGORY,
    "project-management-en": ENGLISH_TEMPLATE_CATEGORY,
    "saudi-budget-consolidation-en": ENGLISH_TEMPLATE_CATEGORY,
    **{slug: ARABIC_TEMPLATE_CATEGORY for slug in SAUDI_EDITIONS},
    **{f"{slug}-en": ENGLISH_TEMPLATE_CATEGORY for slug in SAUDI_EDITIONS},
}

LOCAL_TEMPLATE_PATTERN = "^(?:{})$".format(
    "|".join(re.escape(slug) for slug in LOCAL_TEMPLATE_CATALOG)
)


class LocalTemplateCatalogIncomplete(Exception):
    """Raised before pruning when a required local template failed to import."""


def _local_template_export_hashes() -> dict[str, str]:
    """Return the content hash CoreHandler stores for each approved template."""

    templates_dir = Path(settings.APPLICATION_TEMPLATES_DIR)
    return {
        slug: hashlib.sha256(
            json.dumps(
                json.loads((templates_dir / f"{slug}.json").read_text())["export"]
            ).encode("utf-8")
        ).hexdigest()
        for slug in LOCAL_TEMPLATE_CATALOG
    }


def local_template_catalog_is_current() -> bool:
    """Return whether the database contains exactly the approved local catalog."""

    expected_hashes = _local_template_export_hashes()
    templates = {}
    for slug, category_name, export_hash in Template.objects.values_list(
        "slug", "categories__name", "export_hash"
    ):
        templates.setdefault(slug, {"categories": set(), "export_hash": export_hash})
        if category_name is not None:
            templates[slug]["categories"].add(category_name)
    expected = {
        slug: {
            "categories": {category_name},
            "export_hash": expected_hashes[slug],
        }
        for slug, category_name in LOCAL_TEMPLATE_CATALOG.items()
    }
    category_names = set(TemplateCategory.objects.values_list("name", flat=True))
    expected_category_names = {
        ARABIC_TEMPLATE_CATEGORY,
        ENGLISH_TEMPLATE_CATEGORY,
    }
    return templates == expected and category_names == expected_category_names


def reconcile_local_template_catalog() -> dict:
    """Import the bundled templates and remove obsolete catalog previews.

    This is intentionally fail-safe: imports happen first, and no old template is
    removed unless every approved slug exists afterward. The operation is
    idempotent, so normal restarts only perform the inexpensive state check.
    """

    if local_template_catalog_is_current():
        return {
            "changed": False,
            "removed": 0,
            "templates": len(LOCAL_TEMPLATE_CATALOG),
        }

    CoreHandler().sync_templates(pattern=LOCAL_TEMPLATE_PATTERN)

    installed_slugs = set(Template.objects.values_list("slug", flat=True))
    missing_slugs = set(LOCAL_TEMPLATE_CATALOG) - installed_slugs
    if missing_slugs:
        missing = ", ".join(sorted(missing_slugs))
        raise LocalTemplateCatalogIncomplete(
            f"Refusing to prune templates because these local templates are "
            f"missing: {missing}"
        )

    categories = {
        name: TemplateCategory.objects.get_or_create(name=name)[0]
        for name in (ARABIC_TEMPLATE_CATEGORY, ENGLISH_TEMPLATE_CATEGORY)
    }

    with transaction.atomic():
        for slug, category_name in LOCAL_TEMPLATE_CATALOG.items():
            Template.objects.get(slug=slug).categories.set([categories[category_name]])

    obsolete_templates = list(
        Template.objects.exclude(slug__in=LOCAL_TEMPLATE_CATALOG).select_related(
            "workspace"
        )
    )
    for template in obsolete_templates:
        with transaction.atomic():
            if template.workspace is not None:
                TrashHandler.permanently_delete(template.workspace)
            template.delete()

    TemplateCategory.objects.exclude(
        name__in=(ARABIC_TEMPLATE_CATEGORY, ENGLISH_TEMPLATE_CATEGORY)
    ).delete()

    logger.info(
        "Reconciled the local template catalog: kept %s templates and removed %s.",
        len(LOCAL_TEMPLATE_CATALOG),
        len(obsolete_templates),
    )
    return {
        "changed": True,
        "removed": len(obsolete_templates),
        "templates": len(LOCAL_TEMPLATE_CATALOG),
    }


def reconcile_local_template_catalog_after_migrate(sender, **kwargs):
    """Reconcile synchronously so startup cannot expose a stale catalog.

    CranL runs one combined Celery worker. Queueing this behind core's broad
    template sync left the old 157-template catalog live with no dependable
    completion signal. Running here makes a successful migration/startup the
    signal that the authoritative local catalog is ready.
    """

    from django.conf import settings

    if settings.TESTS:
        return

    result = reconcile_local_template_catalog()
    logger.info("Local template catalog is ready after migrations: %s", result)
    return result
