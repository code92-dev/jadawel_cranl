# backend/src/jadawel/core/subjects.py

- UserSubjectType · class · L10-L38 — class UserSubjectType(SubjectType)
- are_in_workspace · method · L14-L28 — def are_in_workspace( self, subjects: List[Subject], workspace: Workspace ) -> List[bool]
- get_serializer · method · L30-L33 — def get_serializer(self, model_instance, **kwargs)
- get_users_included_in_subject · method · L35-L38 — def get_users_included_in_subject( self, subject: AbstractUser ) -> List[AbstractUser]
- AnonymousUserSubjectType · class · L41-L60 — class AnonymousUserSubjectType(SubjectType)
- are_in_workspace · method · L45-L52 — def are_in_workspace( self, subjects: List[Subject], workspace: Workspace ) -> List[bool]
- get_serializer · method · L54-L55 — def get_serializer(self, model_instance, **kwargs)
- get_users_included_in_subject · method · L57-L60 — def get_users_included_in_subject( self, subject: AnonymousUser ) -> List[AbstractUser]
