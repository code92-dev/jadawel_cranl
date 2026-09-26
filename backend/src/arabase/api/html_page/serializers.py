from rest_framework import serializers

from arabase.views.models import HtmlPageViewFieldOptions


class HtmlPageViewFieldOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = HtmlPageViewFieldOptions
        fields = ("hidden", "order")
