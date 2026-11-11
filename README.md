# Chat Manuscript Bridge

**Preserve the original. Deliver with evidence.**

A self-hosted Model Context Protocol (MCP) server for handing off finished manuscripts from AI conversations without rewriting the article. Each original is stored byte-for-byte with source SHA256 and Git Blob SHA, explicit per-article authorization and a durable, inspectable job status.

**Current stage: v0.1 development.** This public repository implements direct authenticated MCP handoff, immutable GitHub storage, approval and status/recovery logic. It **does not yet ship the Feishu DOCX import/layout/notification worker**. An approved request is not a published document. The pre-existing private Railway worker has not been migrated or modified.

[中文说明](README.zh-CN.md) | [Architecture](docs/ARCHITECTURE.md) | [API](docs/API.md) | [Security](SECURITY.md)

## Capabilities

| Area | Status |
| --- | --- |
| MCP Streamable HTTP / local stdio tools | Implemented |
| Private GitHub immutable UTF-8 original + hash verification | Implemented |
| Figure source URL mapping, stored with original source record | Implemented |
| Explicit single-article approval, destination allowlist | Implemented |
| Durable statuses, safe inspection of ambiguous upload | Implemented |
| Feishu upload, native equations and layout recovery worker | Next integration |
| Real Feishu IM notification and production data migration | Not yet integrated |

The software source is public; your manuscript repository stays private. The bridge is not an LLM writer and does not alter the content.

## Install

Requires Python 3.12+:

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest -q
~~~

Set the environment variables from [.env.example](.env.example). The process does not auto-load .env: export them using your shell or your hosting platform's secret manager.

~~~text
BRIDGE_GITHUB_REPO=your-account/your-private-data-repo
BRIDGE_GITHUB_TOKEN=your-fine-grained-token
BRIDGE_GITHUB_BRANCH=main
BRIDGE_STORAGE_PREFIX=manuscripts/v1
BRIDGE_ALLOWED_DESTINATIONS=personal-knowledge-base
~~~

The token needs access only to the private data repository. A missing destination allowlist **denies all publication approvals**.

### Local stdio

~~~bash
python -m chat_manuscript_bridge
~~~

### Authenticated HTTP

~~~bash
export BRIDGE_TRANSPORT=http
export BRIDGE_ALLOWED_HOST=localhost
export BRIDGE_MCP_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn chat_manuscript_bridge.server:app --host 127.0.0.1 --port 8000
~~~

MCP endpoint: **/mcp**. For an external deployment provide TLS at the ingress, configure the exact host and never expose an unauthenticated HTTP service. The included Dockerfile supports container-based deployment.

## ChatGPT usage

Deploy the service first, then explicitly connect its real MCP endpoint in a compatible ChatGPT client. **Creating a GitHub repository or installing a skill does not automatically expose these MCP tools in ChatGPT.**

The publish_this_chat tool accepts the final manuscript *actually available in the same conversation*, article_id, category, logical destination and confirm=true after the user has authorized that one article. It saves the original and its approval in GitHub; the returned result is a **source-bound job**, not a Feishu success claim.

Use get_publication_status to inspect verified status; reconcile_publication makes no writes and never blindly repeats an uncertain upload. Optional inspect_legacy_article reads older records **without writing to or republishing from** the old private store; configure BRIDGE_LEGACY_PREFIX explicitly before using it.

## Safety and extensibility

This code repository contains no user research, personal Feishu identifiers, passwords, real paper screenshots or production receipts. The source is deliberately separated from any private data repository. The future Feishu worker must preserve exact source hashes, audit each real document's math/figures/text and only send notifications after full layout verification.

See [Architecture](docs/ARCHITECTURE.md) for the migration boundary and release stages. MIT licensed.
