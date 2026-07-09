# Using GlideGrail.md with your AI tools

[`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) is just a markdown file — wiring it into
an assistant always comes down to "load it as context, and tell the model to follow it." But
*how* you load it matters, because the same file behaves differently depending on the
mechanism, and this doc is large (~24,000 words, roughly **41K tokens**). This guide covers
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
Claude Code, Claude.ai, Codex, Gemini CLI, Cursor, and Copilot.

**Easiest — install as a plugin.** In **Claude Code**:

```bash
/plugin marketplace add bikemeardsley/GlideGrail.md
/plugin install glidegrail@glidegrail
```

In the **Claude desktop app**:

1. Open **Customize → Skills**.
2. Next to **Personal plugins**, click **+**.
3. Click **+ Create plugin**, then **Add marketplace**.
4. Paste `bikemeardsley/GlideGrail.md`, then click **Sync**.
5. Click **Install**.

Either way you get the skill with auto-updates, and the standards load automatically whenever a task is ServiceNow-related.
**Gemini CLI — install as an extension:**

```bash
gemini extensions install https://github.com/bikemeardsley/GlideGrail.md
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
- **Plugin (desktop app):** Customize → Skills → **+** next to "Personal plugins" → paste
  `bikemeardsley/GlideGrail.md` → Sync → Install.
- **Skill upload (web, paid plans):** Settings → Skills → upload the zipped `glidegrail/`
  folder. Loads on demand in any chat.
- **Project knowledge:** create a Project, add `GlideGrail.md` to its knowledge, and add
  *"For any ServiceNow code, follow GlideGrail.md"* to the Project instructions — grounds
  every chat in that Project.

### Claude Code
- **Plugin (recommended):** `/plugin marketplace add bikemeardsley/GlideGrail.md` then
  `/plugin install glidegrail@glidegrail`. Auto-updates; loads on demand.
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

### Cursor
- **Project rule (`.mdc`):** create `.cursor/rules/glidegrail.mdc` as an **Agent Requested**
  rule — set `alwaysApply: false`, write a clear `description` (Cursor uses it to decide when
  to load), and point the body at your copy of `GlideGrail.md`. A plain `.md` file in
  `.cursor/rules/` is ignored — it needs the `.mdc` extension. Don't use `alwaysApply: true`:
  at ~41K tokens it would blow the context budget every turn.
- **Remote Rule (no copy in your repo):** Settings → Rules → *Remote Rule (GitHub)* → paste
  this repo's URL. Auto-syncs when the repo updates.

### Gemini
- **Gemini CLI — extension (recommended):** one command installs this repo as an extension,
  with auto-updates:
  ```bash
  gemini extensions install https://github.com/bikemeardsley/GlideGrail.md
  ```
  Gemini loads the bundled skill on demand; update later with
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
  from the community hub (or import/paste from [`open-webui/`](./open-webui/)), **Enable** it,
  toggle **Global**. It detects ServiceNow topics and injects only the relevant standards
  sections; non-ServiceNow chats are untouched. On a ServiceNow-dedicated instance or model,
  set the `assume_servicenow_context` valve to `true`; for small local models lower
  `char_budget`.
- **Tool — on-demand lookup (optional companion):** install
  [GlideGrail ServiceNow Coding Standards Lookup](https://openwebui.com/posts/glidegrail_servicenow_coding_standards_lookup_871d3d99)
  so models with solid function-calling can pull specific sections mid-chat
  (`get_glidegrail_guidance("acl debugging")`). Don't rely on it alone for enforcement —
  many local models never call tools.
- **No admin rights? Knowledge base:** Workspace → Knowledge → upload
  [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md), then reference it with `#` in chat or
  attach it to a custom model with an instruction to follow it.

Full valve reference, deployment profiles, and install options:
[`open-webui/README.md`](./open-webui/README.md).

### Any other assistant
- **Fetch by URL (`llms.txt`) — no install:** any agent with web access can pull the
  standards on demand. Tell it to fetch
  `https://raw.githubusercontent.com/bikemeardsley/GlideGrail.md/main/llms.txt` — an
  [llms.txt](https://llmstxt.org/) index that links straight to the raw standards — and
  follow the standards link before writing ServiceNow code. Also handy as the canonical
  URL for Cursor Remote Rules or an Open WebUI knowledge base.
- Drop an **`AGENTS.md`** at the repo root pointing to
  [`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) — Cursor, Copilot, and Codex all read
  it. Otherwise the universal fallback always works: load the markdown as a system/context
  instruction and tell the model to follow it before writing ServiceNow code.
