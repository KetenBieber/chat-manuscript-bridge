"""Authenticated Streamable HTTP / stdio MCP frontend.

The direct MCP method submits a job, not a fictional synchronous Feishu
completion. This package never generates or rewrites an author's manuscript.
"""
from __future__ import annotations

import hmac
import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .models import BridgeError
from .legacy import LegacyReader
from .service import ManuscriptService
from .storage import GitHubStorage

_HOST = os.getenv("BRIDGE_ALLOWED_HOST", "localhost")
_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[_HOST, _HOST + ":*", "localhost", "localhost:*", "127.0.0.1", "127.0.0.1:*"],
    allowed_origins=["https://" + _HOST, "http://localhost", "http://127.0.0.1"],
)
mcp = FastMCP("Chat Manuscript Bridge", stateless_http=True,
              json_response=True, host="0.0.0.0",
              transport_security=_security)


def service() -> ManuscriptService:
    destinations = tuple(filter(None, (
        x.strip() for x in os.getenv("BRIDGE_ALLOWED_DESTINATIONS", "").split(",")
    )))
    return ManuscriptService(
        GitHubStorage(
            repository=os.environ["BRIDGE_GITHUB_REPO"],
            token=os.environ["BRIDGE_GITHUB_TOKEN"],
            branch=os.getenv("BRIDGE_GITHUB_BRANCH", "main"),
        ),
        prefix=os.getenv("BRIDGE_STORAGE_PREFIX", "manuscripts/v1"),
        allowed_destinations=destinations,
    )


@mcp.tool()
def inspect_configuration() -> dict:
    """Inspect setup and supported capabilities without exposing credentials.

    Start here after connecting MCP. This reports configuration presence and
    the public v0.1 integration boundary; it does not prove GitHub permissions
    or that an external publication worker is running.
    """
    return {
        "service": "chat-manuscript-bridge",
        "version": "0.1.0",
        "github_configured": bool(os.getenv("BRIDGE_GITHUB_REPO") and os.getenv("BRIDGE_GITHUB_TOKEN")),
        "allowed_destinations_count": len(tuple(filter(
            None, (x.strip() for x in os.getenv("BRIDGE_ALLOWED_DESTINATIONS", "").split(","))
        ))),
        "stage": "MCP handoff and durable job-status engine; external delivery worker required",
        "capabilities": {
            "immutable_github_originals": True,
            "sha256_and_git_blob_sha": True,
            "single_article_authorization": True,
            "source_bound_status_and_reconciliation": True,
            "feishu_import_worker_included": False,
            "oauth_21_authorization_server_included": False,
        },
        "usage": {
            "first_write_tool": "submit_manuscript",
            "one_step_handoff_tool": "publish_this_chat",
            "inspect_tool": "get_publication_status",
            "safe_recovery_tool": "reconcile_publication",
            "note": "Approved means queued for an external worker, not published.",
        },
    }


@mcp.tool()
def submit_manuscript(article_id: str, markdown: str, category: str,
                      image_sources: dict[str, str] | None = None) -> dict:
    """Save final Markdown byte-for-byte in YOUR private GitHub data repo.

    Requires article_id, markdown and category; optional image_sources maps
    original Figure markers to verified HTTPS URLs. Uses immutable IDs,
    computes actual SHA256/Git Blob SHA, and rejects source drift. Saves only;
    it NEVER uploads to Feishu or summarizes the manuscript.
    """
    return service().submit(article_id, markdown, category, image_sources)


@mcp.tool()
def approve_publication(article_id: str, destination: str, confirm: bool = False) -> dict:
    """Review or authorize ONE existing immutable source for a logical destination.

    confirm=false previews the article SHA and requires explicit consent.
    confirm=true stores a per-article approval for a server-allowlisted
    destination. A successful approval is NOT a remote publication receipt.
    """
    return service().approve(article_id, destination, confirm)


