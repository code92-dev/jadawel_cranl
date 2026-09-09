# backend/src/jadawel/core/admin/users/handler.py

- UserAdminHandler · class · L25-L172 — class UserAdminHandler
- create_user · method · L26-L58 — def create_user( self, requesting_user: User, username: str, name: str, password: str, is_active: bool = True, is_staff: bool = False, )
- update_user · method · L60-L125 — def update_user( self, requesting_user: User, user_id: int, username: Optional[str] = None, name: Optional[str] = None, password: Optional[str] = None, is_active: Optional[bool] = None, is_staff: Optional[bool] = None, )
- _raise_if_locking_self_out_of_admin · method · L128-L142 — def _raise_if_locking_self_out_of_admin( is_active, is_staff, requesting_user, user_id )
- delete_user · method · L144-L167 — def delete_user(self, requesting_user: User, user_id: int)
- _raise_if_not_permitted · method · L170-L172 — def _raise_if_not_permitted(requesting_user)
