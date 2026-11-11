# Security policy

The v0.1 package is for **single-tenant self-hosting**, not a managed multi-user SaaS.

Use a private GitHub repository for manuscript data; grant the service only minimal contents read/write permissions on that repository. Keep all tokens, Feishu recipient IDs, destination folder tokens and private documents out of this Public code repository. Never commit a real .env file.

For HTTP, require a strong BRIDGE_MCP_TOKEN, an exact BRIDGE_ALLOWED_HOST, and HTTPS in front of the service. The HTTP ASGI gate rejects missing/incorrect bearer headers. Stdio mode inherits local process permissions.

The destination allowlist must be explicitly configured. A chat request cannot approve an arbitrary destination; an approved request by itself is not a live Feishu upload.

The preliminary source URL check is not enough for secure network fetches. Future Figure-download workers must perform their own DNS/IP/redirect SSRF protection and verify downloaded content hashes.

Do not retry remote uploads merely because the client timed out. Check the remote import result and existing document first; a duplicate Feishu document is a correctness failure.

**Known limitations:** v0.1 lacks actual Feishu import, native math repair, a delivery worker, real-time background queue, tenant separation and independent external receipt attestation. Do not use the new package as a replacement for an existing production publisher until these are implemented and tested.

Please report security issues privately using GitHub private vulnerability reporting if enabled; do not post token values or real article bodies in public issues.
