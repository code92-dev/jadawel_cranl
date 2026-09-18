from rest_framework import serializers

from arabase.table_access.models import TableAccessLevel


class TableGrantEntrySerializer(serializers.Serializer):
    table_id = serializers.IntegerField(
        help_text="The table the guest is allowed to reach."
    )
    level = serializers.ChoiceField(
        choices=TableAccessLevel.choices,
        default=TableAccessLevel.VIEWER,
        help_text="VIEWER reads the table, EDITOR may also change its rows.",
    )


class InviteGuestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="The address that is invited as a table guest."
    )
    tables = TableGrantEntrySerializer(
        many=True,
        allow_empty=False,
        help_text="The tables the guest gets, each with its access level.",
    )
    base_url = serializers.URLField(
        help_text="The frontend URL the accept token is appended to, exactly as "
        "for a normal workspace invitation."
    )


class SetGrantsSerializer(serializers.Serializer):
    # Empty is allowed on purpose: it is how an admin parks a guest without
    # removing them, and it leaves them with an empty workspace rather than a
    # half-open one.
    tables = TableGrantEntrySerializer(many=True, allow_empty=True)


class GrantedTableSerializer(serializers.Serializer):
    table_id = serializers.IntegerField()
    name = serializers.CharField()
    database_id = serializers.IntegerField()
    level = serializers.CharField()


class GuestSerializer(serializers.Serializer):
    workspace_user_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
    tables = GrantedTableSerializer(many=True)


class GuestInvitationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    created_on = serializers.DateTimeField()
    tables = GrantedTableSerializer(many=True)


class TableAccessOverviewSerializer(serializers.Serializer):
    guests = GuestSerializer(many=True)
    invitations = GuestInvitationSerializer(many=True)
