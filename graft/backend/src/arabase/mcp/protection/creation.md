# backend/src/arabase/mcp/protection/creation.py

- CompositeEndpointCreationResult · class · L28-L30 — class CompositeEndpointCreationResult
- validate_idempotency_key · function · L33-L38 — def validate_idempotency_key(value: str | None) -> str
- create_protected_mcp_endpoint · function · L41-L86 — def create_protected_mcp_endpoint( *, user, name: str, workspace_id: int, protected_field_ids: list[int], confirm_empty_policy: bool, idempotency_key: str, ) -> CompositeEndpointCreationResult
- _create_protected_mcp_endpoint · function · L90-L134 — def _create_protected_mcp_endpoint( *, user, name: str, workspace_id: int, protected_field_ids: list[int], idempotency_key: str, fingerprint: str, ) -> CompositeEndpointCreationResult
- _load_and_validate_fields · function · L137-L163 — def _load_and_validate_fields(user, workspace, field_ids: list[int]) -> list[Field]
- _request_fingerprint · function · L166-L182 — def _request_fingerprint( name: str, workspace_id: int, field_ids: list[int], confirm_empty_policy: bool, ) -> str
