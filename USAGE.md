# Using GlideGrail.md with your AI tools

[`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) is just a markdown file — wiring it into
an assistant always comes down to "load it as context, and tell the model to follow it." But
*how* you load it matters, because the same file behaves differently depending on the
mechanism, and this doc is large (~28,000 words, roughly **47K tokens**). This guide covers
the three ways to load it and the exact steps for each assistant.

## Three ways to load it

Almost every tool reduces to one of these:

| Pattern | How the model sees it | Context cost | Presence | Best for |
|---|---|---|---|---|
| **Always-on instructions file** | Full text injected into **every** request | High — paid every turn | Guaranteed | Short rule sets; IDE agents |
| **Skill ([`SKILL.md`](./skills/glidegrail/SKILL.md))** | ~100 tokens until the model decides it's relevant, then loads on demand | Low and elastic | On-demand | **Large references like this one**; multi-tool setups |
| **Retrieval / knowledge base / project context** | Only the chunks matching your prompt are pulled in | Low | Probabilistic | Chat apps (Claude / ChatGPT / Gemini) |

## Ship it as a skill (recommended)

For a doc this size, a **skill** is the best home: the model reads only a short description
until your prompt looks like ServiceNow work, then loads the full standards on demand — so it
costs almost nothing in context until it's actually needed. The same skill works across
Claude Code, Claude.ai, Codex, Gemini CLI, Cursor, Copilot, Cline, Roo Code, Junie, and Open WebUI.

**Easiest — install as a plugin.** In **Claude Code**:

```bash
/plugin marketplace add bikemeardsley/GlideGrail.md
/plugin install glidegrail@glidegrail
```

In **claude.ai** (web or desktop app):

1. Open **Customize → Plugins**, then click **Add → Add marketplace**.
2. Enter `bikemeardsley/GlideGrail.md` and install the **glidegrail** plugin.

The plugin is saved to your account, so it also shows up in Cowork and Claude Code. Either way
the standards load automatically whenever a task is ServiceNow-related.

Updates are **not** automatic for third-party marketplaces. In Claude Code, turn them on under
`/plugin` → **Marketplaces → Enable auto-update**, or run `claude plugin update glidegrail@glidegrail`.
In claude.ai, use **Check for updates** or turn on **Sync automatically** for the marketplace.

**Gemini CLI — install as an extension:**

```bash
gemini extensions install https://github.com/bikemeardsley/GlideGrail.md --auto-update
```

**Any other tool — use the skill folder directly.** The skill lives at
[`skills/glidegrail/`](./skills/glidegrail/) — [`SKILL.md`](./skills/glidegrail/SKILL.md) and
[`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) together:

```
glidegrail/
├── SKILL.md
└── GlideGrail.md
```

Copy that folder into your tool's skills directory (or zip it for the claude.ai upload). The
exact location per tool is below.

## Per-tool setup

Each tool supports more than one of the three patterns — pick based on how guaranteed you
need the standards to be present versus how much context you want to spend.

