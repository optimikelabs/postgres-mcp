from importlib import import_module

import anyio

import postgres_mcp.patch_sse


def test_safe_connect_sse_handles_broken_resource(monkeypatch):
    async def _run():
        sse_mod = import_module("mcp.server.sse")
        sse_transport_cls = sse_mod.SseServerTransport

        async def failing_connect(self, scope, receive, send):
            raise anyio.BrokenResourceError

        monkeypatch.setattr(postgres_mcp.patch_sse, "_original_connect_sse", failing_connect, raising=False)

        sse = sse_transport_cls("/msgs")
        scope = {"type": "http"}

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        status = {}

        async def send(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]

        await sse.connect_sse(scope, receive, send)
        assert status.get("code") == 204

    anyio.run(_run)
