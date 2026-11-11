# Feishu IM notifications

This public MCP package can send a **real Feishu IM message** after an external publishing worker has uploaded a document and verified its layout. The package **does not** import Feishu documents itself.

## Configure privately

The server needs four environment variables, set in a trusted secret manager or the MCP client's private configuration (never commit actual values):

~~~dotenv
FEISHU_APP_ID=your-app-id
FEISHU_APP_SECRET=your-app-secret
FEISHU_NOTIFY_RECEIVE_ID_TYPE=open_id
FEISHU_NOTIFY_RECEIVE_ID=your-app-scoped-open-id
~~~

Supported receiver types: open_id, user_id, union_id, chat_id, email. The Feishu app needs permission to send messages to the recipient. For chat_id, the bot must be able to access the group chat.

## Evidence that must exist before notifying

A separately integrated delivery worker must create **real**, source-bound publication and online-layout receipts in the private data repository:

~~~text
BRIDGE_STORAGE_PREFIX/
  originals/<article_id>.md
  jobs/<article_id>.json
  approvals/<article_id>.json
  receipts/<article_id>.json
  layout/<article_id>.json
~~~

The last two records need schema_version=1, a matching article_id and original source_sha256, identical genuine Feishu document_url values, published=true in the publication receipt, and layout_verified=true in the online layout audit.

Writing a fake record is not a substitute for actual API verification. The public MCP does not manufacture the receipt or claim the online document was checked.

## Sending one verified notification

1. Call **get_publication_status** and confirm that status is layout_verified and the document_url is correct.
2. Call **send_feishu_notification** with article_id and confirm=false to preview without sending.
3. Call **send_feishu_notification** with article_id and confirm=true only for the intended recipient.
4. Call **get_notification_status** for the actual result. The tool records Feishu's returned message_id, source SHA and URL on success.

The real Feishu message is plain text with the article ID and verified document link. It does not summarize or rewrite the article.

## Idempotency and recovery

The server writes a persistent, source-bound **notification-attempts** claim before making an external API call.

- sent: GitHub contains a matching successful notification receipt with the Feishu message ID. Repeat calls return the existing result.
- not_sent: there is no attempt and no successful receipt.
- outcome_unknown: an attempt exists without a successful receipt. **Do not resend automatically.** A timeout may have occurred after Feishu accepted the message. Inspect Feishu IM history/audit data and reconcile the existing send manually.

This provides at-most-once automatic sending, not a mathematical exactly-once guarantee. A successful IM API response does not prove the recipient has read the message.

The public Feishu **IM** notification adapter is independent of Feishu **document import**, which still requires an external Worker and a compatible receipt schema. The author's private production project may have its own schema and is not automatically migrated by this tool.

See [Tool catalog](TOOL_CATALOG.md), [API](API.md) and [Security](../SECURITY.md).
