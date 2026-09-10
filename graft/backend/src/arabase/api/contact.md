# backend/src/arabase/api/contact.py

- _configured_rate · function · L38-L63 — def _configured_rate() -> str
- contact_recipients · function · L66-L75 — def contact_recipients() -> list[str]
- ContactFormThrottle · class · L78-L103 — class ContactFormThrottle(SimpleRateThrottle)
- get_cache_key · method · L91-L103 — def get_cache_key(self, request: Request, view) -> str: # Unlike AnonRateThrottle this does not exempt authenticated users: # nothing about this endpoint requires an account, so an account should # not lift the limit. # # `get_ident` is only countable because `NUM_PROXIES` is set (`base.py`). # Left unset, DRF keys on the whole `X-Forwarded-For` string, which the # caller controls — and this endpoint sends mail, so an uncountable # limit here is an open relay.
- ContactFormSerializer · class · L106-L143 — class ContactFormSerializer(serializers.Serializer)
- validate_subject · method · L129-L136 — def validate_subject(self, value: str) -> str: # The subject becomes a mail header. Django raises BadHeaderError on an # embedded newline, which would surface as a 500, so an injection # attempt has to be neutralised here. Everything from the first line # break on is dropped rather than folded into the header: the smuggled # `Bcc: ...` never becomes a real header either way, but there is no # reason to carry it into the subject a human then reads.
- validate_details · method · L138-L143 — def validate_details(self, value: dict) -> dict
- _build_body · function · L146-L156 — def _build_body(data: dict, reference: str) -> str
- send_contact_email · function · L159-L177 — def send_contact_email(data: dict) -> str
- ContactFormView · class · L180-L228 — class ContactFormView(APIView)
- post · method · L198-L228 — def post(self, request: Request) -> Response
