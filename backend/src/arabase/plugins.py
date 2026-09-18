from django.urls import include, path

from jadawel.core.registries import Plugin


class ArabasePlugin(Plugin):
    """Mount point for the Jadawel fork's own API routes.

    Jadawel's `plugin_registry` contributes its members' urls to the root
    urlconf, so registering here adds `/api/arabase/...` without editing
    `jadawel/config/urls.py` or `jadawel/api/urls.py`. Keeping our routes on a
    separate prefix also means an upstream route can never collide with ours.
    """

    type = "arabase"

    def get_hidden_field_ids(self, user, table):
        """Core hook: hide fields that read outside a guest's granted tables.

        Called from `contrib/database/api/views/utils.py` for every field list
        and row payload. Returns an empty set for anyone who is not a table
        guest, which is every normal member.
        """

        from arabase.table_access.hidden_fields import hidden_field_ids_for_guest

        return hidden_field_ids_for_guest(user, table)

    def get_api_urls(self):
        return [
            path(
                "arabase/",
                include("arabase.api.urls", namespace=self.type),
            ),
        ]
