# MCP Tool catalog

Eight source-aware tools in public **v0.1.0**. Tool names are exact. They are exposed by a correctly connected MCP client, not automatically by GitHub, Railway, a skill file or this README.

## Source and authorization tools

### \`submit_manuscript\`

Persist an exact, non-empty UTF-8 Markdown original in your private GitHub data repository. The content is never rewritten or normalized.

| Input | Required | Meaning |
| --- | --- | --- |
| \`article_id: str\` | Yes | Immutable identifier: 1–80 ASCII letters, digits, underscores or hyphens |
| \`markdown: str\` | Yes | Complete original, at most 1 MiB UTF-8; no NUL bytes |
| \`category: str\` | Yes | Printable, non-empty category (max 80 characters) |
| \`image_sources: dict[str,str]\` | No | Mapping of \`async:\`, \`async-ref:\`, \`async-src:\` keys to HTTPS Figure URLs |

**Writes:** \`originals/<article_id>.md\`, \`jobs/<article_id>.json\` under \`BRIDGE_STORAGE_PREFIX\`. **Returns:** \`status=saved\`, actual SHA256 and Git Blob SHA, and whether the operation was idempotent.

A different text, category or Figure map with the same article ID is rejected. Image URLs are validated but **not downloaded** by public v0.1.

### \`approve_publication\`

Preview or confirm authorization for a **single existing source**, bound to its immutable hash and exactly one logical destination in your configured allowlist.

| Input | Required | Meaning |
| --- | --- | --- |
| \`article_id\` | Yes | An already saved source |
| \`destination\` | Yes | Allowlisted logical identifier, such as \`personal-knowledge-base\` |
| \`confirm: bool\` | No | Defaults to \`false\` and returns a preview; \`true\` writes authorization |

**Writes only on confirmation:** \`approvals/<article_id>.json\`. **Returns:** \`approved_for_delivery\`. That is **not** a remote publication.

### \`publish_this_chat\`

A convenience entry point combining \`submit_manuscript\` and \`approve_publication\` **after explicit user consent**.

Inputs: \`article_id, markdown, category, destination, confirm=false, image_sources=None\`.

- \`confirm=false\`: no manuscript write; returns \`requires_confirmation\`.
- \`confirm=true\`: validates destination, persists exact bytes, records a source-bound approval and returns the actual job state.
- \`delivery_worker_started=false\` in public v0.1. The tool does **not** send to Feishu and must never claim it did.

Do not reconstruct a user's long-form original from an inaccessible shared link; only send the final manuscript actually present to the authoring client.

## Read-only inspection and recovery

### \`get_publication_status(article_id)\`

Returns the verified stage, original fingerprint, optional real \`document_url\`, \`layout_verified\` and \`notification_status\`. No remote upload is started.

### \`reconcile_publication(article_id)\`

Explains a safe next action without mutating any remote document. The response includes \`upload_triggered=false\` and \`safe_to_repeat_upload=false\`. An ambiguous attempt is a **stop condition**, not permission to create a second remote document.

### \`list_manuscripts(limit=50)\`

Lists up to 200 article IDs from the configured private store; never returns original article bodies.

### \`inspect_configuration()\`

Returns a non-secret stage/readiness overview. It does not reveal GitHub tokens, logical destination values or private manuscript content.

### \`inspect_legacy_article(article_id)\`

Read-only inspection of a previous private storage layout, available only with explicit \`BRIDGE_LEGACY_PREFIX\`. It cannot migrate, overwrite, or re-publish historical documents.

## Evidence states

\`\`\`mermaid
stateDiagram-v2
    [*] --> saved
    saved --> approved_for_delivery: confirm=true + allowlist
    approved_for_delivery --> upload_outcome_unknown: external worker creates attempt
    upload_outcome_unknown --> published_api_verified: real matching API receipt
    published_api_verified --> layout_verified: exact-source online audit
    note right of approved_for_delivery
      Public v0.1 stops here.
      Worker integration is external.
    end note
\`\`\`

| Status | Evidence | Does it prove the destination is ready? |
| --- | --- | --- |
| \`saved\` | Immutable GitHub source and SHA fingerprints | No |
| \`approved_for_delivery\` | Explicit, source-bound consent | No |
| \`upload_outcome_unknown\` | Worker attempt without definitive outcome | **No; do not repeat upload** |
| \`published_api_verified\` | Matching real remote publication receipt | API yes, layout not yet |
| \`layout_verified\` | Matching real online layout audit | Yes, subject to audit scope |
| \`notification_status=sent\` | Matching real IM \`message_id\` after layout verification | Message API accepted; does not prove recipient read it |

**No fabricated evidence.** Public v0.1 does not write attempt, receipt, layout, or notification files. Integrations must implement and verify those records independently.

See [API.md](API.md) for exact storage paths and [Examples.md](EXAMPLES.md) for sample calls.