### Claude — claude.ai (web / desktop / mobile)
- **Plugin:** Customize → Plugins → **Add → Add marketplace** → enter
  `bikemeardsley/GlideGrail.md` → install. See the update note [above](#ship-it-as-a-skill-recommended).
- **Skill upload (all plans):** Customize → Skills → **+ → Create skill → Upload a skill** →
  the zipped `glidegrail/` folder. Needs **Code execution and file creation** on under
  Settings → Capabilities. Loads on demand in any chat.
- **Project knowledge:** create a Project, add `GlideGrail.md` to its knowledge, and add
  *"For any ServiceNow code, follow GlideGrail.md"* to the Project instructions — grounds
  every chat in that Project.

### Claude Code
- **Plugin (recommended):** `/plugin marketplace add bikemeardsley/GlideGrail.md` then
  `/plugin install glidegrail@glidegrail`. Loads on demand; enable auto-update for the
  marketplace in `/plugin` → Marketplaces (off by default for third-party ones). There's also an
  optional `servicenow-docs` plugin in a separate marketplace — see
  [Companion plugin](#companion-plugin--live-servicenow-docs) at the end of this doc.
- **Skill folder (manual):** copy `skills/glidegrail/` into `.claude/skills/` (shared via the
  repo) or `~/.claude/skills/` (personal, all projects).
- **`CLAUDE.md` pointer:** add *"For all ServiceNow code, follow GlideGrail.md"* and keep the
  doc in the repo. `CLAUDE.md` is injected every turn, so point — don't paste the whole doc.

### ChatGPT (app)
- **Project:** upload [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) and add *"Follow
  GlideGrail.md for all ServiceNow code"* to the Project instructions. Files and instructions
  carry across every chat in the Project.

### OpenAI Codex
- **Skill (recommended):** copy `skills/glidegrail/` to `.agents/skills/glidegrail/` in the
  repo (Codex scans from the working directory up to the repo root) or `~/.agents/skills/`.
- **`AGENTS.md` pointer:** Codex reads `AGENTS.md` at the repo root — add a line directing it
  to [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md).

### GitHub Copilot
- **Repo-wide:** create `.github/copilot-instructions.md` with *"For ServiceNow code, follow
  GlideGrail.md."* Applies in Copilot Chat, agent mode, the cloud agent, and CLI — but **not**
  inline ghost-text completions.
- **Path-scoped:** add `.github/instructions/servicenow.instructions.md` with an `applyTo:`
  glob so it loads only for matching files (e.g. `**/*.{js,xml}`).
- **Skill:** copy `skills/glidegrail/` to `.github/skills/glidegrail/` — activates only when
  the task matches, the lightest-context option if your repo isn't ServiceNow-only.

### Microsoft 365 Copilot
- **Custom agent (agent builder):** in Copilot chat, choose **New agent** in the left pane →
  **Skip to configure** → add *"For all ServiceNow code, follow GlideGrail.md; ask for the
  project's PREFIX if unknown"* to the instructions → under **Knowledge**, upload
  [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) renamed to `.txt` (`.md` isn't a
  supported upload type), point at a copy in SharePoint/OneDrive, or add
  `https://github.com/bikemeardsley/GlideGrail.md` as a website source (website sources allow
  at most two path levels, so a raw file URL won't work). Retrieval is chunk-based like a
  ChatGPT Project — relevant sections are pulled per prompt. Once it works, share the agent
  with your team.
- Requires an M365 Copilot license, and agent creation can be admin-restricted — if
  **New agent** is missing, ask your tenant admin.

### Cursor
- **Plugin:** install from the
  [cursor.directory listing](https://cursor.directory/plugins/glidegrail-servicenow-coding-standards).
- **Skill (recommended for a manual setup):** copy `skills/glidegrail/` to
  `.cursor/skills/glidegrail/` (or `.agents/skills/`, or `~/.cursor/skills/` for all
  projects). Cursor also reads `.claude/skills/` and `.codex/skills/`.
- **Project rule (`.mdc`):** create `.cursor/rules/glidegrail.mdc` as an **Apply
  Intelligently** rule — set `alwaysApply: false`, write a clear `description` (Cursor uses it
  to decide when to load), and point the body at your copy of `GlideGrail.md`. A plain `.md`
  file in `.cursor/rules/` is ignored — it needs the `.mdc` extension. Don't use
  `alwaysApply: true`: at ~47K tokens it would blow the context budget every turn.

### Cline / Roo Code
- **Skill (recommended):** copy `skills/glidegrail/` to `.cline/skills/glidegrail/` (Cline;
  `.claude/skills/` also works) or `.roo/skills/glidegrail/` (Roo Code; `.agents/skills/`
  also works). Loads only when the task matches.
- **Rules-folder pointer:** create `.clinerules/glidegrail.md` (Cline) or
  `.roo/rules/glidegrail.md` (Roo Code) in your project. Rules files are injected into
  **every** request, so at ~47K tokens don't paste the doc itself — point instead:

  ```markdown
  For any ServiceNow code, load and follow GlideGrail.md before writing:
  https://raw.githubusercontent.com/bikemeardsley/GlideGrail.md/main/skills/glidegrail/GlideGrail.md
  (or the local copy if this repo vendors one). Substitute PREFIX with this
  project's scoped-app prefix.
  ```

  Both tools can read a vendored copy of the doc from the repo on demand, which also works
  fully offline — a good fit if you're pairing them with local models via Open WebUI/Ollama.

### JetBrains (AI Assistant / Junie)
- **Junie — skill (recommended):** copy `skills/glidegrail/` to `.junie/skills/glidegrail/`
  or `.agents/skills/glidegrail/`. Works in the Junie CLI and the IDE plugin.
- **Junie — pointer:** put the same short pointer text as the Cline example above in
  `.junie/AGENTS.md` or the root `AGENTS.md` (see [`templates/AGENTS.md`](./templates/AGENTS.md)).
  `.junie/guidelines.md` still works but is the legacy location. Point, don't paste.
- **AI Assistant:** add the pointer as a project rule (Settings → Tools → AI Assistant →
  **Rules**, which creates `.aiassistant/rules/*.md`), or keep a vendored `GlideGrail.md` in
  the repo and attach it to chats with the file-context picker when working on ServiceNow code.

### Gemini / Antigravity
- **Antigravity CLI — plugin (recommended):** Antigravity replaces Gemini CLI. One command
  installs this repo as a plugin with the skill:
  ```bash
  agy plugin install https://github.com/bikemeardsley/GlideGrail.md
  ```
  Already have the Gemini CLI extension? `agy plugin import gemini` converts it.
- **Gemini CLI — extension:** one command installs this repo as an extension:
  ```bash
  gemini extensions install https://github.com/bikemeardsley/GlideGrail.md --auto-update
  ```
  Gemini loads the bundled skill on demand. Without `--auto-update`, update by hand with
  `gemini extensions update glidegrail`. No build step — it's pure markdown.
- **Gemini CLI — manual:** copy `skills/glidegrail/` to `.gemini/skills/glidegrail/`.
- **Gemini app — Gem:** create a Gem, add *"Follow GlideGrail.md for all ServiceNow code"* to
  its instructions, and upload [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) as a
  context file.

### Open WebUI

Open WebUI gets its own mechanism — a **Filter function** that runs in the platform's request
pipeline, so the standards are injected automatically for **any** model you serve (local
Ollama models, OpenRouter, anything), with no model cooperation needed.

- **Filter — automatic enforcement (recommended; requires admin):** install
  [GlideGrail ServiceNow Coding Standards Enforcement](https://openwebui.com/posts/glidegrail_servicenow_coding_standards_enforcement_00c849c7)
  from the community hub, **Enable** it,
  toggle **Global**. It detects ServiceNow topics and injects only the relevant standards
  sections; non-ServiceNow chats are untouched. On a ServiceNow-dedicated instance or model,
  set the `assume_servicenow_context` valve to `true`; for small local models lower
  `char_budget`.
- **Tool — on-demand lookup (optional companion):** install
  [GlideGrail ServiceNow Coding Standards Lookup](https://openwebui.com/posts/glidegrail_servicenow_coding_standards_lookup_871d3d99)
  so models with solid function-calling can pull specific sections mid-chat
  (`get_glidegrail_guidance("acl debugging")`). Don't rely on it alone for enforcement —
  many local models never call tools.
- **No admin rights? Skill:** install the
  [GlideGrail skill](https://openwebui.com/posts/glidegrail_d3af0156) from the community hub. The model loads the standards on demand; needs native function calling.
- **Skills not enabled either? Knowledge base:** Workspace → Knowledge → upload
  [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md), then reference it with `#` in chat or
  attach it to a custom model with an instruction to follow it.

### Any other assistant
- **Fetch by URL (`llms.txt`) — no install:** any agent with web access can pull the
  standards on demand. Tell it to fetch
  `https://raw.githubusercontent.com/bikemeardsley/GlideGrail.md/main/llms.txt` — an
  [llms.txt](https://llmstxt.org/) index that links straight to the raw standards — and
  follow the standards link before writing ServiceNow code.
- Drop an **`AGENTS.md`** at the repo root pointing to
  [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) — Codex, Cursor, Copilot, Cline, Junie, Zed, Jules,
  Devin, Amp, and most other agents read it. A ready-made copy lives at
  [`templates/AGENTS.md`](./templates/AGENTS.md): copy it in, set your `PREFIX`, done.
  Otherwise the universal fallback always works: load the markdown as a system/context
  instruction and tell the model to follow it before writing ServiceNow code.

## Companion plugin — live ServiceNow docs

`GlideGrail.md` is the judgment layer: *how* you want ServiceNow code written. It works on its
own. If you also want the agent to check *what the platform actually does*, there's a separate,
independent plugin for that: **[`servicenow-docs`](https://github.com/bikemeardsley/claude-servicenow-docs)**.

It bundles the Fetch MCP server plus a skill that reads ServiceNow's official documentation
live from GitHub — the [`ServiceNow/ServiceNowDocs`](https://github.com/ServiceNow/ServiceNowDocs)
repo, which publishes the AI Platform docs as one Markdown file per topic with an `llms.txt`
index. The agent reads the index, fetches the one or two topics it needs, and cites them.
Nothing is cloned or downloaded, and there is nothing to keep in sync.

**Prerequisite — `uv`.** The Fetch server launches via `uvx`, so `uv` must be installed. It
provisions its own Python, so Python is not a separate prerequisite.

- macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Reopen your terminal afterwards so `uvx` lands on `PATH`, and check with `uvx --version`.

**Install (Claude Code):**
```bash
/plugin marketplace add bikemeardsley/claude-servicenow-docs
/plugin install servicenow-docs@servicenow-docs
```

Restart Claude, then run `/mcp` — a `fetch` server should be listed and connected. If it
isn't, `uv` is almost certainly missing or not yet on `PATH`. The first launch is slower while
`uvx` downloads and caches the server.

**Claude Desktop needs one extra step.** Desktop lists the plugin's bundled Fetch server under
**Connectors**, but can't start it from there, so the server has to be added to Desktop's own
config once: fully quit Claude Desktop, open **Settings → Developer → Edit Config**, and merge
`"fetch": { "command": "uvx", "args": ["--with", "mcp<2", "mcp-server-fetch"] }` into the
`mcpServers` object in `claude_desktop_config.json` (keeping any servers already there), then
relaunch. Full steps: [Claude Desktop setup](https://github.com/bikemeardsley/claude-servicenow-docs#claude-desktop-setup).

**Tradeoffs.** Retrieval is online and file-at-a-time: always current and light on context,
but it needs internet access and can't grep the whole corpus. For offline use or full-corpus
search, clone the docs repo and point a filesystem or git MCP server at it instead.

Details and troubleshooting: [`bikemeardsley/claude-servicenow-docs`](https://github.com/bikemeardsley/claude-servicenow-docs).
