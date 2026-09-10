# backend/src/jadawel/contrib/dashboard/widgets/service.py

- WidgetService · class · L22-L191 — class WidgetService
- __init__ · method · L23-L25 — def __init__(self)
- get_widget · method · L27-L51 — def get_widget(self, user: AbstractUser, widget_id: int) -> Widget
- get_widgets · method · L53-L81 — def get_widgets(self, user: AbstractUser, dashboard_id: int) -> list[Widget]
- create_widget · method · L83-L129 — def create_widget( self, user: AbstractUser, widget_type: str, dashboard_id: int, order: int | None = None, **kwargs, ) -> Widget
- update_widget · method · L131-L163 — def update_widget( self, user: AbstractUser, widget_id: int, **kwargs ) -> UpdatedWidget
- delete_widget · method · L165-L191 — def delete_widget(self, user: AbstractUser, widget_id: int) -> Widget
