# 🏆GlideGrail.md
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00.svg?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/bikemeardsley)
[![ServiceNow docs.md](https://img.shields.io/badge/ServiceNow-docs.md-62D84E.svg?logo=servicenow&logoColor=white)](https://github.com/ServiceNow/ServiceNowDocs)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-blue.svg)](LICENSE)

#### *ServiceNow Coding Standards for Humans and AI Agents*

Most ServiceNow best practice material is scattered across community posts, docs, tribal
knowledge, or just not widely known, and written to be read by a human. GlideGrail.md consolidates years of experience and common rules
into a single reference written to be consumed by a model: concrete, directive, and
specific enough to change what your AI assistant (Claude, ChatGPT, Codex, Gemini, Copilot,
Cursor) actually produces.

Equally useful as a human reference or a review checklist.

## 🚀 Quick start

**Setting this up in your assistant?** See [USAGE.md](./USAGE.md) for step-by-step setup for every
tool (Claude, ChatGPT, Codex, GitHub Copilot, Cursor, Gemini), and which load method to use for
each.

The quickest installs:

**Claude Code / Claude desktop app** - install as a plugin:
```bash
/plugin marketplace add bikemeardsley/GlideGrail
/plugin install glidegrail@glidegrail
```
**Claude desktop app** - install as a plugin:

1. Open **Customize → Skills**.
2. Next to **Personal plugins**, click **+**.
3. Click **+ Create plugin**, then **Add marketplace**.
4. Paste `bikemeardsley/GlideGrail`, then click **Sync**.
5. Click **Install**.

**Gemini CLI** — install as an extension:
```bash
gemini extensions install https://github.com/bikemeardsley/GlideGrail
```

Every other tool loads the skill from [`skills/glidegrail/`](./skills/glidegrail/) (raw standards:
[`GlideGrail.md`](./skills/glidegrail/GlideGrail.md)) see [USAGE.md](./USAGE.md) for the steps.

## What's inside

[`GlideGrail.md`](./skills/glidegrail/GlideGrail.md) covers, as enforceable conventions:

| Area | Covers |
|---|---|
| 📐 **Ground rules & scope** | When an agent should confirm vs. build, scoped-app-first discipline, configuration over hardcoding (no hardcoded URLs or sys_ids), recognising and flagging technical debt before incurring it, code readability, and a "Do Not Use" table of banned patterns |
| 🏷️ **Naming** | Tables, fields, Script Includes, Business Rules, variables, update sets, and widgets — with a configurable `PREFIX` |
| ⚙️ **Server-side scripting** | GlideRecord / GlideAggregate patterns, GlideElement handling, Script Include structure, GlideAjax, constants, and performance at scale |
| 🖥️ **Client-side** | UI Policies vs. Client Scripts vs. Data Policies, GlideForm, GlideAjax, and UI Actions across classic forms and Workspaces |
| 🔄 **Automation** | Business Rules (timing, order, recursion guards), Events, Scheduled Jobs, and Flow Designer — what belongs in a flow vs. a script |
| 🔐 **Security** | ACL design, hardening, and debugging; integration user and data security |
| 🪵 **Logging, errors & ops** | A 3-tier logging convention, error-handling return contracts, and pre-go-live review routines (logs, queues) |
| 🗃️ **Data & migration** | Data model conventions — table/field/choice design (default vs. calculated vs. derived, state-field rules) and database views — plus CMDB, Import Sets & Transform Maps (staging-first), and Update Sets (promotion, fix scripts) |
| 🛒 **Catalog, platform UX & i18n** | Service Catalog (items vs. record producers), MRVS, attachments, system properties, notifications, messages/i18n, and UI Builder |
| 🎨 **Service Portal** | Widgets, AngularJS providers, server communication, client-side state, SCSS, BEM, accessibility (WCAG), and Moment.js i18n |
| 🔌 **Integrations** | Interface design and non-repudiation, Scripted REST APIs, IntegrationHub & custom spokes, OAuth 2.0, and LDAP user import |
| ✅ **Testing** | The Automated Test Framework — coverage expectations, suite hierarchy, reusable base tests, and running suites via the CI/CD API |

> **Works on its own; pairs well with the official ServiceNow sources.** GlideGrail.md is the
> judgment layer (how you want code written) and needs nothing else to be useful. When you
> want to go further, two official, free companions complement it:
> - [ServiceNow product docs in markdown](https://github.com/ServiceNow/ServiceNowDocs) (LLM-optimized) for authoritative, current platform behavior, and
> - [ServiceNow now-sdk agent skills](https://github.com/ServiceNow/sdk) for live Fluent/SDK mechanics when you're building with the ServiceNow SDK.

## License

Licensed under a [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
Free to use, share, and adapt, including commercially, with attribution.

## Support

If GlideGrail.md saves you time and/or you find it useful, please give this repo a Star. You can also sponsor the project by 
[buying me a coffee](https://buymeacoffee.com/bikemeardsley) ☕. Entirely optional, always
appreciated!

---

*Maintained by [Michael Beardsley](https://github.com/bikemeardsley). Built from real
ServiceNow development.*
