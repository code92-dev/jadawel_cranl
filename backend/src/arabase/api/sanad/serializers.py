from rest_framework import serializers

from arabase.sanad.models import SanadChat, SanadMessage


class SanadMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SanadMessage
        fields = (
            "id",
            "role",
            "status",
            "content",
            "context",
            "actions",
            "approvals",
            "error",
            "created_on",
        )


class SanadChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SanadChat
        fields = ("id", "title", "model", "created_on", "updated_on")


class SanadChatWithMessagesSerializer(SanadChatSerializer):
    messages = SanadMessageSerializer(many=True, read_only=True)

    class Meta(SanadChatSerializer.Meta):
        fields = (*SanadChatSerializer.Meta.fields, "messages")


class SanadContextSerializer(serializers.Serializer):
    table_id = serializers.IntegerField(required=False, allow_null=True)
    view_id = serializers.IntegerField(required=False, allow_null=True)


class SendSanadMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=8000, trim_whitespace=True)
    model = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    context = SanadContextSerializer(required=False, default=dict)


class SanadDecisionSerializer(serializers.Serializer):
    tool_call_id = serializers.CharField(max_length=255)
    approved = serializers.BooleanField()


class SanadDecisionsSerializer(serializers.Serializer):
    decisions = SanadDecisionSerializer(many=True, allow_empty=False)
