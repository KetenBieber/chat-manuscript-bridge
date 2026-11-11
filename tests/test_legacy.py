import json

import pytest

from chat_manuscript_bridge.legacy import LegacyReader
from chat_manuscript_bridge.models import BridgeError, canonical_json, git_blob_sha, sha256


class Storage:
    def __init__(self):
        self.files = {}
        self.reads = []
        self.writes = 0

    def read(self, path):
        self.reads.append(path)
        return self.files.get(path)

    def create(self, path, body):
        self.writes += 1
        self.files[path] = body
        return git_blob_sha(body)

    def list_names(self, path):
        return []


def fixture():
    store = Storage()
    original = b"# Synthetic article\n\nA factual demo.\n"
    prefix = "example-legacy/bridge"
    name = "demo_article"
    store.files[prefix + "/originals/" + name + ".md"] = original
    store.files[prefix + "/ready/" + name + ".json"] = canonical_json({
        "article_id": name,
        "status": "ready",
        "source_git_blob_sha": git_blob_sha(original),
        "source_path": prefix + "/originals/" + name + ".md",
    })
    return store, LegacyReader(store, prefix), sha256(original)


def test_read_only_legacy_original_and_sha():
    store, reader, digest = fixture()
    state = reader.inspect("demo_article")
    assert state["source_verified"]
    assert state["source_sha256"] == digest
    assert not state["published_api_verified"]
    assert store.writes == 0


def test_source_mismatch_fails_closed():
    store, reader, _ = fixture()
    store.files["example-legacy/bridge/originals/demo_article.md"] = b"Changed"
    with pytest.raises(BridgeError):
        reader.inspect("demo_article")
    assert store.writes == 0


def test_legacy_receipts_are_strictly_source_bound():
    store, reader, digest = fixture()
    name = "example-legacy/bridge/feishu-receipts/demo_article_" + digest[:16] + ".json"
    store.files[name] = canonical_json({
        "published": True,
        "source_sha256": digest,
        "document_url": "https://example.feishu.cn/docx/synthetic-id",
    })
    state = reader.inspect("demo_article")
    assert state["published_api_verified"]
    assert not state["layout_verified"]
    layout = ("example-legacy/bridge/feishu-layout/demo_article_" +
              digest[:16] + "_after.json")
    store.files[layout] = canonical_json({
        "source_sha256": digest,
        "layout_verified": True,
    })
    assert reader.inspect("demo_article")["layout_verified"]
    store.files[layout] = canonical_json({
        "source_sha256": "0" * 64,
        "layout_verified": True,
    })
    with pytest.raises(BridgeError):
        reader.inspect("demo_article")
    assert store.writes == 0
