# backend/src/jadawel/throttling/middleware.py

- ThrottleBlacklistMiddleware · class · L17-L51 — class ThrottleBlacklistMiddleware
- __init__ · method · L32-L39 — def __init__(self, get_response: Callable[[HttpRequest], HttpResponse])
- __call__ · method · L41-L51 — def __call__(self, request: HttpRequest) -> HttpResponse
- ConcurrentUserRequestsMiddleware · class · L54-L68 — class ConcurrentUserRequestsMiddleware
- __init__ · method · L61-L62 — def __init__(self, get_response: Callable[[HttpRequest], HttpResponse])
- __call__ · method · L64-L68 — def __call__(self, request: HttpRequest) -> HttpResponse
