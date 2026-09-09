# backend/src/jadawel/contrib/builder/data_sources/models.py

- get_default_data_source_content_type · function · L14-L15 — def get_default_data_source_content_type()
- DataSource · class · L18-L101 — class DataSource( HierarchicalModelMixin, TrashableModelMixin, FractionOrderableMixin, BuilderInstanceWithFormulaMixin, models.Model, )
- Meta · class · L50-L55 — class Meta
- get_parent · method · L57-L58 — def get_parent(self)
- get_last_order · method · L61-L70 — def get_last_order(cls, page: Page)
- get_unique_order_before_data_source · method · L73-L86 — def get_unique_order_before_data_source(cls, before: "DataSource")
- formula_generator · method · L88-L101 — def formula_generator(self, instance: "DataSource")
