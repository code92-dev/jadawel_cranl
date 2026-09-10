# backend/tests/jadawel/contrib/database/webhooks/test_webhook_validators.py

- _DummySocket · class · L16-L25 — class _DummySocket
- settimeout · method · L17-L18 — def settimeout(self, *args, **kwargs)
- connect · method · L20-L22 — def connect(self, *args, **kwargs): # Never do real outbound network in unit tests.
- close · method · L24-L25 — def close(self)
- _disable_real_network · function · L29-L51 — def _disable_real_network(monkeypatch)
- deterministic_getaddrinfo · function · L30-L44 — def deterministic_getaddrinfo(host, port, *args, **kwargs)
- test_advocate_blocks_internal_address · function · L54-L60 — def test_advocate_blocks_internal_address(): # This request should go through
- test_advocate_blocks_invalid_urls · function · L63-L73 — def test_advocate_blocks_invalid_urls(): # This request should go through
- test_advocate_whitelist_rules · function · L77-L84 — def test_advocate_whitelist_rules(): # This request should go through
- test_advocate_blacklist_rules · function · L88-L100 — def test_advocate_blacklist_rules(): # This request should not go through
- test_hostname_blacklist_rules · function · L106-L113 — def test_hostname_blacklist_rules(): # This request should not go through
- test_hostname_blacklist_rules_only_allow_one_host · function · L119-L129 — def test_hostname_blacklist_rules_only_allow_one_host()
- test_advocate_combination_of_whitelist_blacklist_rules · function · L136-L149 — def test_advocate_combination_of_whitelist_blacklist_rules()
- test_advocate_hostname_blacklist_overrides_ip_lists · function · L157-L172 — def test_advocate_hostname_blacklist_overrides_ip_lists()
