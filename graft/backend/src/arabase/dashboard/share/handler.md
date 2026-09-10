# backend/src/arabase/dashboard/share/handler.py

- token_lifetime · function · L21-L29 — def token_lifetime() -> timedelta
- DashboardShareHandler · class · L32-L173 — class DashboardShareHandler
- get_share · method · L48-L58 — def get_share(self, dashboard: Dashboard) -> DashboardShare
- get_share_or_none · method · L60-L64 — def get_share_or_none(self, dashboard: Dashboard) -> Optional[DashboardShare]
- create_share · method · L66-L70 — def create_share(self, dashboard: Dashboard) -> DashboardShare
- delete_share · method · L72-L75 — def delete_share(self, dashboard: Dashboard)
- rotate_slug · method · L77-L80 — def rotate_slug(self, share: DashboardShare) -> DashboardShare
- set_password · method · L82-L92 — def set_password( self, share: DashboardShare, password: Optional[str] ) -> DashboardShare
- get_share_by_slug · method · L94-L112 — def get_share_by_slug(self, slug: str) -> DashboardShare
- get_public_share_by_slug · method · L114-L144 — def get_public_share_by_slug( self, slug: str, authorization_token: Optional[str] = None, ) -> DashboardShare
- _get_jwt_secret · method · L146-L147 — def _get_jwt_secret(self, share: DashboardShare) -> str
- encode_token · method · L149-L159 — def encode_token(self, share: DashboardShare) -> str
- decode_token · method · L161-L166 — def decode_token(self, share: DashboardShare, token: str) -> Dict[str, Any]
- is_token_valid · method · L168-L173 — def is_token_valid(self, share: DashboardShare, token: str) -> bool
- get_public_authorization_token · function · L176-L188 — def get_public_authorization_token(request: Request) -> Optional[str]
