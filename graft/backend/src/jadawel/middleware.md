# backend/src/jadawel/middleware.py

- json_error_404_add_trailing_slash · function · L13-L31 — def json_error_404_add_trailing_slash(path: str) -> HttpResponse
- json_error_404_not_found · function · L34-L38 — def json_error_404_not_found(path: str) -> HttpResponse
- json_is_accepted · function · L41-L43 — def json_is_accepted(request: HttpRequest) -> bool
- JadawelCustomHttp404Middleware · class · L46-L65 — class JadawelCustomHttp404Middleware
- __init__ · method · L47-L48 — def __init__(self, get_response: Callable[[HttpRequest], HttpResponse])
- __call__ · method · L50-L65 — def __call__(self, request: HttpRequest) -> HttpResponse
- ClearContextMiddleware · class · L68-L84 — class ClearContextMiddleware
- __init__ · method · L74-L75 — def __init__(self, get_response: Callable[[HttpRequest], HttpResponse])
- __call__ · method · L77-L84 — def __call__(self, request: HttpRequest) -> HttpResponse
- ClearDBStateMiddleware · class · L87-L99 — class ClearDBStateMiddleware
- __init__ · method · L93-L94 — def __init__(self, get_response: Callable[[HttpRequest], HttpResponse])
- __call__ · method · L96-L99 — def __call__(self, request)
