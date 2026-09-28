"""
New application-builder apps start from the Jadawel theme preset.

Upstream creates an app with its own stock theme: blue buttons with 4 px
corners, black-bordered square inputs and tables, Inter with no Arabic
letters, and every alignment on the left. An app created here instead starts
from `theme_presets.DEFAULT_PRESET`, aligned for the language of the person who
created it.

Only apps created from scratch get it. Duplicates, imports and template
installs send the same `application_created` signal with a `type_name`, and
keep the theme they were made with.
"""

from loguru import logger

from arabase.builder.theme_presets import DEFAULT_PRESET, preset_theme


def creator_language(user) -> str:
    profile = getattr(user, "profile", None)
    return getattr(profile, "language", None) or "ar"


def apply_default_theme(sender, application, user=None, **kwargs):
    from jadawel.contrib.builder.models import Builder
    from jadawel.contrib.builder.theme.handler import ThemeHandler

    if "type_name" in kwargs:
        return
    # The instance the API response is serialized from, so the new theme is in
    # the response rather than only on the next load.
    builder = application if isinstance(application, Builder) else None
    if builder is None:
        specific = application.specific
        if not isinstance(specific, Builder):
            return
        builder = specific
    try:
        ThemeHandler().update_theme(
            builder, **preset_theme(DEFAULT_PRESET, creator_language(user))
        )
    except Exception:  # noqa: BLE001 - never fail the app's creation over a look
        logger.exception("Could not apply the default theme to builder {}", builder.id)


def connect_builder_theme_defaults():
    from jadawel.core.signals import application_created

    application_created.connect(
        apply_default_theme, dispatch_uid="arabase_builder_default_theme"
    )
