---
name: glidegrail
description: >-
  ServiceNow coding standards. Use whenever writing, reviewing, or refactoring ServiceNow
  code or config: GlideRecord, Script Includes, Business Rules, Client Scripts, UI Policies,
  GlideAjax, Flow Designer, ACLs, Service Catalog, Service Portal, REST and integrations, ATF.
---

# GlideGrail — ServiceNow Coding Standards

**`GlideGrail.md`** (alongside this file) is the source of truth for ServiceNow code. Its
API signatures and conventions are deliberately precise: take the rule from it, not from
general knowledge, and prefer it over your defaults when they differ.

It is about 47K tokens, so read only what the task needs:

1. **List its sections:** the `## ` headings with line numbers (e.g.
   `grep -n '^## ' GlideGrail.md`). Each section runs to the next `## ` heading.
2. **Always read** *Agent Ground Rules*, *Technical Debt* and *Do Not Use*. They apply to
   every task.
3. **Read the sections the task touches**, by line range: a Client Script task needs
   *Client Scripts*, *GlideForm* and *GlideAJAX*, not *ATF* or *LDAP*. A rule that links to
   another section (`[…](#anchor)`) and decides what you write: read that section too.

Read the whole file only for a broad review that spans most areas.
