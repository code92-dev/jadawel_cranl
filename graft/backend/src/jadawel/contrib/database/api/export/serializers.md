# backend/src/jadawel/contrib/database/api/export/serializers.py

- ExportedFileURLSerializerMixin · class · L64-L71 — class ExportedFileURLSerializerMixin(FileURLSerializerMixin)
- get_handler · method · L70-L71 — def get_handler(self)
- ExportJobSerializer · class · L74-L96 — class ExportJobSerializer(ExportedFileURLSerializerMixin, serializers.ModelSerializer)
- get_status · method · L80-L81 — def get_status(self, instance)
- Meta · class · L83-L96 — class Meta
- DisplayChoiceField · class · L99-L106 — class DisplayChoiceField(serializers.ChoiceField)
- to_representation · method · L105-L106 — def to_representation(self, obj)
- BaseExporterOptionsSerializer · class · L109-L148 — class BaseExporterOptionsSerializer(serializers.Serializer)
- CsvExporterOptionsSerializer · class · L151-L164 — class CsvExporterOptionsSerializer(BaseExporterOptionsSerializer): # For ease of use we expect the JSON to contain human typeable forms of each # different separator instead of the unicode character itself. By using the # DisplayChoiceField we can then map this to the actual separator character by # having those be the second value of each choice tuple.
