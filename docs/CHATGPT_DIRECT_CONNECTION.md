# Direct ChatGPT connection and auth boundaries

This document covers the **public Chat Manuscript Bridge v0.1.0** package, not any private Railway production service.

GitHub repositories, Agent Skills, MCP packages and ChatGPT client connections are distinct. Installing a skill or updating `mcp.json` does not create an authorized ChatGPT MCP connection.

## Available transports

- **Local stdio:** use any client that registers a local MCP process; this is the preferred public v0.1 setup.
- **Streamable HTTP:** self-host `https://YOUR-DOMAIN/mcp`, protected by a static Bearer token, exact host constraints and operator-managed TLS.
- **ChatGPT custom MCP authorization:** this public v0.1 package does **not** implement OAuth 2.1. Some ChatGPT setup forms support OAuth/no-auth rather than arbitrary static API keys. Do not choose no-auth or expose a live secret to bypass this incompatibility.

A static `BRIDGE_MCP_TOKEN` should be supplied through a safe secret channel to a compatible client. Never paste it in chat, a public issue, a manifest or URL.

For direct ChatGPT custom-MCP use where OAuth is mandatory, an operator first needs a secure OAuth authorization provider with proper PKCE, resource metadata, scoped/audience-validated credentials and token lifecycle. That layer is currently **not part of this release**.

## Honest acceptance test

1. Connect through a client that supports your selected transport and authentication.
2. Confirm that the client really exposes `inspect_configuration`, `publish_this_chat` and `get_publication_status`; a GitHub app connection alone is not that proof.
3. Call `inspect_configuration` and confirm `capabilities.feishu_import_worker_included=false` for public v0.1.
4. Submit synthetic text and verify immutable source hash readback.
5. Approve a single logical destination, query the job and expect `approved_for_delivery`—not a Feishu document.
6. Use read-only `reconcile_publication` for ambiguous external attempts. Never retry blindly.

See [Client setup](CLIENT_SETUP.md), [Quickstart](QUICKSTART.md) and [Roadmap](ROADMAP.md).
