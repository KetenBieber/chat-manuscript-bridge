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

def test_inspect_configuration_explains_real_public_release_boundary(monkeypatch):
    from chat_manuscript_bridge.server import inspect_configuration
    monkeypatch.setenv("BRIDGE_GITHUB_REPO", "example/private-docs")
    monkeypatch.setenv("BRIDGE_GITHUB_TOKEN", "synthetic-test-token")
    monkeypatch.setenv("BRIDGE_ALLOWED_DESTINATIONS", "private-knowledge-base")
    state = inspect_configuration()
    assert state["github_configured"] is True
    assert state["allowed_destinations_count"] == 1
    assert state["capabilities"]["immutable_github_originals"] is True
    assert state["capabilities"]["feishu_import_worker_included"] is False
    assert state["capabilities"]["oauth_21_authorization_server_included"] is False
    assert state["usage"]["one_step_handoff_tool"] == "publish_this_chat"
    assert "synthetic-test-token" not in str(state)


def test_guided_prompts_reinforce_source_and_retry_safety():
    from chat_manuscript_bridge.server import (
        manuscript_handoff_checklist, publication_reconciliation_checklist
    )
    guide = manuscript_handoff_checklist()
    recovery = publication_reconciliation_checklist()
    assert "complete" in guide
    assert "NOT a" in guide
    assert "get_publication_status" in recovery
    assert "NOT be retried blindly" in recovery
