from jadawel.contrib.database.views.exceptions import (
    DecoratorValueProviderTypeNotCompatible,
    ViewDecorationNotSupported,
)
from jadawel.contrib.database.views.models import ViewDecoration
from jadawel.contrib.database.views.registries import DecoratorType


def ensure_single_decorator_per_view(view, decorator_type, ignore_id=None):
    """Enforce at most one decoration of a given type per view.

    Matches the agreed product rule (one left-border and one background
    configuration per view). The frontend `canAdd` already prevents this, so
    this is the API-level backstop.
    """
    existing = ViewDecoration.objects.filter(view=view, type=decorator_type)
    if ignore_id is not None:
        existing = existing.exclude(pk=ignore_id)
    return existing


class ColorRowDecoratorTypeBase(DecoratorType):
    """Shared behavior for the row-coloring decorator types.

    Both types enforce one configuration of their own type per view, while
    explicitly allowing one background and one left-border decoration to
    coexist.
    """

    def before_create_decoration(self, view, user):
        if ensure_single_decorator_per_view(view, self.type).exists():
            raise ViewDecorationNotSupported(
                f"View {view.id} already has a {self.type} decoration."
            )

    def before_update_decoration(self, view_decoration, user):
        # ViewDecorationNotSupported is only mapped on the create endpoint,
        # so updates reuse the compatibility error (mapped on both) to avoid
        # a 500 on this extreme edge case.
        if (
            ensure_single_decorator_per_view(
                view_decoration.view, self.type, ignore_id=view_decoration.id
            ).exists()
            and view_decoration.type != self.type
        ):
            raise DecoratorValueProviderTypeNotCompatible(
                f"View {view_decoration.view_id} already has a {self.type} decoration."
            )


class BackgroundColorDecoratorType(ColorRowDecoratorTypeBase):
    """Paints the whole row background with the decoration value.

    OSS re-implementation of upstream's premium `background_color`
    decorator. The type string intentionally matches upstream so that
    exports, duplication and Airtable imports keep referring to the same
    type. The value itself is resolved client-side by the matching value
    provider; the backend only stores and validates the configuration.
    """

    type = "background_color"


class LeftBorderColorDecoratorType(ColorRowDecoratorTypeBase):
    """Paints a subtle color bar on the row's inline-start edge.

    OSS re-implementation of upstream's `left_border_color` decorator.
    The type string matches upstream (it is what the Airtable import
    mapping emits) and "left" is read as the logical inline-start edge,
    so the bar renders on the right in Arabic (RTL) views. The value is
    resolved client-side by the value provider like the background one.
    """

    type = "left_border_color"
