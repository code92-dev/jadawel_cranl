# backend/src/jadawel/contrib/builder/elements/service.py

- ElementService · class · L41-L325 — class ElementService
- __init__ · method · L42-L43 — def __init__(self)
- get_element · method · L45-L63 — def get_element(self, user: AbstractUser, element_id: int) -> Element
- get_elements · method · L65-L88 — def get_elements(self, user: AbstractUser, page: Page) -> List[Element]
- get_builder_elements · method · L90-L108 — def get_builder_elements( self, user: AbstractUser, builder: "Builder" ) -> List[Element]
- create_element · method · L110-L166 — def create_element( self, user: AbstractUser, element_type: ElementType, page: Page, before: Optional[Element] = None, order: Optional[int] = None, **kwargs, ) -> Element
- update_element · method · L168-L193 — def update_element( self, user: AbstractUser, element: ElementForUpdate, **kwargs ) -> Element
- delete_element · method · L195-L214 — def delete_element(self, user: AbstractUser, element: ElementForUpdate)
- move_element · method · L216-L273 — def move_element( self, user: AbstractUser, target_page: Page, element: ElementForUpdate, parent_element: Optional[Element], place_in_container: str, before: Optional[Element] = None, ) -> Element
- recalculate_full_orders · method · L275-L283 — def recalculate_full_orders(self, user: AbstractUser, page: Page)
- duplicate_element · method · L285-L325 — def duplicate_element( self, user: AbstractUser, element: Element ) -> ElementsAndWorkflowActions
