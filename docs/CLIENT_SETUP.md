# MCP clients and transports

Chat Manuscript Bridge uses the **Model Context Protocol (MCP)**. Installing the Python package only starts a server; tools appear in a chat application **after that client has registered and connected the transport**.

## Transport compatibility

| Client capability | Public v0.1 | Setup |
| --- | --- | --- |
| Local **stdio** MCP | Supported | Recommended for local single-user development |
| Remote **Streamable HTTP** with static Bearer | Supported by server | Deploy behind TLS and authenticate with `BRIDGE_MCP_TOKEN` |
| ChatGPT custom MCP **OAuth** connection | **Not provided** | Requires a separately implemented OAuth provider; static Bearer is not an OAuth login |
| Running a skill with no MCP connection | **Not sufficient** | A skill can describe tools; it cannot install or authenticate them |
| Using GitHub + Railway app as a separate handoff | External integration | Not part of this public server or its installation instructions |

### Option A: local stdio

First complete the [Quickstart](QUICKSTART.md). Then register the following **illustrative** settings in the MCP-capable client of your choice. The config location/schema varies by product; consult your client's current documentation.

```json
{
  "mcpServers": {
    "chat-manuscript-bridge": {
      "command": "/absolute/path/chat-manuscript-bridge/.venv/bin/python",
      "args": ["-m", "chat_manuscript_bridge"],
      "env": {
        "BRIDGE_TRANSPORT": "stdio",
        "BRIDGE_GITHUB_REPO": "your-account/your-private-manuscripts",
        "BRIDGE_GITHUB_BRANCH": "main",
        "BRIDGE_GITHUB_TOKEN": "<use-the-client-secret-store-if-available>",
        "BRIDGE_STORAGE_PREFIX": "manuscripts/v1",
        "BRIDGE_ALLOWED_DESTINATIONS": "personal-knowledge-base"
      }
    }
  }
}
```

For Windows, use the absolute `...\\chat-manuscript-bridge\\.venv\\Scripts\\python.exe` path. If the client doesn't support encrypted environment-variable storage, supply the credential through a trusted operating-system process manager instead of committing the configuration.

**First check:** call `inspect_configuration`. Next submit a clearly synthetic manuscript, query its status and confirm `saved`. Avoid testing with personal papers.

### Option B: authenticated Streamable HTTP

Run behind an HTTPS ingress. You need:

- `BRIDGE_TRANSPORT=http`
- `BRIDGE_MCP_TOKEN` (a strong random secret of **at least 24 characters**)
- `BRIDGE_ALLOWED_HOST` set to the exact publicly requested hostname
- `BRIDGE_GITHUB_REPO`, `BRIDGE_GITHUB_TOKEN`, and `BRIDGE_ALLOWED_DESTINATIONS` as above

The server endpoint is `https://YOUR-HOST/mcp` behind a TLS reverse proxy. It rejects missing or incorrect `Authorization: Bearer ...`; localhost upstream should remain unexposed. Remote hostname/Origin restrictions and proper ingress configuration remain operator responsibilities.

> **Do not use no-auth** to work around a client that cannot supply Bearer authentication. Remote MCP discovery is not proof that an end-to-end tool call has been authorized.

### ChatGPT specifics

A GitHub repository, a ChatGPT plugin/skill package and a connected custom MCP server are separate objects. The public server has **static Bearer authentication**, not a user-facing OAuth 2.1 authorization-code flow. Some ChatGPT custom MCP registration UIs accept OAuth/no-auth rather than arbitrary API-key forms. In those clients this public v0.1 server cannot be registered directly until the operator builds a secure OAuth integration (including client identity, authorization, PKCE, scope/audience enforcement, token lifecycle and revocation). **Do not put the Bearer secret in chat, a public manifest or a URL.**

An alternate **GitHub App → private worker** handoff is possible in a separate system, but it does not grant this public v0.1 package a Feishu worker.

## Common connection failures

| What you see | Meaning | Safe response |
| --- | --- | --- |
| No MCP tools in the client | Process not started or remote connection not registered | Verify transport configuration; inspect actual tool listing |
| 401 on `/mcp` | Missing/invalid Bearer token | Check a secure credential store; never post tokens |
| Host / Origin denied | Security settings do not match public hostname | Align `BRIDGE_ALLOWED_HOST`, proxy and Origin; don't disable protections |
| Tool runs but `github_configured=false` | Missing GitHub repo/token env vars | Fix server environment |
| GitHub 403 | Incorrect permissions, token expiry or GitHub rate limit | Inspect GitHub authorization and API limits privately |
| Status stays `approved_for_delivery` | Expected if there is no delivery worker | Do not report a published document |
| `upload_outcome_unknown` | Remote attempt may have taken effect | Read-only `reconcile_publication`; **never blind retry** |

See [Security](../SECURITY.md), [Tool catalog](TOOL_CATALOG.md) and [API](API.md).
