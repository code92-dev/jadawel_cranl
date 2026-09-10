# backend/src/jadawel/contrib/database/tokens/handler.py

- TokenHandler · class · L38-L508 — class TokenHandler
- get_by_key · method · L39-L65 — def get_by_key(self, key)
- get_token · method · L67-L99 — def get_token(self, user, token_id, base_queryset=None)
- generate_unique_key · method · L101-L129 — def generate_unique_key(self, length=32, max_tries=1000)
- create_token · method · L131-L159 — def create_token(self, user, workspace, name)
- rotate_token_key · method · L161-L189 — def rotate_token_key(self, user, token)
- update_token · method · L191-L215 — def update_token(self, user, token, name)
- update_token_permissions · method · L217-L375 — def update_token_permissions( self, user, token, create=None, read=None, update=None, delete=None )
- equals · function · L341-L351 — def equals(permission_1, permission_2)
- has_table_permission · method · L377-L418 — def has_table_permission( self, token: Token, type_name: Union[str, List[str]], table: Table ) -> bool
- get_token_from_request · method · L420-L429 — def get_token_from_request(self, request: Request) -> Token | None
- raise_table_permission_error · method · L431-L447 — def raise_table_permission_error(self, table: Table, type_name: str | list[str])
- check_table_permissions · method · L449-L489 — def check_table_permissions( self, request_or_token: Request | Token, type_name: str | list[str], table: Table, force_check=False, )
- delete_token · method · L491-L508 — def delete_token(self, user, token)
