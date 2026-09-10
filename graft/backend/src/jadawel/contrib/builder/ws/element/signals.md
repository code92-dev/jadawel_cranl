# backend/src/jadawel/contrib/builder/ws/element/signals.py

- element_created · function · L23-L41 — def element_created( sender, element: Element, user: AbstractUser, before_id=None, **kwargs )
- elements_created · function · L45-L65 — def elements_created( sender, elements: List[Element], page: Page, user: AbstractUser, **kwargs )
- element_updated · function · L69-L84 — def element_updated(sender, element: Element, user: AbstractUser, **kwargs)
- element_moved · function · L88-L107 — def element_moved( sender, element: Element, before: Element, user: AbstractUser, **kwargs )
- element_deleted · function · L111-L125 — def element_deleted(sender, page: Page, element_id: int, user: AbstractUser, **kwargs)
- element_orders_recalculated · function · L129-L142 — def element_orders_recalculated( sender, page: Page, user: AbstractUser = None, **kwargs )
- elements_moved · function · L146-L167 — def elements_moved( sender, page: Page, elements: List[Element], user: AbstractUser = None, **kwargs )
