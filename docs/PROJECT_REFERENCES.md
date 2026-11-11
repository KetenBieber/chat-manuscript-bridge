# Design references for the open-source presentation

The repository information architecture is inspired by well-maintained **high-visibility** Agent Skills and MCP projects. These are references for **documentation patterns**, not dependencies, endorsements, or copied code/design assets.

| Project | Useful pattern | Adaptation here |
| --- | --- | --- |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | Clear one-sentence purpose, client setup recipes, capability distinctions | Focused subtitle + stdio/HTTP instructions, honest ChatGPT auth caveat |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | User-facing tasks first, then tools and setup | Use-case / tool table, explicit capability explanations |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | Distinction between educational reference implementations and production readiness | Strong v0.1 warning and public/private delivery boundary |
| [anthropics/skills](https://github.com/anthropics/skills) | Discoverability and direct installation guidance | Navigation between README, quickstart, tool catalog and worked examples |
| [obra/superpowers](https://github.com/obra/superpowers) | Concise positioning, process overview and installation by environment | Practical first-screen overview, safe workflow and platform-specific instructions |

## What we intentionally avoid

- Fabricated usage statistics, stars or download counts.
- A pretend working Feishu demo that is actually private production infrastructure.
- “One-click ChatGPT install” claims without a genuine connected MCP and compatible auth.
- Third-party logos, screenshots or branding assets copied without permission.
- Marketing badges claiming a release or test state absent from the repository.
- A flood of stale migration notes at the top of the public README.

The public README aims to answer, in order: **What is this? Who needs it? What works now? How do I try it? Which tools does it expose? Where are the limits?**

Project copyright, source code, copy and diagrams are original to this repository. Read individual reference licenses if incorporating actual code from any external project.
