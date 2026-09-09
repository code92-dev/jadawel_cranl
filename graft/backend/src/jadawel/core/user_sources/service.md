# backend/src/jadawel/core/user_sources/service.py

- UserSourceService · class · L30-L297 — class UserSourceService
- __init__ · method · L31-L32 — def __init__(self)
- get_user_source · method · L34-L62 — def get_user_source( self, user: AbstractUser, user_source_id: int, for_authentication: bool = False ) -> UserSource
- get_user_source_by_uid · method · L64-L92 — def get_user_source_by_uid( self, user: AbstractUser, user_source_uid: str, for_authentication: bool = False ) -> UserSource
- get_user_sources · method · L94-L121 — def get_user_sources( self, user: AbstractUser, application: Application ) -> List[UserSource]
- create_user_source · method · L123-L176 — def create_user_source( self, user: AbstractUser, user_source_type: UserSourceType, application: Application, before: Optional[UserSource] = None, **kwargs, ) -> UserSource
- update_user_source · method · L178-L222 — def update_user_source( self, user: AbstractUser, user_source: UserSourceForUpdate, **kwargs ) -> UserSource
- delete_user_source · method · L224-L245 — def delete_user_source(self, user: AbstractUser, user_source: UserSourceForUpdate)
- move_user_source · method · L247-L287 — def move_user_source( self, user: AbstractUser, user_source: UserSourceForUpdate, before: Optional[UserSource] = None, ) -> UserSource
- recalculate_full_orders · method · L289-L297 — def recalculate_full_orders(self, user: AbstractUser, application: Application)
