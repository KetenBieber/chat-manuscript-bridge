# Worked examples

The following walkthrough uses **invented manuscript data** and a private sample repository. Tool-call JSON is **illustrative**: clients send MCP calls through their own APIs, not by pasting raw JSON into an ordinary terminal.

## 1. Check non-secret configuration

```json
{"tool":"inspect_configuration","arguments":{}}
```

Example response (values shown for a configured sample server):

```json
{
  "service": "chat-manuscript-bridge",
  "version": "0.1.0",
  "github_configured": true,
  "allowed_destinations_count": 1,
  "stage": "MCP handoff and durable job-status engine; external delivery worker required"
}
```

## 2. Save the actual final original

```json
{
  "tool": "submit_manuscript",
  "arguments": {
    "article_id": "example_paper_001",
    "category": "robotics",
    "markdown": "# Example: Robot Policy\n\nA complete synthetic test manuscript.\n\nIts author controls the content."
  }
}
```

The server writes `originals/example_paper_001.md` and `jobs/example_paper_001.json` under `BRIDGE_STORAGE_PREFIX` **in your private data repository**.

The reply includes real, calculated `source_sha256` and `source_git_blob_sha`. Do not type a made-up SHA into an approval. The canonical source must be validated on subsequent reads.

Calling `submit_manuscript` again with identical bytes is idempotent; calling it with the same article ID and *different* text must fail. Use a new ID for a revised draft.

## 3. Preview and confirm the destination

Preview requires no approval write:

```json
{
  "tool": "approve_publication",
  "arguments": {
    "article_id": "example_paper_001",
    "destination": "personal-knowledge-base",
    "confirm": false
  }
}
```

After the actual user explicitly authorizes this article, confirm:

```json
{
  "tool": "approve_publication",
  "arguments": {
    "article_id": "example_paper_001",
    "destination": "personal-knowledge-base",
    "confirm": true
  }
}
```

This returns `status=approved_for_delivery`. **No Feishu API is called by public v0.1.** `personal-knowledge-base` is a logical allowlist label, not a real remote folder URL.

## 4. Query the truthful publication status

```json
{"tool":"get_publication_status","arguments":{"article_id":"example_paper_001"}}
```

Illustrative response *before a real delivery worker exists* (hash strings omitted here intentionally):

```json
{
  "article_id": "example_paper_001",
  "category": "robotics",
  "status": "approved_for_delivery",
  "destination": "personal-knowledge-base",
  "document_url": null,
  "layout_verified": false,
  "notification_status": "not_sent"
}
```

The actual response also carries the real `source_sha256` and `source_git_blob_sha`. A UI should render this as **approved / waiting for delivery**, not as a published document.

## 5. One-step handoff from a finished conversation

When an author has asked to publish the **entire finalized article**, a compatible MCP client can call:

```json
{
  "tool": "publish_this_chat",
  "arguments": {
    "article_id": "example_chat_final_001",
    "category": "robotics",
    "destination": "personal-knowledge-base",
    "confirm": true,
    "markdown": "# Example final article\n\nAll paragraphs from the actually available conversation."
  }
}
```

The result includes `source`, `approval`, `publication` objects and `delivery_worker_started=false` for public v0.1.

Do not send a paraphrase or generated replacement when the original is unavailable. Do not claim an upload succeeded because an MCP handoff returned HTTP 200.

## 6. Handle ambiguous uploads safely

```json
{"tool":"reconcile_publication","arguments":{"article_id":"example_paper_001"}}
```

The tool never repeats a remote upload. Its response explicitly includes:

```json
{"upload_triggered":false,"safe_to_repeat_upload":false}
```

With a real integrated worker, a source-matched remote receipt can prove `published_api_verified`; a separate layout record can prove `layout_verified`; a valid `message_id` can prove the notification API accepted the message. The public v0.1 tool does **not** manufacture those records.

## Figure-source mapping

If the final conversation contains an image marker such as `<AsyncImage query="paper Figure 2"/>`, pass a source-bound `image_sources` entry with a verified paper/author HTTPS image URL:

```json
{
  "image_sources": {
    "async:paper Figure 2": "https://example.org/official-figure-2.png"
  }
}
```

This is an **illustrative source-mapping URL**, not a verified real paper Figure. Public v0.1 validates source URL form and stores the mapping; actual image download and rendering require a separately implemented, SSRF-safe worker.

## Inspecting old private records

When `BRIDGE_LEGACY_PREFIX` is configured, `inspect_legacy_article` reads existing source and publication evidence only. It does not migrate, alter or re-publish a historical document.

See the [Tool catalog](TOOL_CATALOG.md) for exact inputs and [Architecture](ARCHITECTURE.md) for the protocol.
