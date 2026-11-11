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
    """Non-secret readiness view; no credentials, destination tokens or Open IDs."""
    return {
        "service": "chat-manuscript-bridge",
        "version": "0.1.0",
        "github_configured": bool(os.getenv("BRIDGE_GITHUB_REPO") and os.getenv("BRIDGE_GITHUB_TOKEN")),
        "allowed_destinations_count": len(tuple(filter(
            None, (x.strip() for x in os.getenv("BRIDGE_ALLOWED_DESTINATIONS", "").split(","))
        ))),
        "stage": "MCP handoff and durable job-status engine; external delivery worker required",
    }


@mcp.tool()
def submit_manuscript(article_id: str, markdown: str, category: str,
                      image_sources: dict[str, str] | None = None) -> dict:
    """Persist exact UTF-8 original in a private GitHub store; never publishes by itself."""
    return service().submit(article_id, markdown, category, image_sources)


@mcp.tool()
def approve_publication(article_id: str, destination: str, confirm: bool = False) -> dict:
    """Approve one SHA-bound article to one allowlisted logical destination."""
    return service().approve(article_id, destination, confirm)


@mcp.tool()
def publish_this_chat(article_id: str, markdown: str, category: str,
                      destination: str, confirm: bool = False,
                      image_sources: dict[str, str] | None = None) -> dict:
    """One chat call to save + authorize delivery, returning status not a fake URL.

    Requires explicit single-article consent. No separate ChatGPT session or
    autonomous AI author is invoked. The delivery worker is independent.
    """
    if not confirm:
        return {"article_id": article_id, "requires_confirmation": True,
                "category": category, "destination": destination}
    svc = service()
    source = svc.submit(article_id, markdown, category, image_sources)
    approval = svc.approve(article_id, destination, confirm=True)
    return {"article_id": article_id, "source": source,
            "approval": approval, "publication": svc.status(article_id),
            "delivery_worker_started": False}


@mcp.tool()
def get_publication_status(article_id: str) -> dict:
    """Read the durable state and real source-bound receipt when one exists."""
    return service().status(article_id)


@mcp.tool()
def reconcile_publication(article_id: str) -> dict:
    """Read-only failure recovery advice; never repeats an ambiguous Feishu upload."""
    return service().reconcile(article_id)


@mcp.tool()
def list_manuscripts(limit: int = 50) -> dict:
    """List immutable manuscript IDs in the configured private GitHub repository."""
    return service().list_articles(limit)


class BearerAuth:
    """Minimal ASGI bearer gate for HTTP scopes; lifespan passes through."""

    def __init__(self, downstream, secret: str):
        if not secret or len(secret) < 24:
            raise BridgeError("BRIDGE_MCP_TOKEN must contain at least 24 characters")
        self.downstream, self.secret = downstream, secret

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.downstream(scope, receive, send)
            return
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
