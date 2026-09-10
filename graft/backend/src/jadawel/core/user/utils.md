# backend/src/jadawel/core/user/utils.py

- UserSessionPayload · class · L14-L16 — class UserSessionPayload
- normalize_email_address · function · L19-L30 — def normalize_email_address(email)
- generate_session_tokens_for_user · function · L33-L54 — def generate_session_tokens_for_user( user: AbstractUser, include_refresh_token: bool = False, verified_email_claim: Optional[str] = None, ) -> Dict[str, str]
- sign_user_session · function · L57-L77 — def sign_user_session(user_id: int, refresh_token: str) -> str
- prepare_user_tokens_payload · function · L80-L105 — def prepare_user_tokens_payload( user_id: int, access_token: Union[AccessToken, str], refresh_token: Optional[Union[RefreshToken, str]] = None, ) -> Dict[str, str]
