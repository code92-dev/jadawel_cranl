# backend/src/jadawel/contrib/builder/pages/service.py

- PageService · class · L27-L203 — class PageService
- __init__ · method · L28-L29 — def __init__(self)
- get_page · method · L31-L49 — def get_page(self, user: AbstractUser, page_id: int) -> Page
- create_page · method · L51-L84 — def create_page( self, user: AbstractUser, builder: Builder, name: str, path: str, path_params: PagePathParams = None, query_params: PageQueryParams = None, ) -> Page
- delete_page · method · L86-L105 — def delete_page(self, user: AbstractUser, page: Page)
- update_page · method · L107-L141 — def update_page(self, user: AbstractUser, page: Page, **kwargs) -> Page
- order_pages · method · L143-L177 — def order_pages( self, user: AbstractUser, builder: Builder, order: List[int] ) -> List[int]
- duplicate_page · method · L179-L203 — def duplicate_page( self, user: AbstractUser, page: Page, progress_builder: Optional[ChildProgressBuilder] = None, ) -> Page
