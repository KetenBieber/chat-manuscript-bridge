# Product roadmap & release status

This is a public general-purpose **MCP source handoff layer**, developed separately from a pre-existing private knowledge-publishing integration. Features are marked as implemented only when present in this repository; private production success cannot be counted as public-package feature completeness.

## Capability matrix

| Capability | Public v0.1.0 | Next acceptance requirement |
| --- | --- | --- |
| Local stdio MCP | **Implemented** | End-to-end test in supported clients |
| Streamable HTTP + static Bearer gate | **Implemented** | TLS / proxy deployment and auth review |
| Immutable private GitHub Markdown + SHA256 + Git Blob SHA | **Implemented** | Additional failure and concurrency tests |
| Figure source URL map | **Implemented (metadata)** | SSRF-safe download + binary SHA verification |
| User confirmation & allowlisted destinations | **Implemented** | Broader client interoperability tests |
| Source-bound status + read-only reconciliation | **Implemented** | Independent remote receipt attestation |
| Optional read-only private legacy inspection | **Implemented** | Migration plan with no overwrites |
| Real Feishu DOCX import, native math, images and layout repair | **Not shipped** | Dedicated provider + tests against actual documents |
| Real Feishu message notification | **Not shipped** | Message-ID receipt after full online audit |
| OAuth 2.1 for direct ChatGPT custom MCP registration | **Not shipped** | Compliant IdP, PKCE, token lifecycle and scope checks |
| Public multi-tenant hosting | **Not shipped** | Tenant isolation, abuse controls, quotas, audit logging |
| Interactive web dashboard / MCP App UI | **Not shipped** | Real data-bound app, accessibility, security and browser tests |

## Milestones

### 1. Foundation — source contract (current)

One clear source of truth, private GitHub storage, immutable IDs, two independent content hashes, explicit per-article consent, and safe state/legacy inspection. The MCP server does not invent worker outcomes or remote URLs.

### 2. Provider interface and deterministic delivery (planned)

Create a provider abstraction for destinations (starting with Feishu) and binary assets. Explicitly separate:

1. Authoritative source bytes and Figure references.
2. Worker attempt and at-most-once remote import claim.
3. Remote API receipt for the same source fingerprint.
4. Same-document layout verification of headings, prose, links, images, tables and equations.
5. IM notification after full layout verification, with an independent message-ID receipt.

Retain existing private production IDs/claims unchanged during migration; no history rewrite or duplicate import.

### 3. Client experience (planned)

Platform-specific connection recipes, sample MCP prompts/resources, developer diagnostics, and an optional real UI showing jobs, approval state, hashes, remote document link and per-stage reconciliation. **No UI should simulate publication success with fabricated data.**

### 4. Interoperability & release quality (planned)

Test matrices for Python 3.12/3.13, stdio/HTTP clients, typed tool inputs, private GitHub rate limits, authenticated remote hosting, idempotent retries, and a staging Feishu workspace. Publish a tagged release only when tests and documentation describe the same capabilities.

## Definition of done for the Feishu provider

- Complete original Markdown preserved, no LLM rewriting.
- Actual Figure bytes archived from verified paper/author source with safe host/redirect handling.
- True user consent and destination approval.
- Remote import recorded exactly once; ambiguous outcomes never retried blindly.
- Existing document repaired in place; math, images, paragraphs, tables and headings audited.
- Only after online audit: independent Feishu IM receipt with message ID.
- Regression suite, staged deployment, then carefully controlled production cutover.

Feature proposals and synthetic test cases are welcome. See [Contributing](../CONTRIBUTING.md).
