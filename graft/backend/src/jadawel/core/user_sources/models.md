# backend/src/jadawel/core/user_sources/models.py

- get_default_user_source · function · L20-L21 — def get_default_user_source()
- gen_uuid · function · L24-L25 — def gen_uuid()
- UserSource · class · L28-L117 — class UserSource( HierarchicalModelMixin, PolymorphicContentTypeMixin, WithRegistry, FractionOrderableMixin, TrashableModelMixin, models.Model, )
- get_type_registry · method · L79-L82 — def get_type_registry()
- Meta · class · L84-L85 — class Meta
- get_parent · method · L87-L88 — def get_parent(self)
- get_last_order · method · L91-L100 — def get_last_order(cls, application: "Application")
- get_unique_order_before_user_source · method · L103-L117 — def get_unique_order_before_user_source(cls, before: "UserSource")
