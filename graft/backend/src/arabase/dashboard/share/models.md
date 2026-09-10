# backend/src/arabase/dashboard/share/models.py

- DashboardShare · class · L10-L62 — class DashboardShare(HierarchicalModelMixin, CreatedAndUpdatedOnMixin, models.Model)
- Meta · class · L39-L40 — class Meta
- get_parent · method · L42-L43 — def get_parent(self)
- has_password · method · L46-L47 — def has_password(self) -> bool
- create_new_slug · method · L50-L51 — def create_new_slug() -> str
- rotate_slug · method · L53-L54 — def rotate_slug(self)
- set_password · method · L56-L57 — def set_password(self, password: str)
- check_public_password · method · L59-L62 — def check_public_password(self, password: str) -> bool
