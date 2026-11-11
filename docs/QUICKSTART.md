# Quickstart / 快速入门

Get a locally running, source-faithful MCP handoff server. This guide exercises the **public v0.3 core interface** only; it does not publish a Feishu document.

## 1. Prerequisites

- **Python 3.12 or 3.13**, Git, and an MCP-capable client.
- A GitHub **private data repository** that you control. Do not point the bridge at this public source repository.
- A GitHub **fine-grained personal access token** with **Contents: read/write** for only that data repository. The service creates files and reads them back by Git Blob SHA.
- A user-chosen logical destination string, such as `personal-knowledge-base`. In public v0.1 this is an approval allowlist—not a Feishu folder ID.

You may use `uv` or a standard Python venv. No global Python environment modification is necessary.

## 2. Install

**macOS / Linux**

```bash
git clone https://github.com/KetenBieber/chat-manuscript-bridge.git
cd chat-manuscript-bridge
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest -q
```

**Windows PowerShell**

```powershell
git clone https://github.com/KetenBieber/chat-manuscript-bridge.git
cd chat-manuscript-bridge
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
```

You can also use `uv venv --python 3.12` and `uv pip install -e ".[test]"` after creating a local environment.

## 3. Configure the private storage

The service deliberately **does not automatically load** `.env`. Put the following values in your MCP client's private environment configuration, shell session, or a trusted secret manager. Never commit actual values.

```dotenv
BRIDGE_GITHUB_REPO=your-account/your-private-manuscripts
BRIDGE_GITHUB_BRANCH=main
BRIDGE_GITHUB_TOKEN=<your-fine-grained-token>
BRIDGE_STORAGE_PREFIX=manuscripts/v1
BRIDGE_ALLOWED_DESTINATIONS=personal-knowledge-base
BRIDGE_TRANSPORT=stdio
```

Use `.env.example` as a template only. The storage prefix and destination are **logical** identifiers, not personal URLs. This creates a new `manuscripts/v1/` folder inside the private data repository.

## 4. Connect your MCP client

For a stdio-capable client, use the Python executable from your environment and this command:

```json
{
  "mcpServers": {
    "chat-manuscript-bridge": {
      "command": "/absolute/path/to/chat-manuscript-bridge/.venv/bin/python",
      "args": ["-m", "chat_manuscript_bridge"],
      "env": {
        "BRIDGE_TRANSPORT": "stdio",
        "BRIDGE_GITHUB_REPO": "your-account/your-private-manuscripts",
        "BRIDGE_GITHUB_BRANCH": "main",
        "BRIDGE_GITHUB_TOKEN": "<stored-securely-by-your-client>",
        "BRIDGE_STORAGE_PREFIX": "manuscripts/v1",
        "BRIDGE_ALLOWED_DESTINATIONS": "personal-knowledge-base"
      }
    }
  }
}
```

Client configuration syntax and secret-storage capabilities vary. On Windows, replace the executable with the absolute path to `.venv\\Scripts\\python.exe`. Do not paste live tokens into public repositories or issue comments. See [Client setup](CLIENT_SETUP.md).

## 5. Verify the connection

Call `inspect_configuration` via your **real MCP client's tool interface**. It should report at least the following fields (the actual response also includes `capabilities` and `usage`):

```json
{
  "service": "chat-manuscript-bridge",
  "version": "0.3.0",
  "github_configured": true,
  "allowed_destinations_count": 1,
  "stage": "MCP handoff and durable job-status engine; external delivery worker required"
}
```

This is an **illustrative** response for a correctly configured local server. The stage text makes it explicit that no Feishu worker is bundled.

Then use `submit_manuscript` with **synthetic test text**, and `get_publication_status` to confirm `saved`. Approve only when you intend to authorize the chosen destination. See [Examples](EXAMPLES.md) and the [API contract](API.md).

## 6. HTTP deployment (optional)

If your MCP client supports static Bearer authentication and Streamable HTTP, you can expose the same tools through a TLS-terminating reverse proxy.

```bash
export BRIDGE_TRANSPORT=http
export BRIDGE_ALLOWED_HOST=your-mcp.example.com
export BRIDGE_MCP_TOKEN="<a-strong-random-secret-at-least-24-characters>"
uvicorn chat_manuscript_bridge.server:app --host 127.0.0.1 --port 8000
```

The endpoint is `/mcp`. Set your GitHub and destination variables as above. Keep the proxy's upstream private and use HTTPS. The included Dockerfile starts `uvicorn` on port 8000 for a container orchestrator.

**Important:** Static Bearer authentication in this server is *not* a ready-to-use ChatGPT OAuth integration. Some ChatGPT custom MCP connection flows require OAuth, and creating a plugin or skill will not automatically connect this endpoint. See [Client setup](CLIENT_SETUP.md).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| MCP client shows no tools | It may not have started the stdio command or authenticated the remote HTTP MCP |
| `inspect_configuration.github_configured=false` | Missing GitHub environment variables; a truthy check does not itself validate repository permissions |
| `Destination is not ... allowed` | Add the logical destination to `BRIDGE_ALLOWED_DESTINATIONS`; do not supply a Feishu folder URL |
| `Article ID already belongs to a different source` | Create a **new** article ID for a changed draft; immutable originals must not be overwritten |
| HTTP 401 | Bearer token absent/incorrect, or client does not support the configured auth |
| GitHub 403 | Token permissions, expiry or rate limits; inspect privately, do not paste token into a bug report |
| Job stays `approved_for_delivery` | Expected for public v0.1: no delivery worker is bundled |

For security implications and safe disclosure see [SECURITY.md](../SECURITY.md).


## Optional: Markdown to PDF/PNG posters

Install the poster extra and Pandoc + XeLaTeX, then call generate_document_poster on an existing .md path in your GitHub repository. This is separate from the external publication worker. The included Dockerfile.poster supplies the required PDF toolchain. See [Document posters](POSTERS.md).

## Optional verified Feishu IM notification

If your independent publishing worker has supplied **real**, source-bound document and layout receipts, configure the Feishu bot credentials and recipient privately. Preview with send_feishu_notification(confirm=false), then explicitly confirm one send. See [Feishu notifications](FEISHU_NOTIFICATIONS.md). This does not enable document upload.
