# Chat Manuscript Bridge

**Save your writing. Publish it. Turn it into shareable posters.**

An MCP tool for moving finished Markdown documents out of conversations—into GitHub, connected publishing services, or shareable PDF and PNG images.

[简体中文](README.zh-CN.md) · [Get started](docs/QUICKSTART.md) · [Create posters](docs/POSTERS.md) · [MCP tools](docs/TOOL_CATALOG.md)

## What can it do?

| Feature | What you get |
| --- | --- |
| **Save articles to GitHub** | Keep the full Markdown document, without asking another AI to rewrite it |
| **Hand off for publication** | Approve a document for a connected publishing workflow and check its delivery status |
| **Create document posters** | Turn an existing GitHub Markdown file into a PDF, page images and an optional long poster |
| **Organize and revisit** | Find saved documents, inspect progress and safely resume interrupted jobs |

Poster files are saved directly into a folder in your selected GitHub repository:

~~~text
posters/my-article/
  document.pdf
  page-001.png
  page-002.png
  poster-long.png        # if the image is not too large
  manifest.json
~~~

> The MCP package includes GitHub storage and poster export. Publishing to Feishu or other document services needs a separately connected destination worker; it is not bundled here.

## Quick start

**Requires Python 3.12+ and an MCP-compatible client.**

~~~bash
git clone https://github.com/KetenBieber/chat-manuscript-bridge.git
cd chat-manuscript-bridge
python -m pip install -e .
python -m chat_manuscript_bridge
~~~

Configure your GitHub repository and access token in the server environment. See the [quickstart](docs/QUICKSTART.md) for client connection instructions.

To enable **document posters**, also install:

~~~bash
python -m pip install -e ".[poster]"
~~~

The poster engine uses Pandoc, XeLaTeX and a suitable installed font. The [poster guide](docs/POSTERS.md) covers Windows and Linux setup.

You can also run poster export without an MCP client:

~~~bash
chat-manuscript-poster --source manuscripts/v1/originals/my-article.md --output posters/my-article
~~~

### Example

Ask your connected MCP client:

> Generate a PDF and image posters from my-article.md in GitHub, and save them in the posters/my-article folder.

The **generate_document_poster** tool reads the existing Markdown, creates real PDF and PNG files, and saves them back into GitHub. Long documents always retain their individual page images.

## MCP tools

**submit_manuscript** · **publish_this_chat** · **approve_publication** · **generate_document_poster** · **list_manuscripts** · **get_publication_status** · **reconcile_publication** · **inspect_configuration** · **inspect_legacy_article**

[All tools](docs/TOOL_CATALOG.md) · [Poster setup](docs/POSTERS.md) · [Examples](docs/EXAMPLES.md) · [Security](SECURITY.md)

MIT licensed · [Contributing](CONTRIBUTING.md)
