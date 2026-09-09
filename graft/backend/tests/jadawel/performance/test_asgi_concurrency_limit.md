# backend/tests/jadawel/performance/test_asgi_concurrency_limit.py

- test_asgi_concurrency_no_limit · function · L10-L92 — def test_asgi_concurrency_no_limit(async_event_loop, test_thread)
- close_el · function · L29-L44 — async def close_el()
- make_app · function · L46-L57 — def make_app(qevents)
- dummy_app · function · L47-L55 — async def dummy_app(scope, receive, send)
- receive · function · L67-L68 — def receive()
- send · function · L70-L71 — async def send(out)
- test_asgi_concurrency_limit · function · L95-L205 — def test_asgi_concurrency_limit(async_event_loop, test_thread)
- close_el · function · L116-L131 — async def close_el()
- make_app · function · L133-L144 — def make_app(qevents)
- dummy_app · function · L134-L142 — async def dummy_app(scope, receive, send)
- receive · function · L151-L152 — async def receive()
- send · function · L154-L155 — async def send(out)
