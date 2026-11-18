<!--
  GlideGrail AGENTS.md template — copy this file to the ROOT of your
  ServiceNow project repo. Codex, Cursor, Copilot, Cline, Junie, Zed, Jules, Devin, Amp, and most
  coding agents read AGENTS.md automatically. Replace <YOUR_PREFIX> below,
  and save a copy of GlideGrail.md at docs/GlideGrail.md (or change that
  path below). Delete this comment block after copying.
-->

# Agent instructions

## ServiceNow coding standards

All ServiceNow code and platform artifacts in this repository follow
**GlideGrail.md** — concrete, directive ServiceNow development standards.

Before writing, reviewing, or refactoring anything ServiceNow-related
(GlideRecord queries, Script Includes, Business Rules, Client Scripts,
UI Policies, Flow Designer, ACLs, Service Catalog, Service Portal widgets,
Scripted REST APIs, integrations, ATF tests, …):

1. **Read only the sections you need** from `docs/GlideGrail.md` (about 47K
   tokens in all). List its `## ` headings with line numbers; each section
   runs to the next one. Always read *Agent Ground Rules*, *Technical Debt*
   and *Do Not Use*, then the sections the task touches, by line range.
   No local copy? Fetch
   `https://raw.githubusercontent.com/bikemeardsley/GlideGrail.md/main/skills/glidegrail/GlideGrail.md`.
2. **Follow its rules over your defaults** when they differ, rather than
   relying on general knowledge.
3. **Substitute the `PREFIX` placeholder** in the naming conventions with this
   project's prefix: `<YOUR_PREFIX>`.
