# Project launch kit

Useful text and links for sharing Chat Manuscript Bridge. **The code is public, but these drafts are not evidence that a third-party forum post or formal GitHub Release has already been published.**

## GitHub repository description (short)

Source-faithful MCP publishing bridge: archive Markdown in GitHub, export PDF posters, verify delivery, and notify via Feishu IM.

## Suggested GitHub topics

`mcp` · `model-context-protocol` · `chatgpt` · `markdown` · `github` · `feishu` · `lark` · `pdf` · `publishing` · `research-workflow`

## 中文介绍（适合 V2EX / 掘金 / 技术交流群）

我把平时在 ChatGPT 对话中完成的长篇论文解读，整理成了一个独立的开源 MCP 工具：**Chat Manuscript Bridge**。

主要解决的是文章从对话到正式交付的衔接问题：原稿保存到自己的 GitHub 私有仓库、做 SHA-256 和 Git Blob SHA 校验、针对单篇文章授权发布、查询真实的远端交付状态，以及把 Markdown 导出成 PDF / 分页 PNG / 可选长图。

这次增加了一个可选飞书 IM 通知适配器：需要已有发布 Worker 提供真实的飞书文档与在线排版核验回执，才能发送消息；对结果不确定的网络请求，工具不会盲目补发，以免重复通知。

需要特别说明：公开仓库目前提供归档、验证、图片推文和消息通知接口；**飞书文档导入及排版 Worker 不包含在这个开源包内**。不需要使用我的私有论文库，也可以部署工具的通用部分。

GitHub：https://github.com/KetenBieber/chat-manuscript-bridge

欢迎帮忙测试不同 MCP 客户端、提 Issue，或者贡献新的发布平台适配器。

## English introduction (for GitHub Discussions, Hacker News, MCP communities)

I built **Chat Manuscript Bridge**, an open-source MCP server for the part of AI-assisted writing that happens *after* the draft is finished.

It preserves the approved Markdown in your own private GitHub repository, checks both SHA-256 and the Git Blob SHA, requires source-bound publication consent, and distinguishes a queued job from a real delivery receipt. It can export the stored Markdown to PDF and page/long-image posters.

There is also an optional Feishu/Lark IM notification adapter: it sends only after an independently connected worker has provided authentic document and layout-verification receipts, with a durable claim to prevent blind duplicate sends.

**Scope note:** the public package does *not* include the full Feishu document-import/formatting worker. I am publishing the reusable source-handoff, poster and verified-notification parts separately from my private research content.

Repo: https://github.com/KetenBieber/chat-manuscript-bridge

Feedback on MCP client support, interoperability, and additional publishing providers is welcome.

## Suggested first demo

Record a short terminal walkthrough using an intentionally synthetic manuscript, not personal research documents or credentials:

1. Show the README and run `python -m pytest -q`.
2. Call `submit_manuscript` with test Markdown and show its two source fingerprints.
3. Call `approve_publication` with confirmation disabled, then demonstrate that approval is never represented as an uploaded document.
4. Call `generate_document_poster` on a test manuscript, displaying the resulting PDF and page PNGs.
5. Explain that Feishu IM sending requires a genuine external publication receipt and a matching layout audit; do not fabricate successful external sends.

## Release / promotion checklist

- Verify tests with a local Python 3.12/3.13 environment and document real results.
- Restore GitHub Actions or provide a reproducible independent test log before marking CI green.
- Review tag and release artifacts; publish a GitHub Release only after validation.
- Configure repository description and topics on GitHub (not automatically updated by a README commit).
- Share the Chinese and English introductions where relevant; collect reproducible feedback, do not inflate stars/downloads or claim unimplemented features.
