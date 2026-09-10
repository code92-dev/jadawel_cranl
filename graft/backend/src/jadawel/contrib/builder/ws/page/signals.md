# backend/src/jadawel/contrib/builder/ws/page/signals.py

- page_created · function · L20-L30 — def page_created(sender, page: Page, user: AbstractUser, **kwargs)
- page_updated · function · L34-L47 — def page_updated(sender, page: Page, user: AbstractUser, **kwargs)
- page_deleted · function · L51-L61 — def page_deleted(sender, builder: Builder, page_id: int, user: AbstractUser, **kwargs)
- page_reordered · function · L65-L82 — def page_reordered( sender, builder: Builder, order: List[int], user: AbstractUser, **kwargs ): # Hashing all values here to not expose real ids of pages a user might not have # access to
