# backend/src/advocate/connection.py

- advocate_getaddrinfo · function · L14-L26 — def advocate_getaddrinfo(host, port, get_canonname=False)
- fix_addrinfo · function · L29-L49 — def fix_addrinfo(records)
- fix_record · function · L38-L41 — def fix_record(record, canonname)
- validating_create_connection · function · L53-L129 — def validating_create_connection( address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, socket_options=None, validator=None, )
- _validating_new_conn · function · L134-L165 — def _validating_new_conn(self)
- ValidatingHTTPConnection · class · L173-L178 — class ValidatingHTTPConnection(HTTPConnection)
- __init__ · method · L176-L178 — def __init__(self, *args, **kwargs)
- ValidatingHTTPSConnection · class · L181-L186 — class ValidatingHTTPSConnection(HTTPSConnection)
- __init__ · method · L184-L186 — def __init__(self, *args, **kwargs)
