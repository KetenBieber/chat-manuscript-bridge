# Chat Manuscript Bridge

**文章在对话中写好，GitHub 保存原稿，再由发布工作流完成交付。**

这是一个开源的 [MCP（Model Context Protocol）](https://modelcontextprotocol.io/)工具：把 ChatGPT 等客户端中完成的 Markdown 文章无损归档，交给受控的发布服务，生成 PDF / PNG 图片推文，并在飞书文档核验成功后发送消息提醒。

[English](README.md) · [快速开始](docs/QUICKSTART.md) · [工具说明](docs/TOOL_CATALOG.md) · [飞书通知集成](docs/FEISHU_NOTIFICATIONS.md) · [调用示例](docs/EXAMPLES.md)

## 为什么需要它？

在对话中写出一篇文章并不难，真正麻烦的是后续存档与发布：段落丢失、公式变形、论文原图缺失、重复上传、无法确认消息有没有发送成功。

Chat Manuscript Bridge 用不可变原稿和可核验的交付记录解决这些问题。**文章由 ChatGPT 或其他 MCP 客户端完成，工具不会重新写文章。**

~~~text
ChatGPT 文章定稿
      ↓
GitHub 私有数据仓库：原稿 + SHA-256 + Git Blob SHA
      ├── 文章发布：授权 → 外部 Worker → 平台文档
      ├── 图片推文：Markdown → PDF → 单页 PNG / 长图
      └── 状态核验：查回执 / 防止重复提交
                                  ↓
                       外部发布与在线排版核验成功
                                  ↓
                         可选：飞书 IM 消息通知
~~~

## 已实现的能力

| 功能 | 状态 |
| --- | --- |
| 原稿逐字保存至单独的 GitHub 私有仓库 | 已实现 |
| SHA-256 / Git Blob SHA 原稿一致性检查 | 已实现 |
| 单篇文章 + 受限目的地的明确发布授权 | 已实现 |
| 发布状态查询、失败和未知结果的安全核对 | 已实现 |
| Markdown → PDF / 单页 PNG / 可选整篇长图 | 已实现，需要额外排版依赖 |
| 飞书文档和排版经外部 Worker 实际核验后，发送 IM 消息并记录 message_id | 已实现可选通知适配器 |
| 飞书文档本体导入、公式/图片排版 Worker | **未包含在公开版**，需额外连接 |
| ChatGPT OAuth 2.1 授权服务 | **未包含** |

公开项目不会拿「已批准」冒充「飞书已经发布」，也不会拿消息接口调用冒充通知成功。只有取得真实文档和排版核验回执后，才能发送飞书通知。

## 安装

需要 Python 3.12+：

~~~bash
git clone https://github.com/KetenBieber/chat-manuscript-bridge.git
cd chat-manuscript-bridge
python -m pip install -e ".[test]"
python -m pytest -q
python -m chat_manuscript_bridge
~~~

将私有 GitHub 仓库和访问令牌配置在 MCP 客户端的环境变量里，详细操作见 [快速开始](docs/QUICKSTART.md) 与 [客户端连接](docs/CLIENT_SETUP.md)。

需要生成海报时：

~~~bash
python -m pip install -e ".[poster]"
~~~

还需安装 Pandoc、XeLaTeX 和中文字体，详见 [图片推文说明](docs/POSTERS.md)。

## 三种使用方式

1. **对话定稿后归档：**调用 submit_manuscript 保存全文，或 publish_this_chat 一次性提交并授权。文章 ID 与原稿哈希绑定，改稿使用新的 ID。
2. **交给发布服务：**已经连接的 Worker 负责平台实际上传和在线核验；get_publication_status 展示「待交付 / 已发布 / 已核验」，失败时走 reconcile_publication。
3. **生成 PDF 图片与发送通知：**generate_document_poster 输出 PDF、分页 PNG 和可选长图；send_feishu_notification 仅在外部飞书文档与在线排版已经核验后，向明确配置的个人或群发送一次通知。

**飞书通知配置：**FEISHU_APP_ID、FEISHU_APP_SECRET、FEISHU_NOTIFY_RECEIVE_ID_TYPE、FEISHU_NOTIFY_RECEIVE_ID 必须放在私密环境中。默认只预览，不发送。未知发送结果会锁定，避免一篇文章重复通知。详见 [飞书通知集成与恢复](docs/FEISHU_NOTIFICATIONS.md)。

## 面向开发者

你可以把它接入自己的知识库、博客、文档平台或研究论文工作流，不必依赖作者的私有研究仓库。公开项目提供可复用的 MCP 接口、GitHub 存储、验证和通知适配器；真实发布平台仍由各自的 Worker 负责。

[架构](docs/ARCHITECTURE.md) · [完整工具列表](docs/TOOL_CATALOG.md) · [开发路线](docs/ROADMAP.md) · [贡献指南](CONTRIBUTING.md) · [提交问题](https://github.com/KetenBieber/chat-manuscript-bridge/issues)

MIT License · 欢迎 Star、Issue 和 Pull Request。

**关键词：**MCP、ChatGPT、Markdown 归档、飞书自动化、GitHub、科研笔记、PDF 图片推文、AI 写作工作流。
