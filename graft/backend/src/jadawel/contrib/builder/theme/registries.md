# backend/src/jadawel/contrib/builder/theme/registries.py

- ThemeConfigBlockType · class · L19-L106 — class ThemeConfigBlockType( Instance, EasyImportExportMixin, CustomFieldsInstanceMixin, ABC, )
- get_property_names · method · L38-L47 — def get_property_names(self)
- allowed_fields · method · L50-L55 — def allowed_fields(self)
- serializer_field_names · method · L58-L59 — def serializer_field_names(self)
- related_name_in_builder_model · method · L62-L68 — def related_name_in_builder_model(self) -> str
- update_properties · method · L70-L91 — def update_properties( self, builder, **kwargs: dict ) -> Type[ThemeConfigBlockSubClass]
- enhance_queryset · method · L93-L106 — def enhance_queryset(self, queryset: QuerySet[Builder]) -> QuerySet[Builder]
- ThemeConfigBlockRegistry · class · L114-L136 — class ThemeConfigBlockRegistry( Registry[ThemeConfigBlockTypeSubClass], CustomFieldsRegistryMixin, )
- enhance_list_builder_queryset · method · L124-L136 — def enhance_list_builder_queryset(self, queryset: QuerySet) -> QuerySet
