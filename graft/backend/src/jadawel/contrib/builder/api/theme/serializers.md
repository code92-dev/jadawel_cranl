# backend/src/jadawel/contrib/builder/api/theme/serializers.py

- DynamicConfigBlockSerializer · class · L10-L70 — class DynamicConfigBlockSerializer(serializers.Serializer)
- __init__ · method · L15-L70 — def __init__( self, *args, property_name=None, theme_config_block_type_name=None, serializer_kwargs=None, request_serializer=False, **kwargs, )
- DynamicMeta · class · L65-L68 — class DynamicMeta
- serialize_builder_theme · function · L73-L91 — def serialize_builder_theme(builder: Builder) -> dict
- combine_theme_config_blocks_serializer_class · function · L94-L126 — def combine_theme_config_blocks_serializer_class( theme_config_blocks, request_serializer=False, name="CombinedThemeConfigBlocksSerializer", ) -> serializers.Serializer
- Meta · class · L118-L120 — class Meta
- get_combined_theme_config_blocks_serializer_class · function · L130-L149 — def get_combined_theme_config_blocks_serializer_class( request_serializer=False, ) -> serializers.Serializer
