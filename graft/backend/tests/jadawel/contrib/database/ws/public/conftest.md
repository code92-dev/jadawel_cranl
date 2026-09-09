# backend/tests/jadawel/contrib/database/ws/public/conftest.py

- PublicWebsocketTester · class · L17-L46 — class PublicWebsocketTester(Generic[T], abc.ABC)
- __init__ · method · L18-L19 — def __init__(self, data_fixture)
- newly_created_field_visible_by_default · method · L23-L24 — def newly_created_field_visible_by_default(self)
- create_public_view · method · L27-L35 — def create_public_view( self, user: AbstractUser, table: Table, visible_fields: Optional[List[Field]] = None, hidden_fields: Optional[List[Field]] = None, **kwargs, ) -> T
- create_other_views_that_should_not_get_realtime_signals · method · L37-L46 — def create_other_views_that_should_not_get_realtime_signals( self, user: AbstractUser, table: Table, mock_broadcast_to_channel_group )
- GridViewPublicWebsocketTester · class · L49-L73 — class GridViewPublicWebsocketTester(PublicWebsocketTester[GridView])
- create_public_view · method · L52-L73 — def create_public_view( self, user: AbstractUser, table: Table, visible_fields: Optional[List[Field]] = None, hidden_fields: Optional[List[Field]] = None, **kwargs, ) -> GridView
- GalleryViewPublicWebsocketTester · class · L76-L96 — class GalleryViewPublicWebsocketTester(PublicWebsocketTester[GalleryView])
- create_public_view · method · L79-L96 — def create_public_view( self, user: AbstractUser, table: Table, visible_fields: Optional[List[Field]] = None, hidden_fields: Optional[List[Field]] = None, **kwargs, ) -> GalleryView
- public_realtime_view_tester · function · L109-L137 — def public_realtime_view_tester(request, data_fixture)
