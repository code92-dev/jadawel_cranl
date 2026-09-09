# backend/src/jadawel/test_utils/fixtures/user_source.py

- UserSourceFixtures · class · L15-L154 — class UserSourceFixtures
- _get_user_source_type_or_skip · method · L16-L40 — def _get_user_source_type_or_skip(self, type_name=None)
- create_user_source_with_first_type · method · L42-L44 — def create_user_source_with_first_type(self, **kwargs)
- create_user_source · method · L46-L63 — def create_user_source(self, model_class, user=None, application=None, **kwargs)
- create_user_sources_with_primary_keys · method · L65-L74 — def create_user_sources_with_primary_keys( self, user_source_type: UserSourceType, primary_keys: List[int], **kwargs ) -> List[UserSource]
- create_user_table_and_role · method · L76-L107 — def create_user_table_and_role(self, user, builder, user_role, integration=None)
- create_local_jadawel_table_user_source · method · L109-L154 — def create_local_jadawel_table_user_source( self, application=None, integration=None, table=None, user=None, **kwargs )
