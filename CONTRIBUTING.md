# Contributing to Chat Manuscript Bridge

Thanks for improving a source-faithful MCP delivery protocol. The project accepts documentation fixes, schema and interoperability tests, bug reports, integrations and security improvements.

## Before you contribute

**Only use synthetic manuscript content.** Never commit or post private articles, real research notes, GitHub tokens, Feishu recipient IDs, production folder IDs, signed URLs, message IDs or other personal delivery evidence.

Check [Roadmap](docs/ROADMAP.md) and [Security](SECURITY.md) so proposals match the current **public v0.3 source** feature boundary.

## Local development

```bash
git clone https://github.com/KetenBieber/chat-manuscript-bridge.git
cd chat-manuscript-bridge
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
python -m compileall -q src
python -m pytest -q
```

Tests run **locally** (Python 3.12 or 3.13) or in a separate explicitly selected verification environment. The project does not use GitHub Actions. Before publishing a release, record the exact commands and actual results from an independent test run.

## Code design rules

1. Keep source immutable. A different text under an existing ID is a conflict. Compute SHA256 **and** Git Blob SHA from the actual UTF-8 bytes; never trust caller-supplied digests.
2. Keep consent separate from storage. An approved logical destination must be allowlisted and the user must explicitly confirm each new article.
3. Distinguish **queued**, **approved**, **uploaded via API**, **online layout verified**, and **IM sent**. A successful HTTP/MCP call never proves a Feishu document exists.
4. Handle uncertain remote uploads by reconciliation, never a second blind import. Add a regression test for any fix involving retries, timeouts or race conditions.
5. Keep credentials out of logs and responses; test unsafe URLs, DNS/IP restrictions and bad auth before adding Figure downloads.
6. Do not port any private production data into public tests; add **synthetic fixtures**.
7. Update user docs and the Tool catalog if parameters, response schema or worker behavior change.

## Reporting problems

When filing an issue, include a clear expected/actual behavior, tool name, public package version, Python version, client/transport, and **redacted** logs. Use sample article IDs such as `example_001` and invented URLs. If you suspect a security bug, see [SECURITY.md](SECURITY.md) for private reporting; do not post exploit payloads containing credentials.

## Pull requests

Open a focused pull request with a short explanation and regression tests. This is contribution guidance for outside users; the repository maintainer may also commit directly to `main` during development.

MIT license. By submitting code you agree that your contribution can be distributed under the project's MIT license.
