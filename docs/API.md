# MCP API v0.1

The endpoint is /mcp over authenticated Streamable HTTP, or the local stdio transport.

| Tool | Inputs | Result |
| --- | --- | --- |
| inspect_configuration | none | Readiness without exposing secrets |
| submit_manuscript | article_id, markdown, category, optional image_sources | Source stored with computed SHA256 and Git Blob SHA |
| approve_publication | article_id, destination, confirm=false | Preview without confirmation; otherwise immutable consent |
| publish_this_chat | article_id, markdown, category, destination, confirm=false, optional image_sources | Source + approval; DOES NOT launch a Feishu worker in v0.1 |
| get_publication_status | article_id | Current source-bound state and any real receipts |
| reconcile_publication | article_id | Read-only recovery instructions; safe_to_repeat_upload=false |
| list_manuscripts | limit from 1 to 200 | Private repository article IDs |
| inspect_legacy_article | article_id (requires BRIDGE_LEGACY_PREFIX) | Read-only validation of old Git Blob SHA and source-bound Feishu receipt/layout state; no mutation |

## Status guarantees

- saved: source is present, byte-for-byte and hash validated.
- approved_for_delivery: user confirmed this exact source and allowlisted logical destination. No upload claim.
- upload_outcome_unknown: an attempt record exists without reliable document receipt, upload blocked.
- published_api_verified: a source-matched worker receipt states a real remote API publication.
- layout_verified: a separate, matching online layout audit exists.
- notification_status=sent: a real source-matched message ID exists, with layout already verified.

The v0.1 MCP server does not write remote Feishu receipts, layout verification or notification records. Those statuses require a separately integrated delivery worker. Existing private production records are NOT automatically compatible with these paths.

## Storage contract

All paths are relative to the configured private data repository prefix:

~~~text
originals/<article_id>.md
jobs/<article_id>.json
approvals/<article_id>.json
attempts/<article_id>.json       worker-only
receipts/<article_id>.json       worker-only
layout/<article_id>.json         worker-only
notifications/<article_id>.json  worker-only
~~~

Article IDs use ASCII alphanumerics, underscore and hyphen, maximum 80 characters. Body size limit is 1 MiB UTF-8. Figure source map keys must start with async:, async-ref: or async-src:, and values must be absolute HTTPS URLs. They are not fetched by the current MCP service.
