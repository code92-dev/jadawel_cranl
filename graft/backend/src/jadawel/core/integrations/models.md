# backend/src/jadawel/core/integrations/models.py

- get_default_integration · function · L18-L19 — def get_default_integration()
- Integration · class · L22-L104 — class Integration( HierarchicalModelMixin, PolymorphicContentTypeMixin, WithRegistry, FractionOrderableMixin, TrashableModelMixin, models.Model, )
- get_type_registry · method · L59-L62 — def get_type_registry()
- Meta · class · L64-L65 — class Meta
- get_parent · method · L67-L68 — def get_parent(self)
- context_data · method · L71-L75 — def context_data(self)
- get_last_order · method · L78-L87 — def get_last_order(cls, application: "Application")
- get_unique_order_before_integration · method · L90-L104 — def get_unique_order_before_integration(cls, before: "Integration")
