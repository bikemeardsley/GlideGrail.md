---
name: glidegrail-servicenow-standards
description: >-
  ServiceNow coding standards and conventions for humans and AI agents. Use this skill
  whenever writing, reviewing, or refactoring ServiceNow code or platform artifacts:
  GlideRecord/GlideAggregate queries, Script Includes, Business Rules, Client Scripts,
  UI Policies, GlideAjax, Flow Designer flows, ACLs, Service Catalog items and record
  producers, Service Portal widgets, Scripted REST APIs and integrations, notifications,
  scheduled jobs, MRVS, system properties, logging, or ATF tests. Covers naming
  conventions, server- and client-side patterns, security, and integration design.
---

# GlideGrail — ServiceNow Coding Standards

Before writing or reviewing any ServiceNow code, follow the conventions in **`GlideGrail.md`**
(alongside this file). It is the source of truth for how code should be written on this
platform.

When a task touches ServiceNow, consult `GlideGrail.md` for the specific rule rather than
relying on general knowledge — its API signatures and conventions are intentionally precise,
because wrong details get amplified into hallucinated code downstream. Apply the relevant
section (naming, GlideRecord patterns, Script Include structure, client-side rules, Flow
Designer, ACLs, integrations, logging, etc.) to whatever you produce, and prefer its guidance
over defaults when they differ.
