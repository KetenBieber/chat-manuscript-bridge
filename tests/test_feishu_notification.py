import pytest

from chat_manuscript_bridge.feishu_notification import notify_publication, notification_status
from chat_manuscript_bridge.models import BridgeError, Conflict, canonical_json, git_blob_sha
from chat_manuscript_bridge.service import ManuscriptService


class MemoryStorage:
    def __init__(self):
        self.files = {}

    def read(self, path):
        return self.files.get(path)

    def create(self, path, data):
        if path in self.files and self.files[path] != data:
            raise Conflict("immutable record collision")
        self.files[path] = data
        return git_blob_sha(data)

    def list_names(self, directory):
        return []


def published_fixture(monkeypatch):
    monkeypatch.setenv("FEISHU_APP_ID", "test-app")
    monkeypatch.setenv("FEISHU_APP_SECRET", "test-secret")
    monkeypatch.setenv("FEISHU_NOTIFY_RECEIVE_ID_TYPE", "open_id")
    monkeypatch.setenv("FEISHU_NOTIFY_RECEIVE_ID", "ou_1234567890abcdefgh")
    storage = MemoryStorage()
    service = ManuscriptService(storage, prefix="docs/v1", allowed_destinations=("vault",))
    service.submit("example", "# Test", "research")
    service.approve("example", "vault", True)
    sha = service.record("jobs", "example")["source_sha256"]
    url = "https://my.feishu.cn/docx/ABCD"
    storage.files["docs/v1/receipts/example.json"] = canonical_json({
        "schema_version": 1, "article_id": "example", "source_sha256": sha,
        "published": True, "document_url": url,
    })
    storage.files["docs/v1/layout/example.json"] = canonical_json({
        "schema_version": 1, "article_id": "example", "source_sha256": sha,
        "layout_verified": True, "document_url": url,
    })
    return service, storage


def test_confirm_preview_never_sends(monkeypatch):
    service, _ = published_fixture(monkeypatch)
    response = notify_publication(service, "example")
    assert response["status"] == "requires_confirmation"
    assert notification_status(service, "example")["status"] == "not_sent"


def test_verified_im_send_records_real_id_and_never_duplicates(monkeypatch):
    service, storage = published_fixture(monkeypatch)
    calls = []
    def send(kind, recipient, text):
        calls.append((kind, recipient, text))
        return "om_valid_reply_123"
    first = notify_publication(service, "example", confirm=True, send=send)
    second = notify_publication(service, "example", confirm=True, send=send)
    assert first["message_id"] == second["message_id"] == "om_valid_reply_123"
    assert len(calls) == 1
    assert "docs/v1/notification-attempts/example.json" in storage.files
    assert service.status("example")["notification_status"] == "sent"


def test_timeout_keeps_claim_and_refuses_resend(monkeypatch):
    service, _ = published_fixture(monkeypatch)
    calls = []
    def ambiguous(*args):
        calls.append(1)
        raise TimeoutError("unknown")
    with pytest.raises(TimeoutError):
        notify_publication(service, "example", confirm=True, send=ambiguous)
    assert notification_status(service, "example")["status"] == "outcome_unknown"
    assert notify_publication(service, "example", confirm=True, send=ambiguous)["safe_to_resend"] is False
    assert calls == [1]


def test_unverified_layout_blocks_notification(monkeypatch):
    service, storage = published_fixture(monkeypatch)
    storage.files["docs/v1/layout/example.json"] = canonical_json({
        "schema_version": 1, "article_id": "example",
        "source_sha256": service.record("jobs", "example")["source_sha256"],
        "layout_verified": False, "document_url": "https://my.feishu.cn/docx/ABCD"
    })
    with pytest.raises(BridgeError):
        notify_publication(service, "example", confirm=True, send=lambda *_: "om_bad")
    assert not any("notification-attempts" in path for path in storage.files)


def test_non_feishu_url_rejected(monkeypatch):
    service, storage = published_fixture(monkeypatch)
    sha = service.record("jobs", "example")["source_sha256"]
    url = "https://example.com/docx/fake"
    for section in ("layout", "receipts"):
        data = __import__("json").loads(storage.files[f"docs/v1/{section}/example.json"])
        data["document_url"] = url
        storage.files[f"docs/v1/{section}/example.json"] = canonical_json(data)
    with pytest.raises(BridgeError):
        notify_publication(service, "example", confirm=True, send=lambda *_: "om_bad")
