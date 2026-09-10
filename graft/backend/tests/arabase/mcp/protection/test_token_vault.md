# backend/tests/arabase/mcp/protection/test_token_vault.py

- test_vault_issues_fresh_digest_only_tokens_with_fixed_ttl · function · L29-L62 — def test_vault_issues_fresh_digest_only_tokens_with_fixed_ttl()
- test_vault_issues_one_atomic_batch_with_one_redis_script · function · L69-L111 — def test_vault_issues_one_atomic_batch_with_one_redis_script(monkeypatch)
- register_counted_script · function · L87-L95 — def register_counted_script(script)
- run_script · function · L90-L93 — def run_script(*args, **kwargs)
- test_vault_rejects_an_over_capacity_batch_without_partial_records · function · L118-L143 — def test_vault_rejects_an_over_capacity_batch_without_partial_records(monkeypatch)
- test_vault_collision_does_not_overwrite_or_release_the_existing_token · function · L150-L180 — def test_vault_collision_does_not_overwrite_or_release_the_existing_token(monkeypatch)
- test_vault_redeems_only_the_same_cell_and_current_value · function · L187-L216 — def test_vault_redeems_only_the_same_cell_and_current_value()
- test_vault_rejects_foreign_stale_and_display_only_bindings · function · L235-L259 — def test_vault_rejects_foreign_stale_and_display_only_bindings(variant)
- test_vault_expiry_revokes_a_token_without_plaintext_fallback · function · L266-L285 — def test_vault_expiry_revokes_a_token_without_plaintext_fallback()
- test_vault_capacity_is_reserved_atomically_and_released_on_cleanup · function · L292-L315 — def test_vault_capacity_is_reserved_atomically_and_released_on_cleanup(monkeypatch)
- test_production_vault_stops_issuance_at_memory_safety_floor · function · L322-L351 — def test_production_vault_stops_issuance_at_memory_safety_floor(monkeypatch)
