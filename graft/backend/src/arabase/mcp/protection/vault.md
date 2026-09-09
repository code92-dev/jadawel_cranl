# backend/src/arabase/mcp/protection/vault.py

- MaskTokenVaultUnavailable · class · L61-L62 — class MaskTokenVaultUnavailable(Exception)
- MaskTokenBinding · class · L66-L76 — class MaskTokenBinding
- IssuedMaskToken · class · L80-L83 — class IssuedMaskToken
- _load_active_fingerprint_key · function · L86-L97 — def _load_active_fingerprint_key() -> tuple[str, bytes]
- _load_fingerprint_key · function · L100-L110 — def _load_fingerprint_key(key_id: str) -> bytes
- RedisMaskTokenVault · class · L113-L307 — class RedisMaskTokenVault
- __init__ · method · L116-L134 — def __init__(self, redis_client: Redis | None = None)
- issue · method · L136-L137 — def issue(self, binding: MaskTokenBinding, value: Any) -> IssuedMaskToken
- issue_many · method · L139-L205 — def issue_many( self, items: list[tuple[MaskTokenBinding, Any]] ) -> list[IssuedMaskToken]
- _ensure_issuance_headroom · method · L207-L230 — def _ensure_issuance_headroom(self) -> None
- redeem · method · L232-L279 — def redeem( self, raw_handle: str, binding: MaskTokenBinding, current_value: Any ) -> bool
- delete · method · L281-L307 — def delete(self, digests: list[str]) -> None
- _issued · function · L310-L315 — def _issued(token: GeneratedMaskToken) -> IssuedMaskToken
- get_mask_token_vault · function · L318-L319 — def get_mask_token_vault() -> RedisMaskTokenVault
