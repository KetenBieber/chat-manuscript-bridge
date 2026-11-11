# Chat Manuscript Bridge

**把对话里的文章保存下来、发布出去，或者做成可分享的图片海报。**

这是一个面向 Markdown 文档的 MCP 工具。你可以将已经写好的文章直接存到 GitHub、交给已连接的发布服务，或者生成 PDF 和图片。

[English](README.md) · [快速开始](docs/QUICKSTART.md) · [文档海报](docs/POSTERS.md) · [功能与工具](docs/TOOL_CATALOG.md)

## 有什么功能？

| 功能 | 能做什么 |
| --- | --- |
| **保存文章** | 把完整 Markdown 原文保存到 GitHub，不再让其他 AI 改写或删减 |
| **发布文章** | 交给已连接的发布通道，并查询处理和交付结果 |
| **生成文档海报** | 把 GitHub 中已有的 Markdown 编译成 PDF，再导出逐页图片及可选的整篇长图 |
| **文章管理** | 查找文章、查看进度、处理失败或中断的任务 |

海报文件会直接写到你指定的 **GitHub 仓库文件夹**：

~~~text
posters/my-article/
  document.pdf
  page-001.png
  page-002.png
  poster-long.png        # 篇幅允许时生成整篇长图
  manifest.json
~~~

> 公开 MCP 已提供文章存档与海报导出。飞书等平台的实际上传需另行连接对应的发布服务；当前代码包不包含飞书上传 Worker。

## 怎么使用？

安装 Python 3.12+：

~~~bash
git clone https://github.com/KetenBieber/chat-manuscript-bridge.git
cd chat-manuscript-bridge
python -m pip install -e .
python -m chat_manuscript_bridge
~~~

配置 GitHub 仓库和凭据，再把 MCP 服务加入你使用的客户端。详见 [快速开始](docs/QUICKSTART.md)。

如果需要 PDF / PNG 海报，还需安装：

~~~bash
python -m pip install -e ".[poster]"
~~~

并安装 Pandoc、XeLaTeX 和合适的字体。具体步骤见 [文档海报](docs/POSTERS.md)。

也可以不通过 MCP，在已经配置 GitHub 变量的终端中执行：

~~~bash
chat-manuscript-poster --source manuscripts/v1/originals/my-article.md --output posters/my-article
~~~

连接后可以直接说：

> 把 GitHub 中的 my-article.md 做成 PDF 和长图海报，放到 posters/my-article 文件夹。

工具会读取现有 Markdown，编译为 PDF，导出每页 PNG，并在尺寸允许时拼成一张长图，最后保存回 GitHub。

## 功能入口

**submit_manuscript** · **publish_this_chat** · **approve_publication** · **generate_document_poster** · **list_manuscripts** · **get_publication_status** · **reconcile_publication**

[完整功能说明](docs/TOOL_CATALOG.md) · [海报使用说明](docs/POSTERS.md) · [调用示例](docs/EXAMPLES.md)

MIT 开源 · [贡献指南](CONTRIBUTING.md)
