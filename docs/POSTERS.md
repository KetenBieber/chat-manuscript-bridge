# Markdown 文档海报

**已有 Markdown，不必再写一遍。** 选择 GitHub 仓库中的一篇 Markdown，编译为 PDF，再转换成图片并保存到该仓库。

## 生成结果

~~~text
posters/example-article/
├── document.pdf
├── page-001.png
├── page-002.png
├── poster-long.png      # 尺寸允许时生成整篇长图
└── manifest.json
~~~

长文若超过图片尺寸限制，完整 PDF 和所有单页 PNG 仍会保存；不会强行生成无法打开的超长图片。

## 安装

~~~bash
python -m pip install -e ".[poster]"
~~~

还需要安装系统软件 **Pandoc**、**XeLaTeX** 和适合文章语言的字体。

- **Ubuntu / Debian**：sudo apt install pandoc texlive-xetex texlive-lang-chinese fonts-noto-cjk
- **Windows**：安装 [Pandoc](https://pandoc.org/installing.html) 和 [TeX Live](https://tug.org/texlive/) 或 MiKTeX，再安装所需字体。
- **macOS**：安装 Pandoc、MacTeX 或 TinyTeX，并选择本机已有字体。

默认中文字体是 Noto Serif CJK SC；可通过 font 参数换成系统已安装的字体。

## 调用方式

MCP 工具名称：**generate_document_poster**。

~~~json
{
  "source_path": "manuscripts/v1/originals/example-article.md",
  "output_dir": "posters/example-article",
  "dpi": 140,
  "font": "Noto Serif CJK SC"
}
~~~

文件会写入当前 MCP 服务配置的 GitHub 仓库；已存在的**不同内容不会覆盖**。重新排版可选择新的输出目录。

## 不使用 MCP 也能生成

如果需要从终端执行，安装完成后配置 GitHub 环境变量，再运行：

~~~bash
chat-manuscript-poster --source manuscripts/v1/originals/example-article.md --output posters/example-article
~~~

命令会直接读取配置好的 GitHub 仓库并提交 PDF/PNG 文件。环境中需有 Pandoc、XeLaTeX 和对应字体。

## 图片与排版

- 支持普通 Markdown 图片语法，例如：`![图注](images/diagram.png)`。
- 相对图片路径从原 Markdown 所在目录解析，图片从同一 GitHub 仓库读取。
- 作者网站的 HTTPS 图片可通过 BRIDGE_POSTER_IMAGE_HOSTS 逐个允许；默认不会抓取任意外部网站。
- 支持 PNG、JPEG 和 WebP。图片找不到、过大或损坏时会明确报错，不会静默删图。
- 如果 Markdown 中还存在无法定位原图的 AsyncImage 标记，请先将其转换为有来源的图片链接。
- 使用 Pandoc + XeLaTeX 排版正文、标题、表格、链接、中文及常见 LaTeX 公式。
- 使用 PyMuPDF 将生成的 PDF 渲染为 PNG；默认 140 DPI，可指定 90–180 DPI。
- 最多 48 页。长图尺寸超过上限时保留逐页 PNG。

## 与文章发布分开使用

海报工具只把已有 Markdown 转换为 PDF 和 PNG，并保存 GitHub 文件；不会重写原稿，也不会自动上传飞书。

[快速开始](QUICKSTART.md) · [全部工具](TOOL_CATALOG.md)


### Docker 部署

如果希望通过 HTTP MCP 在服务器上生成海报，可以使用项目根目录的 **Dockerfile.poster**。它包含 Pandoc、XeLaTeX、中文字体和 Python 图片依赖（镜像会明显大于基础 MCP 镜像）。
