import pytest

from chat_manuscript_bridge.models import BridgeError, Conflict, git_blob_sha, sha256
from chat_manuscript_bridge.service import ManuscriptService


class FakeStorage:
    def __init__(self):
        self.files = {}
        self.create_calls = []

    def read(self, path):
        return self.files.get(path)

    def create(self, path, data):
        if path in self.files and self.files[path] != data:
            raise Conflict("not identical")
        self.files[path] = data
        self.create_calls.append(path)
        return git_blob_sha(data)

    def list_names(self, directory):
        prefix = directory + "/"
        return sorted(p[len(prefix):] for p in self.files
                      if p.startswith(prefix) and "/" not in p[len(prefix):])


def svc():
    store = FakeStorage()
    return ManuscriptService(store, prefix="workspace/v1",
                             allowed_destinations=("personal-vault",)), store


def test_submit_byte_identical_and_retry():
    service, store = svc()
    markdown = "# 一篇文章\n\n具有  两个空格  \n"
    first = service.submit("paper_01", markdown, "research")
    second = service.submit("paper_01", markdown, "research")
    assert first["idempotent"] is False
    assert second["idempotent"] is True
    raw = store.read("workspace/v1/originals/paper_01.md")
    assert raw == markdown.encode("utf-8")
    assert first["source_sha256"] == sha256(raw)
    assert service.status("paper_01")["status"] == "saved"


def test_changed_original_and_image_map_rejected():
    service, _ = svc()
    service.submit("a", "# A", "research",
                   {"async:figure": "https://example.org/figure.png"})
    with pytest.raises(Conflict):
        service.submit("a", "# B", "research")
    with pytest.raises(Conflict):
        service.submit("a", "# A", "research")
    with pytest.raises(Conflict):
        service.submit("a", "# A", "different",
                       {"async:figure": "https://example.org/figure.png"})


def test_no_approval_without_explicit_confirmation_and_allowlist():
    service, _ = svc()
    service.submit("p", "Original", "research")
    with pytest.raises(BridgeError):
        service.approve("p", "untrusted", confirm=True)
    preview = service.approve("p", "personal-vault")
    assert preview["requires_confirmation"]
    assert service.status("p")["status"] == "saved"
    first = service.approve("p", "personal-vault", confirm=True)
    assert first["status"] == "approved_for_delivery"
    assert service.status("p")["status"] == "approved_for_delivery"
    assert service.approve("p", "personal-vault", confirm=True)["idempotent"] is True


def test_hash_drift_blocks_status_and_publication():
    service, store = svc()
    service.submit("p", "Original", "research")
    store.files["workspace/v1/originals/p.md"] = b"changed"
    with pytest.raises(BridgeError):
        service.status("p")
    with pytest.raises(BridgeError):
        service.approve("p", "personal-vault", True)


def test_unknown_remote_attempt_remains_blocked():
    service, store = svc()
    service.submit("p", "Original", "research")
    service.approve("p", "personal-vault", True)
    manifest = service.record("jobs", "p")
    from chat_manuscript_bridge.models import canonical_json
    store.files["workspace/v1/attempts/p.json"] = canonical_json({
        "schema_version": 1, "article_id": "p",
        "source_sha256": manifest["source_sha256"], "status": "initiated",
    })
    state = service.reconcile("p")
    assert state["status"] == "upload_outcome_unknown"
    assert state["safe_to_repeat_upload"] is False
    assert state["upload_triggered"] is False


def test_layout_must_match_source_to_claim_success():
    service, store = svc()
    service.submit("p", "Original", "research")
    service.approve("p", "personal-vault", confirm=True)
    ref = service.record("jobs", "p")["source_sha256"]
    from chat_manuscript_bridge.models import canonical_json
    store.files["workspace/v1/receipts/p.json"] = canonical_json({
        "schema_version": 1, "article_id": "p", "source_sha256": ref,
        "published": True, "document_url": "https://example.feishu.cn/docx/test",
    })
    assert service.status("p")["status"] == "published_api_verified"
    store.files["workspace/v1/layout/p.json"] = canonical_json({
        "schema_version": 1, "article_id": "p", "source_sha256": "0" * 64,
        "layout_verified": True,
    })
    with pytest.raises(BridgeError):
        service.status("p")
    store.files["workspace/v1/layout/p.json"] = canonical_json({
        "schema_version": 1, "article_id": "p",
        "source_sha256": ref, "layout_verified": True,
    })
    assert service.status("p")["status"] == "layout_verified"
    assert service.status("p")["notification_status"] == "not_sent"


def test_no_duplicate_permission_if_different_destination():
    store = FakeStorage()
    first = ManuscriptService(store, prefix="workspace/v1",
                              allowed_destinations=("one", "two"))
    first.submit("p", "Original", "research")
    first.approve("p", "one", confirm=True)
    with pytest.raises(Conflict):
        first.approve("p", "two", confirm=True)


def test_list_ids_is_bounded():
    service, _ = svc()
    for name in ("a", "b", "c"):
        service.submit(name, name, "research")
    assert service.list_articles(limit=2)["article_ids"] == ["b", "c"]


def test_receipt_without_explicit_approval_is_rejected():
    service, store = svc()
    service.submit("p", "Original", "research")
    ref = service.record("jobs", "p")["source_sha256"]
    from chat_manuscript_bridge.models import canonical_json
    store.files["workspace/v1/receipts/p.json"] = canonical_json({
        "schema_version": 1, "article_id": "p", "source_sha256": ref,
        "published": True, "document_url": "https://example.feishu.cn/docx/test",
    })
    with pytest.raises(BridgeError):
        service.status("p")


def test_missing_original_with_existing_manifest_is_not_recreated():
    service, store = svc()
    service.submit("p", "Original", "research")
    del store.files["workspace/v1/originals/p.md"]
    with pytest.raises(BridgeError):
        service.submit("p", "Original", "research")
    assert "workspace/v1/originals/p.md" not in store.files
