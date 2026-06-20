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

Rules, not paragraphs, and equally useful as a human reference or a review checklist.

> **Works on its own; pairs well with the official ServiceNow sources.** GlideGrail.md is the
> judgment layer (how you want code written) and needs nothing else to be useful. When you
> want to go further, two official, free companions complement it:
> - [ServiceNow product docs in markdown](https://github.com/ServiceNow/ServiceNowDocs) (LLM-optimized) for authoritative, current platform behavior, and
> - [ServiceNow now-sdk agent skills](https://github.com/ServiceNow/sdk) for live Fluent/SDK mechanics when you're building with the ServiceNow SDK.

## 🚀 Quick start

GlideGrail ships as a **skill** — drop it into your AI tool and it loads automatically whenever
you're writing or reviewing ServiceNow code.

**Claude Code / Claude desktop app** — install as a plugin:
```bash
/plugin marketplace add bikemeardsley/GlideGrail
/plugin install glidegrail@glidegrail
```

**Gemini CLI** — install as an extension:
```bash
gemini extensions install https://github.com/bikemeardsley/GlideGrail
```

**Every other tool** — ChatGPT, Codex, GitHub Copilot, Cursor, Claude Projects,
and more — see **[USAGE.md](./USAGE.md)** for the per-tool setup: which load method to use
(skill, project knowledge, or always-on rules file) and why. The skill itself lives in
[`skills/glidegrail/`](./skills/glidegrail/); the raw standards are
[`GlideGrail.md`](./skills/glidegrail/GlideGrail.md).

## What's inside

[`GlideGrail.md`](./skills/glidegrail/GlideGrail.md)
covers, as enforceable conventions:

- **Ground rules & scope**: when an agent should stop and confirm vs. just build,
  scoped-app-first discipline, code readability, and a consolidated "Do Not Use" table of
  banned patterns
- **Naming**: tables, fields, Script Includes, Business Rules, variables, update sets,
  widgets (with a configurable `PREFIX`)
- **Server-side scripting**: GlideRecord/GlideAggregate patterns, GlideElement handling,
  Script Include structure, GlideAjax, constants, official-API preference, and performance
  at scale
- **Client-side**: UI Policies vs. Client Scripts vs. Data Policies, GlideForm, GlideAjax,
  and UI Actions across both classic forms and Workspaces
- **Automation**: Business Rules (timing, order, recursion guards), Events, Scheduled Jobs,
  and Flow Designer (flow/subflow structure, what belongs in a flow vs. a script)
- **Security**: ACLs (design, hardening, debugging) and integration user/data security
- **Logging, errors & operations**: a 3-tier logging convention, error-handling return
  contracts, and operational-hygiene review routines (logs, queues, pre-go-live checks)
- **Data & migration**: data model and CMDB conventions, Import Sets & Transform Maps
  (staging-first), and Update Sets (promotion discipline, fix scripts, XML data import)
- **Catalog, platform UX & i18n**: Service Catalog (items vs. record producers), MRVS,
  attachments, system properties, notifications, messages/i18n, and UI Builder (Next Experience)
- **Service Portal**: widgets, AngularJS providers, server communication, client-side state,
  SCSS, BEM styling conventions, accessibility (WCAG), and Moment.js i18n
- **Integrations**: interface design and non-repudiation, Scripted REST APIs, Integration
  Hub & custom spokes, OAuth 2.0, and LDAP user import
- **Testing**: the Automated Test Framework (ATF) — coverage expectations, suite hierarchy,
  reusable base tests, and running suites via the CI/CD API

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

If GlideGrail.md saves you time and/or you find it useful, you can
[buy me a coffee](https://buymeacoffee.com/bikemeardsley) ☕. Entirely optional, always
appreciated! Stars and PRs help just as much.

---

*Maintained by [Michael Beardsley](https://github.com/bikemeardsley). Built from real
ServiceNow development.*
