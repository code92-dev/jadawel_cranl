# backend/src/arabase/row_coloring/decorator_types.py

- ensure_single_decorator_per_view · function · L9-L19 — def ensure_single_decorator_per_view(view, decorator_type, ignore_id=None)
- ColorRowDecoratorTypeBase · class · L22-L48 — class ColorRowDecoratorTypeBase(DecoratorType)
- before_create_decoration · method · L30-L34 — def before_create_decoration(self, view, user)
- before_update_decoration · method · L36-L48 — def before_update_decoration(self, view_decoration, user): # ViewDecorationNotSupported is only mapped on the create endpoint, # so updates reuse the compatibility error (mapped on both) to avoid # a 500 on this extreme edge case.
- BackgroundColorDecoratorType · class · L51-L61 — class BackgroundColorDecoratorType(ColorRowDecoratorTypeBase)
- LeftBorderColorDecoratorType · class · L64-L74 — class LeftBorderColorDecoratorType(ColorRowDecoratorTypeBase)
