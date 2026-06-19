# Using GlideGrail.md with your AI tools

[`GlideGrail.md`](./GlideGrail.md) is just a markdown file — wiring it into an assistant always comes down to
"load it as context, and tell the model to follow it." But *how* you load it matters, because
the same file behaves differently depending on the mechanism, and this doc is large
(~24,000 words, roughly **41K tokens**). This guide covers the three ways to load it and the
exact steps for each assistant.

## Three ways to load it

Almost every tool reduces to one of these:

| Pattern | How the model sees it | Context cost | Presence | Best for |
|---|---|---|---|---|
| **Always-on instructions file** | Full text injected into **every** request | High — paid every turn | Guaranteed | Short rule sets; IDE agents |
| **Skill ([`SKILL.md`](./SKILL.md))** | ~100 tokens until the model decides it's relevant, then loads on demand | Low and elastic | On-demand | **Large references like this one**; multi-tool setups |
| **Retrieval / knowledge base / project context** | Only the chunks matching your prompt are pulled in | Low | Probabilistic | Chat apps (Claude / ChatGPT / Gemini) |

## Ship it as a skill (recommended)

For a doc this size, a **skill** is the best home: the model reads only a short description
until your prompt looks like ServiceNow work, then loads the full standards on demand — so it
costs almost nothing in context until it's actually needed. The same skill works across
Claude Code, Claude.ai, Codex, Gemini CLI, Cursor, and Copilot.

The skill is two files — [`SKILL.md`](./SKILL.md) and [`GlideGrail.md`](./GlideGrail.md) — kept together in a
folder:

```
glidegrail/
├── SKILL.md
└── GlideGrail.md
```

To install, copy both into a folder named `glidegrail/` inside your tool's skills directory
(or zip the folder for the claude.ai upload). The exact location per tool is below.

## Per-tool setup

Each tool supports more than one of the three patterns — pick based on how guaranteed you
need the standards to be present versus how much context you want to spend.

### Claude — claude.ai (web / desktop / mobile)
- **Project knowledge:** create a Project, add [`GlideGrail.md`](./GlideGrail.md) to its knowledge, and add
  *"For any ServiceNow code, follow GlideGrail.md"* to the Project instructions. Grounds every
  chat in that Project.
- **Skill (paid plans):** Settings → Skills → upload the zipped `glidegrail/` folder. Loads on
  demand in any chat — use this if you want it available outside a single Project.

### Claude Code
- **Skill (recommended):** put the `glidegrail/` folder in `.claude/skills/` (shared via the
  repo) or `~/.claude/skills/` (personal, all projects). Loads automatically when relevant.
- **`CLAUDE.md` pointer:** add *"For all ServiceNow code, follow GlideGrail.md"* and keep the
  doc in the repo. `CLAUDE.md` is injected every turn, so point — don't paste the whole doc.
- **Ad hoc:** `claude --add-dir /path/to/glidegrail` for a single session.

### ChatGPT (app)
- **Project:** upload [`GlideGrail.md`](./GlideGrail.md) and add *"Follow GlideGrail.md for all ServiceNow code"*
  to the Project instructions. Files and instructions carry across every chat in the Project.
- **Custom GPT:** add [`GlideGrail.md`](./GlideGrail.md) as a knowledge file and reference it in the GPT's
  instructions — best for a reusable, shareable ServiceNow assistant.

### OpenAI Codex
- **Skill (recommended):** put the `glidegrail/` folder at `.agents/skills/glidegrail/` in the
  repo (Codex scans from the working directory up to the repo root) or `~/.agents/skills/`.
- **`AGENTS.md` pointer:** Codex reads `AGENTS.md` at the repo root — add a line directing it
  to [`GlideGrail.md`](./GlideGrail.md).

### GitHub Copilot
- **Repo-wide:** create `.github/copilot-instructions.md` with *"For ServiceNow code, follow
  GlideGrail.md."* Applies in Copilot Chat, agent mode, the cloud agent, and CLI — but **not**
  inline ghost-text completions.
- **Path-scoped:** add `.github/instructions/servicenow.instructions.md` with an `applyTo:`
  glob so it loads only for matching files (e.g. `**/*.{js,xml}`).
- **Skill:** a `.github/skills/glidegrail/` skill activates only when the task matches — the
  lightest-context option if your repo isn't ServiceNow-only.

### Cursor
- **Project rule (`.mdc`):** create `.cursor/rules/glidegrail.mdc` as an **Agent Requested**
  rule — set `alwaysApply: false`, write a clear `description` (Cursor uses it to decide when
  to load), and point the body at `@GlideGrail.md`. A plain `.md` file in `.cursor/rules/` is
  ignored — it needs the `.mdc` extension. Don't use `alwaysApply: true`: at ~41K tokens it
  would blow the context budget every turn.
- **Remote Rule (no copy in your repo):** Settings → Rules → *Remote Rule (GitHub)* → paste
  this repo's URL. Auto-syncs when the repo updates.

### Gemini
- **Gemini app — Gem:** create a Gem, add *"Follow GlideGrail.md for all ServiceNow code"* to
  its instructions, and upload [`GlideGrail.md`](./GlideGrail.md) as a context file.
- **Gemini CLI:** put the `glidegrail/` folder in `.gemini/skills/` or `.agents/skills/`; or
  add a `GEMINI.md` pointer (you can `@GlideGrail.md` to import it). *(Gemini CLI is mid-
  transition to Antigravity CLI for some account tiers — check current docs for exact
  context-file behavior.)*

### Any other assistant
- Drop an **`AGENTS.md`** at the repo root pointing to [`GlideGrail.md`](./GlideGrail.md) — Cursor, Copilot, and
  Codex all read it. Otherwise the universal fallback always works: load the markdown as a
  system/context instruction and tell the model to follow it before writing ServiceNow code.