@mcp.tool()
def publish_this_chat(article_id: str, markdown: str, category: str,
                      destination: str, confirm: bool = False,
                      image_sources: dict[str, str] | None = None) -> dict:
    """One-step handoff of the FINAL, author-approved conversation manuscript.

    confirm=false previews and does not save. With explicit per-article
    permission, confirm=true stores exact Markdown, preserves optional
    Figure mappings, then approves an allowlisted logical destination.
    Public v0.1 returns a durable job with delivery_worker_started=false:
    NO Feishu upload, fabricated link or auto-rewritten article.
    """
    if not confirm:
        return {"article_id": article_id, "requires_confirmation": True,
                "category": category, "destination": destination}
    svc = service()
    # Validate authorization target before creating any private persistent record.
    if destination not in svc.allowed_destinations:
        raise BridgeError("Destination is not in the server's allowed destination list")
    source = svc.submit(article_id, markdown, category, image_sources)
    approval = svc.approve(article_id, destination, confirm=True)
    return {"article_id": article_id, "source": source,
            "approval": approval, "publication": svc.status(article_id),
            "delivery_worker_started": False}


@mcp.tool()
def get_publication_status(article_id: str) -> dict:
    """Inspect this article's verified GitHub/worker evidence by immutable ID.

    Separately reports saved, approved_for_delivery, uncertain upload,
    published_api_verified and layout_verified, plus notification_status.
    An absent real remote receipt yields no document URL.
    """
    return service().status(article_id)


@mcp.tool()
def reconcile_publication(article_id: str) -> dict:
    """Get read-only reconciliation instructions for a blocked or uncertain job.

    This call makes NO remote changes and returns safe_to_repeat_upload=false.
    If an external upload might already exist, inspect the SAME remote
    document/attempt before allowing any new upload.
    """
    return service().reconcile(article_id)


@mcp.tool()
def list_manuscripts(limit: int = 50) -> dict:
    """List article IDs (1–200 items) in the private data repository.

    Returns identifiers only, never the original paper text or credentials.
    """
    return service().list_articles(limit)

@mcp.tool()
def inspect_legacy_article(article_id: str) -> dict:
    """Read-only source and historic receipt inspection for an existing article.

    Requires BRIDGE_LEGACY_PREFIX. Does NOT migrate, overwrite, republish,
    retry ambiguous imports or expose legacy full manuscript content.
    """
    prefix = os.getenv("BRIDGE_LEGACY_PREFIX")
    if not prefix:
        raise BridgeError("BRIDGE_LEGACY_PREFIX is not configured")
    return LegacyReader(service().storage, prefix).inspect(article_id)


@mcp.prompt()
def manuscript_handoff_checklist() -> str:
    """Source-fidelity checklist to prepare an author-approved MCP handoff."""
    return (
        "Before calling submit_manuscript or publish_this_chat: obtain the complete "
        "final article actually present in this conversation; retain each paragraph, "
        "math expression, link, caption and verified Figure source. Ask for explicit "
        "approval of THIS immutable article ID and one allowlisted logical destination. "
        "Never replace the manuscript with a shorter AI summary. After handoff, "
        "inspect the source hashes and exact status: an approved job is NOT a "
        "published remote document in public v0.1."
    )


@mcp.prompt()
def publication_reconciliation_checklist() -> str:
    """Safe recovery plan when remote publication seems to be stalled."""
    return (
        "Call get_publication_status and reconcile_publication for the existing "
        "article_id. Verify actual SHA256 and Git Blob SHA; inspect existing "
        "attempt, receipt, layout and message-ID evidence. An unknown/timeout "
        "remote upload outcome must NOT be retried blindly or moved to a new "
        "article ID. Preserve the original and repair the same remote document "
        "only when a real integrated worker can prove its identity."
    )


class BearerAuth:
    """Minimal ASGI bearer gate for HTTP scopes; lifespan passes through."""

    def __init__(self, downstream, secret: str):
        if not secret or len(secret) < 24:
            raise BridgeError("BRIDGE_MCP_TOKEN must contain at least 24 characters")
        self.downstream, self.secret = downstream, secret

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            await self.downstream(scope, receive, send)
            return
        if scope["type"] != "http":
            raise BridgeError("Only authenticated HTTP MCP transport is supported")
        supplied = dict(scope.get("headers", [])).get(b"authorization", b"").decode("latin-1")
        if not hmac.compare_digest(supplied, "Bearer " + self.secret):
            payload = b"Unauthorized"
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"text/plain"),
                                    (b"content-length", str(len(payload)).encode())]})
            await send({"type": "http.response.body", "body": payload})
            return
        await self.downstream(scope, receive, send)


def make_http_app():
    return BearerAuth(mcp.streamable_http_app(), os.getenv("BRIDGE_MCP_TOKEN", ""))


app = None if os.getenv("BRIDGE_TRANSPORT", "http") == "stdio" else make_http_app()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
