from rest_framework import serializers


class UpdateProviderSettingsSerializer(serializers.Serializer):
    api_key = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=1000,
        help_text="A new API key. Blank or omitted keeps the saved key.",
    )
    clear_api_key = serializers.BooleanField(required=False, default=False)
    models = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=True),
        required=False,
        max_length=50,
    )
    host = serializers.CharField(required=False, allow_blank=True, max_length=500)
    base_url = serializers.CharField(required=False, allow_blank=True, max_length=500)
    organization = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
