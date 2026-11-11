# Chat Manuscript Bridge

**保留原始正文，让每一次交付都有证据。**

这是一个可自行部署的通用 MCP 服务：把当前对话里真正完成的长篇文章，逐字保存到个人 Private GitHub 仓库，使用 Git Blob SHA 和 SHA256 验证原稿，为每篇文章保存明确的发布授权，并通过状态工具检查进度与失败原因。

**当前 v0.1 为基础开发版**，已实现 MCP 入口、GitHub 不可变存储、发布目标白名单、原稿逐篇授权、查询状态和防止不明结果重复发布的基础协议。**公共仓库中的飞书 DOCX 上传、原生公式修复、在线布局验收和 IM 通知 Worker 尚未迁移。** 因此当前的批准状态不等于飞书发布成功。原来的 Private 仓库和生产 Railway 服务保持不变。

## 代码与数据明确分离

- **Public 仓库**：只发布通用 MCP 程序、测试、协议和部署文档。
- **Private 数据仓库**：存放你的完整论文原稿、图片、研究笔记、个人飞书配置及真实回执。
- **ChatGPT / 原作者**：负责正文；MCP 不产生另一份改写后的文章。
- **交付 Worker**：以后负责确定性转换、飞书上传、公式和图片校验、真实回执与通知。

## 快速使用

需要 Python 3.12+：

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
python -m pytest -q
~~~

在环境变量中配置自己的 Private GitHub 仓库、只对该仓库授权的细粒度 Token，以及允许发布的逻辑目标。完整示例见 [.env.example](.env.example)，服务不会自动加载 .env 文件。

~~~text
BRIDGE_GITHUB_REPO=your-account/your-private-data-repo
BRIDGE_GITHUB_TOKEN=your-fine-grained-token
BRIDGE_ALLOWED_DESTINATIONS=personal-knowledge-base
~~~

本地 MCP stdio：运行 **python -m chat_manuscript_bridge**。HTTP 模式需要准确的 BRIDGE_ALLOWED_HOST 和至少 24 字符的 BRIDGE_MCP_TOKEN，通过 Uvicorn 启动并在外部使用 HTTPS；访问路径为 **/mcp**。

## 已提供的工具

| 工具 | 能力 |
| --- | --- |
| submit_manuscript | 原稿字节级保存，重复提交只能是同一内容 |
| approve_publication | 授权指定原稿与白名单目标 |
| publish_this_chat | 一次请求完成保存与授权，**不假冒已上传** |
| get_publication_status | 查询哈希、真实回执、最终布局验收状态 |
| reconcile_publication | 只读恢复建议，不会重复上传 |
| list_manuscripts | 列出私有仓库原稿 ID |
| inspect_configuration | 检查非敏感配置与当前能力 |

新仓库的建立不意味着 ChatGPT 已经连接自建 MCP；需要先部署，再连接真实服务。详细说明：[API](docs/API.md) · [Architecture](docs/ARCHITECTURE.md) · [Security](SECURITY.md)。

本软件使用 MIT License，私人文档与历史数据不得随着代码一起公开。
