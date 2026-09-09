# backend/src/jadawel/contrib/builder/theme/theme_config_block_types.py

- ColorThemeConfigBlockType · class · L26-L28 — class ColorThemeConfigBlockType(ThemeConfigBlockType)
- TypographyThemeConfigBlockType · class · L31-L89 — class TypographyThemeConfigBlockType(ThemeConfigBlockType)
- serializer_field_overrides · method · L36-L68 — def serializer_field_overrides(self)
- import_serialized · method · L70-L89 — def import_serialized( self, parent: Any, serialized_values: Dict[str, Any], id_mapping: Dict[str, Dict[int, int]], files_zip: Optional[ZipFile] = None, storage: Optional[Storage] = None, cache: Optional[Dict[str, any]] = None, **kwargs, ): # Translate from old color property names to new names for compat with templates
- ButtonThemeConfigBlockType · class · L92-L94 — class ButtonThemeConfigBlockType(ThemeConfigBlockType)
- LinkThemeConfigBlockType · class · L97-L119 — class LinkThemeConfigBlockType(ThemeConfigBlockType)
- serializer_field_overrides · method · L102-L119 — def serializer_field_overrides(self)
- ImageThemeConfigBlockType · class · L122-L146 — class ImageThemeConfigBlockType(ThemeConfigBlockType)
- serializer_field_overrides · method · L127-L135 — def serializer_field_overrides(self): # For some reason if we don't allow_null=False here the null value is returned
- request_serializer_field_overrides · method · L138-L146 — def request_serializer_field_overrides(self)
- PageThemeConfigBlockType · class · L149-L229 — class PageThemeConfigBlockType(ThemeConfigBlockType)
- get_property_names · method · L153-L161 — def get_property_names(self)
- serializer_field_overrides · method · L164-L175 — def serializer_field_overrides(self)
- serialize_property · method · L177-L204 — def serialize_property( self, theme_config_block: ThemeConfigBlock, prop_name: str, files_zip=None, storage=None, cache=None, )
- deserialize_property · method · L206-L224 — def deserialize_property( self, prop_name: str, value, id_mapping, files_zip=None, storage=None, cache=None, **kwargs, )
- enhance_queryset · method · L226-L229 — def enhance_queryset(self, queryset: QuerySet[Builder]) -> QuerySet[Builder]
- InputThemeConfigBlockType · class · L232-L234 — class InputThemeConfigBlockType(ThemeConfigBlockType)
- TableThemeConfigBlockType · class · L237-L239 — class TableThemeConfigBlockType(ThemeConfigBlockType)
