# Architecture and migration boundary

## v0.1 now

~~~text
ChatGPT / author supplies entire approved source
                   |
                   v
Authenticated MCP submit_manuscript / publish_this_chat
                   |
                   v
Private GitHub originals + SHA256 + real Git Blob SHA
                   |
                   v
Immutable source-bound jobs/<id>.json
                   |
                   v
Explicit allowlisted approvals/<id>.json
                   |
                   v
Await an external delivery worker (NOT yet in this public package)
                   |
                   v
Worker-only document attempts/receipts/layout records;
             optional MCP Feishu IM send claim + real message-ID receipt
                   |
                   v
MCP get_publication_status / reconcile_publication
~~~

The public source repository never stores private manuscripts or real Feishu receipts. Runtime options select the private repository, branch and storage prefix.

## Invariants

**Original is immutable.** A Unicode UTF-8 original is not trimmed, normalized, rewritten or summarized. The store verifies remote Git Blob SHA and source SHA256; any content drift blocks approval or status.

**Approval is specific.** One article hash, one category, one allowlisted logical destination, user confirmation required. Changing any field requires a new immutable ID.

**Remote upload is not approval.** A future worker must distinguish approved, upload uncertain, published by API, layout verified and notification sent. An ambiguous upload cannot be repeated without reconciling the existing remote document.

**Figures cannot be guessed.** Source mappings hold HTTPS references; future downloader must protect against DNS rebinding and SSRF when fetching actual image bytes.

## Worker record protocol (planned)

- originals/<id>.md: canonical Markdown bytes
- jobs/<id>.json: exact SHA256, Git Blob SHA, byte size, category and source URL map
- approvals/<id>.json: hash-bound user authorization
- attempts/<id>.json: actual worker remote-attempt record
- receipts/<id>.json: actual Feishu API receipt
- layout/<id>.json: actual same-document online structure audit
- notifications/<id>.json: actual message-id receipt

Only a genuine external publishing worker may create document upload attempts, publication receipts and layout audits. The optional MCP Feishu IM adapter can create a notification claim and message-ID receipt **after** the external evidence passes its source-bound checks. It does not import Feishu documents.

## Migration from the existing private project

The older production service stores its pipeline under different private path conventions, including a fixed historical directory prefix, derived artifacts and Feishu receipts. **Those schemas are incompatible with public v0.1 and have not been migrated.** The live Railway source and environment remain unchanged.

A read-only legacy original and publication-receipt inspector is now available through inspect_legacy_article; this is **not** an automatic migration or a new upload. Further work: the original full deterministic Feishu pipeline ported as provider modules; native display-math recovery in the *same* document; sandbox acceptance; canary cutover; only then production source switch. Preserve old source hashes and duplicate-upload prevention records throughout.

See [API](API.md) for current callable tools and [Security](../SECURITY.md) for deployment limitations.
