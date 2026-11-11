# Release notes — source snapshot v0.3.0

**Status:** source code is available on the default branch. A formally tagged GitHub Release and a published PyPI distribution have **not** been issued by this documentation update.

## What changed

- Added an optional Feishu IM notification adapter. It requires independent, authentic source-bound Feishu publication and online-layout receipts before it can send.
- Added MCP tools `send_feishu_notification` and `get_notification_status` with preview-first consent.
- Added a durable claim before external message delivery. Ambiguous results remain blocked rather than causing duplicate automatic sends.
- Added notification-path unit tests: confirmation preview, successful real message-ID recording, repeat-call idempotency, uncertain send, invalid layout and non-Feishu URL.
- Reworked the English and Chinese README to show the actual manuscript-to-publication workflow, concrete use cases and limitations.
- Expanded tool catalog, API reference, setup instructions and optional notification configuration.
- Project metadata now reports version 0.3.0.

## Explicit limitations

- **Document import is not shipped here.** Publishing to Feishu or another platform needs a separately connected destination worker.
- **Feishu IM notification is included only after verified documents.** It is not a general-purpose message tool and it does not re-author the manuscript.
- **GitHub Action status is not accepted as proof of a passed test suite while hosted runners fail to execute.** Run `python -m pytest -q` and `python -m compileall -q src` locally until CI is restored.
- OAuth 2.1 / shared multi-tenant hosting is not bundled.
- There is no claim that this public core alone can reproduce the author's private end-to-end Feishu production pipeline.

See [Quickstart](QUICKSTART.md), [Feishu notifications](FEISHU_NOTIFICATIONS.md), and [Roadmap](ROADMAP.md).
