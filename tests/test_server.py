import asyncio

import pytest

from chat_manuscript_bridge.models import BridgeError
from chat_manuscript_bridge.server import BearerAuth


class Seen:
    def __init__(self):
        self.calls = []

    async def __call__(self, scope, receive, send):
        self.calls.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


def test_http_bearer_denies_unauthenticated_call():
    seen = Seen()
    gate = BearerAuth(seen, "x" * 32)
    sent = []

    async def send(event):
        sent.append(event)

    async def receive():
        return {"type": "http.request"}

    asyncio.run(gate({"type": "http", "headers": []}, receive, send))
    assert [x["status"] for x in sent if x["type"] == "http.response.start"] == [401]
    assert seen.calls == []


def test_http_bearer_allows_valid_token():
    seen = Seen()
    gate = BearerAuth(seen, "x" * 32)
    sent = []

    async def send(event):
        sent.append(event)

    async def receive():
        return {"type": "http.request"}

    asyncio.run(gate({"type": "http", "headers": [(b"authorization", b"Bearer " + b"x" * 32)]},
                     receive, send))
    assert [x["status"] for x in sent if x["type"] == "http.response.start"] == [200]
    assert len(seen.calls) == 1


def test_short_auth_secret_rejected():
    with pytest.raises(BridgeError):
        BearerAuth(Seen(), "short")
