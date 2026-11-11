"""Read-only compatibility auditor for a previous GitHub manuscript protocol.

Never writes the old repository, triggers publication, or changes source IDs.
This module is intentionally provider-neutral: old path prefix is configured
by the operator, and no person's publication data is embedded in the code.
"""
from __future__ import annotations

from .models import BridgeError, decode_record, git_blob_sha, sha256, validate_article_id
from .storage import Storage, validate_prefix


class LegacyReader:
    def __init__(self, storage: Storage, legacy_prefix: str):
        self.storage = storage
        self.prefix = validate_prefix(legacy_prefix)

    def _read_json(self, path: str) -> dict | None:
        import json
        data = self.storage.read(path)
        if data is None:
            return None
        try:
            value = json.loads(data.decode("utf-8"))
        except (ValueError, UnicodeError) as exc:
            raise BridgeError("Corrupted legacy JSON") from exc
        if not isinstance(value, dict):
            raise BridgeError("Invalid legacy JSON object")
        return value

    def inspect(self, article_id: str) -> dict:
        article_id = validate_article_id(article_id)
        ready = self._read_json(self.prefix + "/ready/" + article_id + ".json")
        if not ready:
            raise BridgeError("Legacy ready manifest not found")
        original_path = self.prefix + "/originals/" + article_id + ".md"
        if ready.get("source_path") != original_path or ready.get("article_id") != article_id:
            raise BridgeError("Legacy source path does not match expected immutable original")
        original = self.storage.read(original_path)
        if original is None:
            raise BridgeError("Legacy original not found")
        git_sha = git_blob_sha(original)
        if ready.get("source_git_blob_sha") != git_sha:
            raise BridgeError("Legacy Git Blob SHA mismatch")
        digest = sha256(original)
        processed = self._read_json(self.prefix + "/processed/" + article_id + ".json")
        result = {
            "article_id": article_id,
            "legacy_prefix": self.prefix,
            "source_sha256": digest,
            "source_git_blob_sha": git_sha,
            "source_verified": True,
            "processed_receipt_found": processed is not None,
            "published_api_verified": False,
            "layout_verified": False,
            "no_writes": True,
        }
        receipt_path = self.prefix + "/feishu-receipts/" + article_id + "_" + digest[:16] + ".json"
        receipt = self._read_json(receipt_path)
        if receipt and receipt.get("published") is True:
            if receipt.get("source_sha256") != digest:
                raise BridgeError("Legacy publication source SHA mismatch")
            url = receipt.get("document_url")
            if not isinstance(url, str) or not url.startswith("https://"):
                raise BridgeError("Legacy receipt has no verified document URL")
            result["published_api_verified"] = True
            result["document_url"] = url
            layout_path = self.prefix + "/feishu-layout/" + article_id + "_" + digest[:16] + "_after.json"
            layout = self._read_json(layout_path)
            if layout:
                if layout.get("source_sha256") != digest:
                    raise BridgeError("Legacy layout source SHA mismatch")
                result["layout_verified"] = layout.get("layout_verified") is True
        return result
