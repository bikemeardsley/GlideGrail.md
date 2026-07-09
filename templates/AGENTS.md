<!--
  GlideGrail AGENTS.md template — copy this file to the ROOT of your
  ServiceNow project repo. Codex, Cursor, Zed, Jules, Devin, Amp, and most
  coding agents read AGENTS.md automatically. Replace <YOUR_PREFIX> below,
  and if you vendor a copy of GlideGrail.md in the repo, swap the URL for
  its local path. Delete this comment block after copying.
-->

# Agent instructions

## ServiceNow coding standards

All ServiceNow code and platform artifacts in this repository follow
**GlideGrail.md** — concrete, directive ServiceNow development standards.

Before writing, reviewing, or refactoring anything ServiceNow-related
(GlideRecord queries, Script Includes, Business Rules, Client Scripts,
UI Policies, Flow Designer, ACLs, Service Catalog, Service Portal widgets,
Scripted REST APIs, integrations, ATF tests, …):

1. **Load the standards** — fetch
   `https://raw.githubusercontent.com/bikemeardsley/GlideGrail.md/main/skills/glidegrail/GlideGrail.md`
   (or read the local copy if this repo vendors one).
2. **Follow its rules over your defaults** when they differ, and consult the
   specific section rather than relying on general knowledge.
3. **Substitute the `PREFIX` placeholder** in the naming conventions with this
   project's prefix: `<YOUR_PREFIX>`.
