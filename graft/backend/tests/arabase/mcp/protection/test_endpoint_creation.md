# backend/tests/arabase/mcp/protection/test_endpoint_creation.py

- test_composite_endpoint_creation_is_atomic_and_idempotent · function · L18-L54 — def test_composite_endpoint_creation_is_atomic_and_idempotent(api_client, data_fixture)
- test_empty_policy_requires_explicit_confirmation · function · L58-L79 — def test_empty_policy_requires_explicit_confirmation(api_client, data_fixture)
- test_non_empty_policy_admission_is_feature_gated · function · L84-L105 — def test_non_empty_policy_admission_is_feature_gated(api_client, data_fixture)
- test_staff_rollout_flag_allows_staff_but_not_regular_owners · function · L110-L144 — def test_staff_rollout_flag_allows_staff_but_not_regular_owners(data_fixture)
- test_composite_creation_rejects_foreign_fields_without_creating_endpoint · function · L148-L170 — def test_composite_creation_rejects_foreign_fields_without_creating_endpoint( api_client, data_fixture )
- test_composite_creation_rejects_workspace_without_membership · function · L174-L196 — def test_composite_creation_rejects_workspace_without_membership( api_client, data_fixture )
- test_composite_creation_rolls_back_endpoint_when_policy_write_fails · function · L200-L224 — def test_composite_creation_rolls_back_endpoint_when_policy_write_fails( data_fixture, monkeypatch )
- fail_policy_write · function · L209-L210 — def fail_policy_write(*args, **kwargs)
