# Chat Manuscript Bridge

**Your chat is where the writing happens. GitHub keeps the original. Your publishing pipeline takes it from there.**

An open-source [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for preserving completed Markdown manuscripts, safely handing them to publishing workers, exporting PDF/image posters, and sending evidence-gated Feishu notifications.

[简体中文](README.zh-CN.md) · [Quickstart](docs/QUICKSTART.md) · [MCP tool catalog](docs/TOOL_CATALOG.md) · [Feishu notifications](docs/FEISHU_NOTIFICATIONS.md) · [Examples](docs/EXAMPLES.md)

## Why it exists

A useful article often begins inside an AI conversation. Copying it between tools can lose paragraphs, equations, figures or provenance. Chat Manuscript Bridge preserves the **exact approved Markdown** and gives every delivery a verifiable source fingerprint.

~~~text
ChatGPT or another MCP client (final manuscript)
                         |
                         v
             GitHub immutable original
                SHA-256 + Git Blob SHA
                         |
          +--------------+----------------+
          |              |                |
          v              v                v
    Publishing      PDF / PNG       Status & repair
    handoff job     poster export    without blind retries
          |
          v
  External publishing worker
  (e.g. Feishu document import)
          |
          v
 Verified receipt + layout audit
          |
          v
 Optional Feishu IM notification
 (source-bound and once-only)
~~~

## What works today

| Capability | Included in this repository? |
| --- | --- |
| Save original Markdown in a **separate private GitHub repository** | **Yes** |
| Immutable source SHA-256 / Git Blob SHA verification | **Yes** |
| Approve a specific article for an allowlisted destination | **Yes** |
| Read publication state and reconcile uncertain uploads | **Yes** |
| Generate PDF, page PNGs and optional long poster, then store in GitHub | **Yes**, with optional renderer dependencies |
| Send one Feishu IM alert after **externally verified** publication and layout | **Yes**, optional Feishu notification adapter |
| Upload / format the actual Feishu document | **No** — connect an external delivery worker |
| Built-in ChatGPT OAuth 2.1 server | **No** |

The notification tool sends a real Feishu IM message and stores its returned message ID. It **will not** send for queued, merely approved or unverified publications. If an API result is ambiguous, it blocks automatic resend.

## Install (Python 3.12+)

~~~bash
git clone https://github.com/KetenBieber/chat-manuscript-bridge.git
cd chat-manuscript-bridge
python -m pip install -e ".[test]"
python -m pytest -q
~~~

For local stdio MCP:

~~~bash
python -m chat_manuscript_bridge
~~~

Configure your **private manuscript repository** and a fine-grained GitHub token in your MCP client's secret environment. See [Quickstart](docs/QUICKSTART.md) and [Client setup](docs/CLIENT_SETUP.md) for Windows, macOS/Linux and authenticated HTTP examples.

For document posters:

~~~bash
python -m pip install -e ".[poster]"
~~~

Pandoc, XeLaTeX and an installed CJK font are also required. [Poster guide](docs/POSTERS.md).

## Three practical workflows

1. **Save from chat.** Call submit_manuscript or publish_this_chat with the complete final Markdown. Same ID + same bytes is safe to retry; changed content needs a new ID.
2. **Publish through your worker.** Approve one source and destination. An external worker writes authentic Feishu import, layout and delivery records. get_publication_status distinguishes approved, published and verified.
3. **Make it shareable.** Generate PDF/page PNG/long poster from an existing Markdown source. If the external worker has verified the Feishu document layout, send_feishu_notification can send a one-time message to your configured Feishu user or chat.

The MCP tools never author, summarize or rewrite your manuscript. The original is immutable.

**Notification safety:** FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_NOTIFY_RECEIVE_ID_TYPE and FEISHU_NOTIFY_RECEIVE_ID must be configured privately. The send tool defaults to a preview. Confirmed sends are source-bound; each article is claimed before calling Feishu to avoid duplicate delivery. [Integration and recovery guide](docs/FEISHU_NOTIFICATIONS.md).

## Build on it

This is a reusable **handoff core**, not a full Feishu publisher. You can connect your own worker for Notion, Feishu, a CMS, a blog or a document knowledge base, provided it returns trustworthy source-bound receipts. [Architecture](docs/ARCHITECTURE.md) · [API contract](docs/API.md) · [Roadmap](docs/ROADMAP.md)

**Contributions welcome:** client-setup examples, publication adapters, formatting tests, documentation improvements and reproducible bug reports. [Contributing](CONTRIBUTING.md) · [Issue tracker](https://github.com/KetenBieber/chat-manuscript-bridge/issues) · [Security](SECURITY.md) · MIT License

**Keywords:** MCP, ChatGPT, Markdown publishing, GitHub archival, Feishu/Lark, research notes, PDF posters, AI writing workflow.
