# Direct ChatGPT MCP connection

A GitHub repository, Railway deployment, installed skill, and ChatGPT MCP connection are distinct resources. The MCP endpoint must be **registered and authenticated** in the ChatGPT client before its methods appear as callable tools.

## Transport and authentication

- Use Streamable HTTP at `https://YOUR-DOMAIN/mcp`.
- The production service currently requires `Authorization: Bearer <PRIVATE_TOKEN>`. An anonymous request returns HTTP 401 by design.
- A portable plugin can declare its remote URL in `mcp.json` with `type: streamable-http`, plus `extensions.com.openai.auth: {"type":"api_key","headerScheme":"bearer"}`. Credentials **must be supplied separately** via the client's connection UI; no token belongs in this repository or the plugin archive.
- Some ChatGPT custom MCP registration forms support OAuth or no-auth only, and do not accept a fixed API key. In those clients, **do not choose no-auth** or remove the server's gate. Use a properly implemented OAuth 2.1 authorization provider, or a client connection flow that supports the API-key manifest.
- Installing/updating a personal plugin and authorizing the connection are user actions that cannot be completed by committing source code.

## Direct invocation acceptance test

1. Verify anonymous `GET /mcp` returns HTTP 401.
2. Connect the remote MCP server in ChatGPT with appropriate authentication.
3. Refresh the tool list and check for `inspect_configuration`, `publish_this_chat`, and `get_publication_status`.
4. Invoke read-only `inspect_configuration` through the **actual direct MCP tool**, not a GitHub or Railway proxy.
5. Submit a synthetic completed source to `publish_this_chat` with `confirm=true`, then query the same article ID. The returned job is **not** a Feishu publication receipt.
6. Check source-bound GitHub/Feishu API, online layout and notification receipts independently.

## Diagnosis

A `401` means authentication is absent or rejected; it can prove endpoint reachability but **not** functional tool connection. An unavailable callable name in ChatGPT means the app/tool connection is not actually installed, bound or refreshed. A plugin SKILL can describe the tool but cannot create a server connection or make a private credential available to the model.
