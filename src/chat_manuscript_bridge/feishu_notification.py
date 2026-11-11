"""Optional Feishu IM notification after a verified external publication.

This module does not upload documents. It consumes the source-bound publication
and layout records created by an independently connected delivery worker.
An immutable attempt is stored before the message API call: ambiguous API
outcomes are never automatically retried.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from urllib import error, request
from urllib.parse import urlsplit

from .models import BridgeError, now_utc
from .service import ManuscriptService

_TYPES = {"open_id", "user_id", "union_id", "chat_id", "email"}


def _json_post(url: str, body: dict, *, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                          headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=25) as response:
            if response.status != 200:
                raise BridgeError("Feishu HTTP request failed")
            data = response.read(65537)
    except (error.URLError, TimeoutError, OSError) as exc:
        raise BridgeError("Feishu transport outcome is uncertain; do not retry blindly") from exc
    if len(data) > 65536:
        raise BridgeError("Feishu API response exceeds safe limit")
    try:
        result = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise BridgeError("Feishu API response is invalid; do not retry blindly") from exc
    if not isinstance(result, dict):
        raise BridgeError("Unexpected Feishu API response")
    return result


def _feishu_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    u = urlsplit(url)
    host = (u.hostname or "").lower()
    return (u.scheme == "https" and u.username is None and u.password is None
            and u.port is None
            and (host == "feishu.cn" or host.endswith(".feishu.cn")
                 or host == "larksuite.com" or host.endswith(".larksuite.com"))
            and u.path.startswith("/docx/"))


def _config() -> tuple[str, str, str, str]:
    app_id = os.getenv("FEISHU_APP_ID", "").strip()
    secret = os.getenv("FEISHU_APP_SECRET", "").strip()
    kind = os.getenv("FEISHU_NOTIFY_RECEIVE_ID_TYPE", "open_id").strip()
    recipient = os.getenv("FEISHU_NOTIFY_RECEIVE_ID", "").strip()
    if not app_id or not secret or not recipient:
        raise BridgeError("Feishu app credentials or explicit notification recipient missing")
    if (kind not in _TYPES or not re.fullmatch(r"[^\s<>]{2,256}", recipient)
            or (kind == "open_id" and not re.fullmatch(r"ou_[A-Za-z0-9_-]{16,128}", recipient))):
        raise BridgeError("Invalid Feishu notification recipient")
    return app_id, secret, kind, recipient


def _token(app_id: str, secret: str) -> str:
    result = _json_post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                        {"app_id": app_id, "app_secret": secret})
    token = result.get("tenant_access_token")
    if result.get("code") != 0 or not isinstance(token, str) or not token:
        raise BridgeError("Feishu token acquisition rejected")
    return token


def notification_status(service: ManuscriptService, article_id: str) -> dict:
    state = service.status(article_id)
    attempt = service.record("notification-attempts", article_id)
    notice = service.record("notifications", article_id)
    if notice and notice.get("status") == "sent":
        return {"article_id": article_id, "status": "sent",
                "message_id": notice.get("message_id"),
                "document_url": state.get("document_url")}
    if attempt:
        return {"article_id": article_id, "status": "outcome_unknown",
                "safe_to_resend": False, "requires_manual_reconciliation": True}
    return {"article_id": article_id, "status": "not_sent",
            "layout_verified": state["layout_verified"]}


def notify_publication(service: ManuscriptService, article_id: str, *,
                       confirm: bool = False, send=None) -> dict:
    """Send once only after matching immutable source, publication and layout.

    The send callback is injectable for unit tests. Production uses Feishu's real
    IM API and records its returned message ID, never fabricating acknowledgement.
    """
    state = service.status(article_id)
    if not state["layout_verified"] or state["status"] != "layout_verified":
        raise BridgeError("Article has no source-bound verified Feishu layout")
    source_sha = state["source_sha256"]
    url = state["document_url"]
    receipt = service.record("receipts", article_id)
    layout = service.record("layout", article_id)
    if (not _feishu_url(url) or not receipt or not layout
            or receipt.get("document_url") != url
            or layout.get("document_url") != url
            or layout.get("source_sha256") != source_sha
            or receipt.get("source_sha256") != source_sha):
        raise BridgeError("Published Feishu URL and layout evidence do not match")
    previous = notification_status(service, article_id)
    if previous["status"] != "not_sent":
        return previous
    if not confirm:
        return {"article_id": article_id, "status": "requires_confirmation",
                "document_url": url, "source_sha256": source_sha}
    app_id, secret, kind, recipient = _config()
    # Resolve credentials before claiming the once-only send.
    access = None if send is not None else _token(app_id, secret)
    fingerprint = hashlib.sha256((kind + ":" + recipient).encode("utf-8")).hexdigest()
    attempt = {"schema_version": 1, "article_id": article_id,
               "source_sha256": source_sha, "document_url": url,
               "recipient_type": kind, "recipient_fingerprint": fingerprint,
               "state": "claimed", "claimed_at_utc": now_utc(),
               "claim_nonce": secrets.token_hex(16)}
    # Never silently overwrite a previous attempt; even an HTTP timeout may
    # mean Feishu actually delivered the message.
    if service.record("notification-attempts", article_id) is not None:
        return notification_status(service, article_id)
    service._create_record("notification-attempts", article_id, attempt)
    if service.record("notification-attempts", article_id) != attempt:
        raise BridgeError("Notification claim readback failed; no send attempted")
    body = f"📚 文章已发布\n文章 ID：{article_id}\n完整文档：{url}"
    if send is None:
        reply = _json_post(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=" + kind,
            {"receive_id": recipient, "msg_type": "text",
             "content": json.dumps({"text": body}, ensure_ascii=False)},
            token=access)
        if reply.get("code") != 0:
            raise BridgeError("Feishu IM API rejected message; reconcile claim before retry")
        message_id = (reply.get("data") or {}).get("message_id")
    else:
        message_id = send(kind, recipient, body)
    if not isinstance(message_id, str) or not message_id:
        raise BridgeError("Feishu IM response lacks message_id; outcome uncertain")
    notice = {"schema_version": 1, "article_id": article_id,
              "source_sha256": source_sha, "document_url": url,
              "status": "sent", "message_id": message_id}
    service._create_record("notifications", article_id, notice)
    if service.record("notifications", article_id) != notice:
        raise BridgeError("Feishu delivered but GitHub receipt readback failed; do not resend")
    return {"article_id": article_id, "status": "sent", "message_id": message_id,
            "document_url": url}
