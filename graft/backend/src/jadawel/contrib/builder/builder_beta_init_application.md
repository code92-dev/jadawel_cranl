# backend/src/jadawel/contrib/builder/builder_beta_init_application.py

- BuilderApplicationTypeInitApplication · class · L35-L298 — class BuilderApplicationTypeInitApplication
- __init__ · method · L40-L51 — def __init__(self, user: "AbstractUser", application: "Builder")
- get_target_table · method · L53-L85 — def get_target_table(self) -> Optional["Table"]
- create_page · method · L87-L88 — def create_page(self, name: str, path: str) -> "Page"
- create_integration · method · L90-L96 — def create_integration(self) -> "Integration"
- create_intro_element · method · L98-L120 — def create_intro_element(self, page: "Page", link_to_page: "Page") -> None
- create_table_element · method · L122-L172 — def create_table_element( self, page: "Page", table: "Table", integration: "Integration" ) -> None
- create_form_element · method · L174-L257 — def create_form_element( self, page: "Page", integration: "Integration", table: "Table" = None ) -> None
- create_container_element · method · L259-L298 — def create_container_element(self, page: "Page")
