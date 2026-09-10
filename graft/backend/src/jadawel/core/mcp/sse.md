# backend/src/jadawel/core/mcp/sse.py

- DjangoChannelsSseServerTransport · class · L48-L227 — class DjangoChannelsSseServerTransport
- __init__ · method · L57-L65 — def __init__(self, endpoint: str) -> None
- connect_sse · method · L68-L167 — async def connect_sse(self, scope: "Scope", receive: "Receive", send: "Send")
- sse_writer · function · L110-L129 — async def sse_writer()
- group_listener · function · L131-L150 — async def group_listener()
- response_wrapper · function · L155-L161 — async def response_wrapper(scope: Scope, receive: Receive, send: Send)
- handle_post_message · method · L169-L227 — async def handle_post_message( self, scope: "Scope", receive: "Receive", send: "Send" ) -> None
