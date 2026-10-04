from rest_framework import serializers


class UpdateFeatureAccessSerializer(serializers.Serializer):
    everyone = serializers.BooleanField(
        help_text="Open the feature to every user, or limit it to staff and its "
        "granted email addresses."
    )


class AddFeatureGrantsSerializer(serializers.Serializer):
    emails = serializers.ListField(
        child=serializers.EmailField(max_length=254),
        min_length=1,
        max_length=100,
        help_text="Email addresses to grant the feature. An address without an "
        "account yet is covered once an account is created with it.",
    )
