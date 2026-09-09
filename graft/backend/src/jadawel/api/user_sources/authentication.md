# backend/src/jadawel/api/user_sources/authentication.py

- NotUserSourceToken · class · L29-L30 — class NotUserSourceToken(Exception)
- UserSourceJSONWebTokenAuthentication · class · L33-L177 — class UserSourceJSONWebTokenAuthentication(JWTAuthentication)
- __init__ · method · L39-L53 — def __init__( self, use_user_source_authentication_header: bool = False, *args, **kwargs )
- get_header · method · L55-L68 — def get_header(self, request)
- authenticate · method · L70-L177 — def authenticate(self, request: Request) -> Optional[Tuple[AuthUser, Token]]
- UserSourceJSONWebTokenAuthenticationExtension · class · L180-L193 — class UserSourceJSONWebTokenAuthenticationExtension(OpenApiAuthenticationExtension)
- get_security_definition · method · L188-L193 — def get_security_definition(self, auto_schema)
