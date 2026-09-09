# backend/src/jadawel/contrib/builder/elements/permission_manager.py

- ElementVisibilityPermissionManager · class · L27-L274 — class ElementVisibilityPermissionManager(PermissionManagerType)
- auth_user_can_view_element · method · L36-L73 — def auth_user_can_view_element(self, user, element)
- check_multiple_permissions · method · L75-L107 — def check_multiple_permissions( self, checks, workspace=None, include_trash=False, )
- exclude_elements_with_role · method · L109-L138 — def exclude_elements_with_role( self, queryset: QuerySet, role_type: Element.ROLE_TYPES, role: str, prefix: str = "", ) -> QuerySet
- exclude_elements_without_role · method · L140-L169 — def exclude_elements_without_role( self, queryset: QuerySet, role_type: Element.VISIBILITY_TYPES, role: str, prefix: str = "", ) -> QuerySet
- exclude_elements_with_page_visibility · method · L171-L190 — def exclude_elements_with_page_visibility( self, queryset: QuerySet, actor: AbstractUser, ) -> QuerySet
- exclude_elements_with_visibility · method · L192-L218 — def exclude_elements_with_visibility( self, queryset: QuerySet, visibility_type: Element.VISIBILITY_TYPES, prefix: str = "", ) -> QuerySet
- filter_queryset · method · L220-L274 — def filter_queryset( self, actor, operation_name: str, queryset, workspace=None, )
