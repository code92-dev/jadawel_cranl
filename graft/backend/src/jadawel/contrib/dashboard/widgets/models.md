# backend/src/jadawel/contrib/dashboard/widgets/models.py

- Widget · class · L21-L102 — class Widget( HierarchicalModelMixin, TrashableModelMixin, CreatedAndUpdatedOnMixin, FractionOrderableMixin, PolymorphicContentTypeMixin, WithRegistry, models.Model, )
- Meta · class · L60-L61 — class Meta
- get_type_registry · method · L64-L67 — def get_type_registry()
- get_parent · method · L69-L70 — def get_parent(self)
- get_last_order · method · L73-L85 — def get_last_order( cls, dashboard: "Dashboard", )
- get_last_orders · method · L88-L102 — def get_last_orders( cls, dashboard: "Dashboard", amount=1, )
- SummaryWidget · class · L105-L110 — class SummaryWidget(Widget)
