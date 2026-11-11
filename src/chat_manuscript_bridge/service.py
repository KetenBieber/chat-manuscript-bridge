"""Durable user-facing handoff and read-only recovery; no fake Feishu success."""
from __future__ import annotations

import json
from typing import Callable

from .models import (
    BridgeError, Conflict, canonical_json, decode_record, git_blob_sha,
    manuscript_bytes, now_utc, sha256, validate_article_id, validate_category,
    validate_destination, validate_image_sources,
)
from .storage import Storage, validate_prefix


class ManuscriptService:
    def __init__(self, storage: Storage, *, prefix: str = "manuscripts/v1",
                 allowed_destinations: tuple[str, ...] = ()):
        self.storage = storage
        self.prefix = validate_prefix(prefix)
        self.allowed_destinations = frozenset(validate_destination(x) for x in allowed_destinations)

    def path(self, area: str, article_id: str, ext: str) -> str:
        validate_article_id(article_id)
        return self.prefix + "/" + area + "/" + article_id + "." + ext

    def record(self, area: str, article_id: str) -> dict | None:
        raw = self.storage.read(self.path(area, article_id, "json"))
        return None if raw is None else decode_record(raw, area)

    def _create_record(self, area: str, article_id: str, obj: dict) -> dict:
        raw = canonical_json(obj)
        try:
            self.storage.create(self.path(area, article_id, "json"), raw)
        except Conflict:
            existing = self.record(area, article_id)
            if existing != obj:
                raise
        return obj

    def submit(self, article_id: str, markdown: str, category: str,
               image_sources: dict[str, str] | None = None) -> dict:
        article_id = validate_article_id(article_id)
        category = validate_category(category)
        original = manuscript_bytes(markdown)
        figures = validate_image_sources(image_sources)
        content_sha = sha256(original)
        expected = {
            "schema_version": 1,
            "article_id": article_id,
            "source_path": self.path("originals", article_id, "md"),
            "source_sha256": content_sha,
            "source_git_blob_sha": git_blob_sha(original),
            "source_bytes": len(original),
            "category": category,
            "image_sources": figures,
        }
        existing_manifest = self.record("jobs", article_id)
        if existing_manifest:
            if any(existing_manifest.get(k) != v for k, v in expected.items()):
                raise Conflict("Article ID already belongs to a different source/category/Figure map")
        # An interrupted first submission can be safely resumed with the same bytes.
        self.storage.create(expected["source_path"], original)
        saved = existing_manifest or {**expected, "created_at_utc": now_utc()}
        if not existing_manifest:
            self._create_record("jobs", article_id, saved)
        return {
            "article_id": article_id, "status": "saved",
            "source_sha256": content_sha,
            "source_git_blob_sha": expected["source_git_blob_sha"],
            "idempotent": bool(existing_manifest),
        }

    def _validated_manifest(self, article_id: str) -> dict:
        article_id = validate_article_id(article_id)
        item = self.record("jobs", article_id)
        if item is None:
            raise BridgeError("Article not submitted")
        original = self.storage.read(item["source_path"])
        if (original is None or sha256(original) != item["source_sha256"]
                or git_blob_sha(original) != item["source_git_blob_sha"]
                or len(original) != item["source_bytes"]):
            raise BridgeError("Immutable original is missing or its hash has changed")
        return item

    def approve(self, article_id: str, destination: str, confirm: bool = False) -> dict:
        manifest = self._validated_manifest(article_id)
        destination = validate_destination(destination)
        if destination not in self.allowed_destinations:
            raise BridgeError("Destination is not in the server's allowed destination list")
        if not confirm:
            return {"article_id": article_id, "requires_confirmation": True,
                    "destination": destination, "source_sha256": manifest["source_sha256"]}
        obj = {
            "schema_version": 1, "article_id": article_id,
            "source_sha256": manifest["source_sha256"],
            "source_git_blob_sha": manifest["source_git_blob_sha"],
            "category": manifest["category"],
            "destination": destination,
            "explicit_user_confirmation": True,
        }
        previous = self.record("approvals", article_id)
        if previous is not None:
            if any(previous.get(k) != v for k, v in obj.items()):
                raise Conflict("Article already approved for a different source or destination")
        else:
            self._create_record("approvals", article_id,
                                {**obj, "approved_at_utc": now_utc()})
        return {"article_id": article_id, "status": "approved_for_delivery",
                "source_sha256": manifest["source_sha256"],
                "destination": destination, "idempotent": previous is not None}

    def status(self, article_id: str) -> dict:
        manifest = self._validated_manifest(article_id)
        ref = manifest["source_sha256"]
        result = {"article_id": article_id, "source_sha256": ref,
                  "source_git_blob_sha": manifest["source_git_blob_sha"],
                  "category": manifest["category"], "status": "saved",
                  "document_url": None, "layout_verified": False,
                  "notification_status": "not_sent"}
        approval = self.record("approvals", article_id)
        if approval:
            if (approval.get("source_sha256") != ref
                    or approval.get("source_git_blob_sha") != manifest["source_git_blob_sha"]):
                raise BridgeError("Approval source does not match immutable original")
            result["status"] = "approved_for_delivery"
            result["destination"] = approval.get("destination")
        attempt = self.record("attempts", article_id)
        if attempt:
            if attempt.get("source_sha256") != ref:
                raise BridgeError("Remote attempt source hash mismatch")
            result["status"] = "upload_outcome_unknown"
            result["blocker"] = "Existing attempt must be reconciled; never blindly repeat upload"
        receipt = self.record("receipts", article_id)
        if receipt:
            if (receipt.get("source_sha256") != ref
                    or receipt.get("published") is not True
                    or not isinstance(receipt.get("document_url"), str)
                    or not receipt["document_url"].startswith("https://")):
                raise BridgeError("Invalid or source-mismatched delivery receipt")
            result["status"] = "published_api_verified"
            result["document_url"] = receipt["document_url"]
            result.pop("blocker", None)
            layout = self.record("layout", article_id)
            if layout:
                if layout.get("source_sha256") != ref:
                    raise BridgeError("Layout audit source hash mismatch")
                if layout.get("layout_verified") is True:
                    result["status"] = "layout_verified"
                    result["layout_verified"] = True
        notification = self.record("notifications", article_id)
        if notification and result["layout_verified"]:
            if notification.get("source_sha256") != ref:
                raise BridgeError("Notification source hash mismatch")
            if notification.get("status") == "sent" and notification.get("message_id"):
                result["notification_status"] = "sent"
        return result

    def reconcile(self, article_id: str) -> dict:
        """Safety-first status inspection; does not invoke an external upload."""
        state = self.status(article_id)
        state["upload_triggered"] = False
        state["safe_to_repeat_upload"] = False
        state["next_action"] = (
            "audit_existing_document_in_place" if state["document_url"] else
            "inspect_remote_import_ticket_before_any_retry" if state["status"] == "upload_outcome_unknown" else
            "await_authorized_delivery_worker" if state["status"] == "approved_for_delivery" else
            "request_source_bound_approval"
        )
        return state

    def list_articles(self, limit: int = 50) -> dict:
        if not isinstance(limit, int) or not 1 <= limit <= 200:
            raise BridgeError("limit must be from 1 to 200")
        names = self.storage.list_names(self.prefix + "/jobs")
        ids = [x[:-5] for x in names if x.endswith(".json")]
        # An unreadable or incorrect job must not disappear silently.
        return {"article_ids": ids[-limit:], "returned": min(len(ids), limit)}
