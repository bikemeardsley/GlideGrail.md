# 🏆GlideGrail()
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00.svg?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/bikemeardsley)
[![ServiceNow docs.md](https://img.shields.io/badge/ServiceNow-docs.md-62D84E.svg?logo=servicenow&logoColor=white)](https://github.com/ServiceNow/ServiceNowDocs)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-blue.svg)](LICENSE)

#### *ServiceNow Coding Standards for Humans and AI Agents*

Most ServiceNow best practice material is scattered across community posts, docs, tribal
knowledge, or just not widely known, and written to be read by a human. GlideGrail() consolidates years of experience and common rules
into a single reference written to be consumed by a model: concrete, directive, and
specific enough to change what your AI assistant (Claude, ChatGPT, Codex, Gemini, Copilot,
Cursor) actually produces. "Use `GlideAggregate` to count, never `getRowCount()`." "One
Script Include per table, named `[PREFIX][Table]Service`."

Rules, not paragraphs, and equally useful as a human reference or a review checklist.

> **Works on its own; pairs well with the official ServiceNow sources.** GlideGrail() is the
> judgment layer (how you want code written) and needs nothing else to be useful. When you
> want to go further, two official, free companions complement it:
> - [ServiceNow product docs in markdown](https://github.com/ServiceNow/ServiceNowDocs) (LLM-optimized) for authoritative, current platform behavior, and
> - [ServiceNow now-sdk agent skills](https://github.com/ServiceNow/sdk) for live Fluent/SDK mechanics when you're building with the ServiceNow SDK.

## 🚀 Quick start: add GlideGrail() to your AI tool

Grab [`SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md`](./SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md)
(clone the repo, or download the raw file) and wire it into whichever assistant you use.

### <img src="https://cdn.simpleicons.org/claude" width="20" align="center" alt=""/> Claude & Claude Code
**Claude (claude.ai / desktop / mobile):** attach [`SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md`](./SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md)
to a Project (so it grounds every chat in that Project), or upload it at the start of a
conversation and say *"Follow these ServiceNow standards in all code you write."*

**Claude Code:** place the file in (or near) your project and launch with it in context:
```bash
claude --add-dir /path/to/glidegrail
```
Or add a line to your project's `CLAUDE.md`: *"Follow SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md
for all ServiceNow code."* and it loads automatically every session.

### ChatGPT / Codex
Paste the [file's contents](./SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md) into a **Project's**
custom instructions (or a Custom GPT's knowledge), or attach the file at the start of a
coding session and instruct: *"Follow these ServiceNow standards in all code you write."*

### <img src="https://cdn.simpleicons.org/githubcopilot" width="20" align="center" alt=""/> GitHub Copilot
Add a `.github/copilot-instructions.md` to your repo that says to follow
[the standards file](./SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md), and keep the file in the
repo so Copilot's workspace context can read it.

### <img src="https://cdn.simpleicons.org/googlegemini" width="20" align="center" alt=""/> Gemini
Attach [the file](./SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md) (or paste it) into a **Gem's**
instructions, or include it at the top of your prompt/context for the session.

### <img src="https://cdn.simpleicons.org/cursor" width="20" align="center" alt=""/> Cursor
Add it as a project rule: drop [the file](./SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md) in
`.cursor/rules/` (or reference it from `.cursorrules`) so it's loaded into every request
automatically.

### Any other assistant
The pattern is identical everywhere: **load the markdown as context/system instruction, and
tell the model to follow it before generating ServiceNow code.** It's just a text file.

## What's inside

[`SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md`](./SERVICENOW_GLIDEGRAIL_CODING_STANDARDS.md)
covers, as enforceable conventions:

- **Naming**: tables, fields, Script Includes, Business Rules, variables, update sets,
  widgets (with a configurable `PREFIX`)
- **Server-side scripting**: GlideRecord/GlideAggregate patterns, Script Include structure,
  GlideAjax, constants, official-API preferences
- **Client-side**: UI Policies vs. Client Scripts, GlideForm, GlideAjax usage
- **Flow Designer**: flow/subflow structure, error handling, what belongs in a flow vs. a script
- **Data model & CMDB**: table design, references, CI conventions
- **Notifications, scheduled jobs, MRVS, system properties, logging** (a 3-tier logging
  convention), and **i18n/messages**

## Make it yours

These are strong, internally consistent defaults drawn from real ServiceNow development. `PREFIX` is engagement specific (use your client code, `SN`, or your own).
Fork it, disagree with it, adapt it to your team's house style. The value is that it's
consistent and complete enough to ground an agent out of the box, where your shop differs,
change the rule and keep going.

## Versioning

Tagged to the **Australia** release family. Conventions evolve with the platform, so if a
rule references a feature that's changed, open an issue or PR.

## License

Licensed under a [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Free to use, share, and adapt, including commercially, with attribution.

## Support

If GlideGrail() saves you time and/or you find it useful, you can
[buy me a coffee](https://buymeacoffee.com/bikemeardsley) ☕. Entirely optional, always
appreciated! Stars and PRs help just as much.

---

*Maintained by [Michael Beardsley](https://github.com/bikemeardsley). Built from real
ServiceNow development.*
