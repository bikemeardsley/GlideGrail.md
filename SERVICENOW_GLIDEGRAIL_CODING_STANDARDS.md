# ServiceNow Development Standards

> Engagement-agnostic best practices for ServiceNow development.  
> PREFIX is engagement-specific: use the client prefix, `SN` (ServiceNow), or equivalent as appropriate per project.

> **Authoritative platform reference.** These standards capture *judgment and conventions*. For *current, authoritative platform behavior* (APIs, feature specifics, release changes), consult ServiceNow's official documentation published as markdown for LLM consumption: https://github.com/ServiceNow/ServiceNowDocs . If a rule here and the official docs ever conflict on a platform *fact*, the official docs win on facts; this doc governs style and conventions. Agents: check that repo for any feature detail you are unsure about before generating code.

---

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [General Coding Standards](#general-coding-standards)
3. [Code Readability](#code-readability)
4. [Official API Preference](#official-api-preference)
5. [System Properties](#system-properties)
6. [GlideRecord](#gliderecord)
7. [GlideForm](#glideform)
8. [GlideAJAX](#glideajax)
9. [Script Includes](#script-includes)
10. [UI Policies](#ui-policies)
11. [Business Rules](#business-rules)
12. [Client Scripts](#client-scripts)
13. [Access Control Lists (ACLs)](#access-control-lists-acls)
14. [Logging](#logging)
15. [Operational Hygiene](#operational-hygiene)
16. [Messages & i18n](#messages--i18n)
17. [Notifications](#notifications)
18. [Scheduled Jobs](#scheduled-jobs)
19. [Multi-row Variable Sets (MRVS)](#multi-row-variable-sets-mrvs)
20. [Service Catalog — Items & Record Producers](#service-catalog--items--record-producers)
21. [Update Sets](#update-sets)
22. [Flow Designer](#flow-designer)
23. [CMDB](#cmdb)
24. [UI Builder (Next Experience)](#ui-builder-next-experience)
25. [Service Portal — Widgets](#service-portal--widgets)
26. [Service Portal — AngularJS Providers](#service-portal--angularjs-providers)
27. [Service Portal — Server Communication](#service-portal--server-communication)
28. [Service Portal — SCSS](#service-portal--scss)
29. [Service Portal — Styling Conventions](#service-portal--styling-conventions)
30. [Service Portal — Accessibility (WCAG)](#service-portal--accessibility-wcag)
31. [Service Portal — Moment.js i18n](#service-portal--momentjs-i18n)
32. [Automated Test Framework (ATF)](#automated-test-framework-atf)
33. [Import Sets & Transform Maps](#import-sets--transform-maps)
34. [Integrations — General](#integrations--general)
35. [Integrations — Scripted REST API](#integrations--scripted-rest-api)
36. [Integrations — Integration Hub & Custom Spokes](#integrations--integration-hub--custom-spokes)
37. [Integrations — OAuth 2.0](#integrations--oauth-20)
38. [Integrations — LDAP User Import](#integrations--ldap-user-import)
39. [Integrations — Security](#integrations--security)

---

## Naming Conventions

| Artifact | Convention | Example |
|---|---|---|
| PREFIX | Engagement-specific | `SN` or your client prefix |
| Tables | `snake_case` singular | `my_asset` |
| Fields | `snake_case` | `assigned_group` |
| Script Includes | `PascalCase` | `IncidentService`, `IncidentServiceAjax` |
| Business Rules / Client Scripts | `PREFIX - Description` | `SN - Set Priority on Create` |
| Functions / variables | `camelCase` with type hint | `incidentGr`, `membersArr` |
| Constants | `UPPERCASE_SNAKE` | `MAX_RETRY_COUNT` |
| Widget name | Title Case | `My Task Board` |
| Widget ID | `kebab-case` | `my-task-board` |
| Update sets | `PREFIX - STRY# - Description #00N` | `SN - STRY001 - Incident Form Changes #001` |

---

## General Coding Standards

- Use `getUniqueValue()` for the current record's sys_id; `getValue('field')` for reference field sys_ids
- Never dot-walk sys_ids — dot-walking a field returns a `GlideElement` object, not a string value
- Server-side array iteration: `map` / `filter` / `reduce` / `sort` only; `while` for `.next()` loops; never `forEach` server-side
- Constants Script Include: use `Object.freeze`, `UPPER_CASE` for category keys, `lower_snake_case` for values
- Use `GlideDateTime` server-side; pass Unix ms timestamps to the client
- Use `GlideRecordSecure` for any Script Include callable from the client side
- Widget server scripts must delegate all business logic to Script Includes — no logic directly in the widget
- Wrap single-context scripts (transform map scripts, background scripts, ad-hoc scripts) in a self-executing function `(function() { ... })();` to prevent global scope leakage. Business Rules and Client Scripts are already wrapped by the platform default — keep the default wrapper intact.
- Prefer `getDisplayValue()` over hardcoded display field names (`gr.cmdb_ci.getDisplayValue()` instead of `gr.cmdb_ci.name`) so code survives dictionary display-field changes.

---

## Code Readability

Code is read far more often than it is written. Write for the next person on the team.

### JSDoc Headers on Functions

Every Script Include method and every non-trivial standalone function gets a JSDoc-style header. At minimum, describe the purpose, parameters (with types), and return value (with type). Keep headers accurate — an outdated comment is worse than none.

```javascript
/**
 * addGlideListElement — add a sys_id to a comma-separated glide_list field value
 *
 * @param {string} currentValue - existing comma-separated list (may be empty)
 * @param {string} id - sys_id to add if not already present
 * @return {string} updated comma-separated list
 */
addGlideListElement: function(currentValue, id) { /* ... */ }
```

### Meaningful Inline Comments

- Comment the **why**, not the **what** — the code already shows what it does
- Remove stale comments during code review; a wrong comment is a trap
- `// Set i to 0` is noise; `// Walk backwards so deleteRecord() doesn't skip rows` is signal

### Whitespace and Structure

- Use blank lines to separate logical blocks within a function
- Put spaces around operators and after commas
- Group related variable declarations together
- Use the ServiceNow script editor's Format Code button before saving

### Descriptive Variable and Function Names

Variable and function names should make the code self-documenting.

```javascript
// ❌ BAD — cryptic
function del(r, d, s) { /* ... */ }

// ✅ GOOD — intent is clear from the signature
function deleteIfCanceled(taskGr, defaultAnswer, stateValue) { /* ... */ }
```

Short loop counters (`i`, `j`) are fine. One- or two-letter names for anything else are not.

### Cache Repeated Function Results

If a function returns the same value throughout a code block, call it once and store the result. This improves both readability and performance.

```javascript
// ❌ BAD — four identical calls
if (gs.getUserID() == currentRec.getValue('assigned_to') ||
    gs.getUserID() == currentRec.getValue('u_coordinator') ||
    gs.getUserID() == currentRec.getValue('caller_id') ||
    gs.getUserID() == currentRec.caller_id.manager.toString()) { /* ... */ }

// ✅ GOOD — single call, named intermediates
var currentUserId = gs.getUserID();
var isOwner       = currentUserId == currentRec.getValue('assigned_to');
var isCoordinator = currentUserId == currentRec.getValue('u_coordinator');
var isCaller      = currentUserId == currentRec.getValue('caller_id');
var isCallerMgr   = currentUserId == currentRec.caller_id.manager.toString();

if (isOwner || isCoordinator || isCaller || isCallerMgr) { /* ... */ }
```

### Return Values from Functions

Functions that perform work should return a value the caller can check — a count, a boolean, an object, or `null`/`false` on failure. This makes error handling possible without reading the function body.

```javascript
/**
 * @return {boolean} true on successful save, false otherwise
 */
function saveRecord(gr) {
    var sysId = gr.update();
    return !gs.nil(sysId);
}

if (!saveRecord(currentRec)) {
    gs.addErrorMessage(gs.getMessage('record.save_failed'));
}
```

### Guard Against Undefined Values Before Use

Dot-walking through empty references, reading `vaVars` that may be coerced to `"null"`, or accessing fields that may not exist will produce unpredictable results and warning messages. Check before you use.

```javascript
// ❌ BAD — throws warnings if cmdb_ci or installed_on is empty
var tableName = current.cmdb_ci.installed_on.sys_class_name;

// ✅ GOOD — guard first
var tableName = current.cmdb_ci.installed_on.getValue('sys_class_name');
if (tableName) {
    // safe to use
} else {
    gs.warn('[MyBR] sys_class_name unavailable for ' + current.getDisplayValue());
}
```

**vaVars gotcha:** null values in `vaVars` can be coerced to the string `"null"`. Use truthy checks, not `== null` or `== ''` comparisons.

### Avoid `eval()`

Never use `eval()`. It opens the door to injection, makes debugging harder (no line numbers in errors), and has no legitimate use case that can't be solved another way.

### Avoid Dynamic JEXL in Jelly `<g:evaluate>`

(Applies to UI Pages, legacy CMS, classic portal — rare in modern builds but called out here for completeness.)

Never embed Jelly variables directly inside `<g:evaluate>` using `${jvar_name}` syntax — this affects the JVM's PermGen memory and can cause outages over time. Instead, set `jelly="true"` on the evaluate tag and reference variables via the `jelly.` prefix.

```xml
<!-- ❌ BAD -->
<g:evaluate>
    var gr = new GlideRecord('incident');
    gr.addQuery('assigned_to', '${jvar_userid}');
</g:evaluate>

<!-- ✅ GOOD -->
<g:evaluate jelly="true">
    var gr = new GlideRecord('incident');
    gr.addQuery('assigned_to', jelly.jvar_userid);
</g:evaluate>
```

---

## Official API Preference

**Principle: Prefer official ServiceNow APIs over direct property access for writes and semantic checks.**

Official platform methods are the supported, documented contract. Direct property access bypasses the `GlideElement` getter/setter layer and can misbehave on journal, reference, currency, encrypted, and custom-typed fields — silently producing wrong values, malformed audit entries, or upgrade-breaking behaviour. Documented methods are also clearer in intent: `gs.nil(x)` reads as a null check; `x == null || x == ''` reads as a string comparison and obscures what the code is actually testing.

### Apply this rule

| Use this | …instead of this | Why |
|---|---|---|
| `current.setValue('field', value)` | `current.field = value` | `setValue` goes through the field's typed setter — required for correct handling of journals, references, currency, encrypted, and custom field types |
| `current.getValue('field')` | `current.field.toString()`, `current.field + ''` | Returns the underlying string value directly; no coercion games |
| `current.getDisplayValue('field')` | `current.field.getDisplayValue()` *(acceptable)* / manual concatenation | Both are official; `getDisplayValue('field')` is the more direct form |
| `current.field.changes()` *(in Business Rules)* | `current.field != previous.field` | `changes()` is the documented BR API — handles type quirks, only available where `previous` exists (before/after BRs) |
| `gs.nil(value)` | `value == null \|\| value == ''` | Single documented null/empty check; correct for `GlideElement`, `String`, `null`, `undefined`, and empty values |
| `GlideAggregate` | manual `while (gr.next()) { count++ }` / loop summing | Aggregation is computed in the database; no per-row Java object instantiation |
| `gs.getUserID()`, `gs.getUserName()`, `gs.hasRole('admin')` | `new GlideRecord('sys_user').addQuery('sys_id', …)` for the current user | Documented session API; no query overhead; respects impersonation correctly |
| Documented level-aware logging APIs — see [Logging](#logging) for the tiered hierarchy | `gs.log()` for permanent code | `gs.log()` has no level and is hard to filter at scale; level-aware APIs are filterable by level and source |

### What this rule does NOT cover

The principle targets writes and semantic checks. The following are explicitly fine and should keep being used:

- **Dot-walking for reads** — `current.assigned_to.email`, `current.cmdb_ci.support_group.name` is officially supported, idiomatic, and the right tool for reading values through a reference chain
- **Direct `GlideElement` comparisons in conditions** — `if (current.state == 6)`, `if (current.priority < 3)` is fine; the `GlideElement` coerces to its value for comparison
- **`gs.getProperty('name', 'default')`** — this is *already* the official API for reading system properties; no change needed
- **Reading sys_id** — keep using `current.getUniqueValue()` (current record) and `current.getValue('reference_field')` (reference field sys_id); never dot-walk a sys_id, as documented in [General Coding Standards](#general-coding-standards)

### Client-side equivalent

The same principle applies in the browser:

- `g_form.setValue('field', value)`, `g_form.getValue('field')`, `g_form.getDisplayValue('field')` — never reach for the DOM
- This reinforces (and shares enforcement with) the **no DOM manipulation** rule under [Client Scripts → Core Rules](#client-scripts), which already bans `document.getElementById()`, jQuery, and direct DOM access

### Why this matters in practice

- **Upgrade safety** — ServiceNow can change the internal representation of a field type between releases; the documented setter/getter is the stable contract
- **Audit and journal correctness** — `current.work_notes = 'x'` and `current.setValue('work_notes', 'x')` do not always produce the same audit entry on journal-input fields
- **Reference-field hygiene** — `current.assigned_to = userGr` (passing a `GlideRecord`) silently coerces in ways that differ from `setValue('assigned_to', userGr.getUniqueValue())` and can break on upgrade
- **Reviewability** — the principle makes intent explicit at the call site, which is the single biggest factor in code-review speed for ServiceNow scripts

---

## System Properties

Use `sys_properties` for configuration values. Never hardcode values in scripts — use system properties to keep functionality dynamic and flexible.

**Use System Properties when:**
- A setting is configured once and rarely changed (no more than 1–2 times a month)
- There is only one instance of the setting per application install

**Use User Preferences when:**
- A setting is personalized per user
- There is a global default but individual users can override it

**Use an Application Settings table when:**
- Multiple instances of the same setting exist (e.g. per-board configuration)
- Settings are unrelated to user context but need to vary per object/record
- The number of settings or their values cannot be determined upfront

> ❌ Do not use `sys_properties` if values are dynamic, per-object, or vary across multiple app instances — use a dedicated configuration table instead.

---

## GlideRecord

**General rules:**
- Use `getValue('field')` to extract field values — dot-walking returns a `GlideElement` object, not the value
- Variable naming: `descriptiveNameGr` e.g. `incidentGr`
- Never nest GlideRecord queries inside other GlideRecord loops — use hash maps or join queries

**Query efficiency:**
- Use `addEncodedQuery()` for complex queries instead of chaining `addQuery()` / `addOrCondition()`
- Use `GlideAggregate` for counting records — not `getRowCount()` (getRowCount retrieves all records first, causing performance issues at scale)
- Use `setLimit(1)` when only confirming existence — this tells the database to stop after one match instead of returning and counting the whole result set:
  ```javascript
  // ❌ BAD — retrieves every active incident just to check one exists
  var incGr = new GlideRecord('incident');
  incGr.addQuery('active', true);
  incGr.query();
  if (incGr.hasNext()) { /* ... */ }

  // ✅ GOOD — database returns at most one row
  var incGr = new GlideRecord('incident');
  incGr.addQuery('active', true);
  incGr.setLimit(1);
  incGr.query();
  if (incGr.hasNext()) { /* ... */ }
  ```
- Use `addJoinQuery()` instead of nesting a GlideRecord inside another GlideRecord loop
- Use Related List Query (RLQUERY) when filtering by a specific count of related records — `addJoinQuery()` can only test for existence (≥1), not exact counts

**Always test queries on a sub-production instance before deploying to production.** An invalid encoded query silently drops the invalid condition and may return all records — running `update()`, `deleteRecord()`, or `deleteMultiple()` on that result can cause data loss.

**Active field vs. state field:**
- When determining whether a record is open or closed, query the `active` field — not individual state values. This leverages ServiceNow's OOB state-to-active mapping configured per table, keeping scripts resilient to state value changes.
- Only query specific `state` values when the business logic requires a particular state (e.g. "In Progress" vs "On Hold"), not for simple open/closed checks.
- If the target table does not have an `active` field, then fall back to state value checks.
```javascript
// ✅ GOOD — open vs. closed check
interactionGr.addQuery('active', true);

// ❌ BAD — hardcoding state values for a simple open/closed check
interactionGr.addQuery('state', '!=', '7');
interactionGr.addQuery('state', 'NOT IN', '3,7,8');

// ✅ OK — querying a specific state for business logic
incidentGr.addQuery('state', '2'); // Need specifically "In Progress"
```
---

## GlideForm

- Client-side only — always accessed via the global `g_form` object
- Never use `g_form` in UI Policies — use a Client Script if scripting is required

### setValue on Reference Fields

When setting a reference field with `g_form.setValue()`, **always pass the display value as the third argument**. Omitting it forces a synchronous AJAX round-trip to the server to fetch the display value, blocking the browser.

```javascript
// ❌ BAD — synchronous server call to fetch display value
g_form.setValue('assigned_to', userSysId);

// ✅ GOOD — no server call needed
g_form.setValue('assigned_to', userSysId, userDisplayName);
```

When the display value isn't known client-side, retrieve both via a single GlideAJAX call and set them together in the callback.

---

## GlideAJAX

**Choose the right pattern by trigger:**

| Trigger | Preferred approach |
|---|---|
| `onChange` (field change) | GlideAJAX |
| `onLoad` (before record loads) | Display Business Rule + `g_scratchpad` (not available in Service Portal) |
| After save | Business Rule or Flow |

**Avoid:**
- `getReference()` with callback — not preferred
- GlideRecord with callback — not preferred
- `getReference()` without callback — **very bad practice** (synchronous, blocks the browser)
- GlideRecord without callback — **very bad practice** (synchronous, blocks the browser)

**Implementation rules:**
- Client side: always use `getXMLAnswer()` + `JSON.parse()` to handle the response
- Max 1 AJAX call per client script
- For Service Catalog, always use GlideAJAX — there is no table on which to trigger Business Rules

---

## Script Includes

- Must be a **class**, not a standalone function
- Avoid generic names (e.g. `AbcUtils`) — name reflects the target table or responsibility
- No `eval`; no hardcoded sys_ids
- Single responsibility — separate functions for reusability across server-side components

**Server-side SI:**
- One SI per target table
- Named `[PREFIX][TargetTable]Service` e.g. `SNIncidentService`

**AJAX SI:**
- Named `[PREFIX][TargetTable]ServiceAjax` e.g. `SNIncidentServiceAjax`
- Extends `AbstractAjaxProcessor`
- No `initialize()` method
- Thin wrapper only — delegates all logic to the corresponding server-side SI
- Returns JSON, not plain strings
- Always `stringify(getParameter('param_name'))` when reading AJAX params

---

## UI Policies

- **Prefer UI Policies over Client Scripts** for controlling field visibility, mandatory state, and read-only state
- If scripting is required, use a **Client Script** instead of a UI Policy — **except** for simple date/time validations (see below)
- Use a single UI Policy for initialization
- Bundle multiple field actions into a single UI Policy where possible
- Mandatory fields **cannot** be hidden
- Mandatory fields **cannot** be made read-only

**Date/Time validation exception:**
Simple date/time validations in record producers or catalog items may use a UI Policy with a scripted message, because handling timezone and user format correctly in a Client Script is complex. Acceptable validations:
- Date/time is before or after another date/time
- Date/time is N days from now
- Date/time is older than N hours

**Catalog UI Policies:**
- Set the *When to apply* checkboxes correctly — determine whether the policy should run on the catalog item, the target record, or both

---

## Business Rules

Business Rules execute server-side logic in response to database operations. They are one of the most powerful — and most commonly misused — features on the platform.

### When to Use (and When Not To)

| Need | Use | Don't use |
|---|---|---|
| Set field values before a record is saved | Before BR | After BR (value is already committed) |
| React to a record change — user needs the result reflected immediately | After BR | Async BR (user may see stale state) |
| React to a record change — result is non-urgent (metrics, SLAs, external calls, notifications, logging) | Async BR | After BR (blocks the transaction) |
| Display data to a form before it loads | Display BR + `g_scratchpad` | After BR |
| Complex multi-step automation | Flow Designer | Business Rule |
| Client-side field control (show/hide, mandatory) | UI Policy or Client Script | Business Rule |

**Async BR decision rule:** if the user needs to see the side-effect in the next page render (e.g. a related record shown in a form), use After. If the side-effect can complete seconds later without the user noticing (metrics, SLA calculations, outbound REST, email events), use Async — it returns control to the user faster and won't hold up the transaction.

### Timing and Order

- **Before** — runs before the record is written to the database; use for validation, field defaulting, and field calculation
- **After** — runs after the record is committed; use for side-effects (creating related records, sending events, logging)
- **Async** — runs after the record is committed, on a separate thread; use for work that does not need to complete before the user sees the result (e.g. external callouts, heavy processing)
- **Display** — runs when a form loads (not on list views); use exclusively to populate `g_scratchpad` for client-side consumption; not available in Service Portal

**Execution order within the same timing:** controlled by the `Order` field (default 100). Lower numbers run first. Avoid relying on execution order between independent BRs — if order matters, consolidate into one BR or use events.

### Core Rules

- **Never call `current.update()` inside a before BR** — the record is about to be saved anyway; calling `current.update()` triggers a second save and can cause infinite recursion
- **Keep BRs lean** — delegate all non-trivial logic to a Script Include; the BR itself should be a thin wrapper (condition check + SI call)
- **One BR per concern** — do not pack unrelated logic into a single BR; this makes conditions unmanageable and debugging difficult
- **Always set conditions** — never leave the condition blank (fires on every operation on the table); use both the condition field and a script condition where appropriate
- **Filter by operation** — check only the operations (insert, update, delete, query) the BR actually needs
- **Avoid `current.setWorkflow(false)`** unless you have a specific, documented reason — it suppresses all subsequent BRs, flows, and notifications for that transaction
- **Use `current.operation()` checks** in combination BRs that fire on both insert and update, to differentiate behaviour

### Preventing Recursive / Runaway BRs

- If an after BR updates the same record, it re-triggers before/after BRs on that table — guard with `current.update()` avoidance or a recursion flag (`gs.getSession().putClientData()` or a script-scoped variable)
- For bi-directional integrations, filter out updates by the integration user (see the Integrations — General section on loop prevention)
- Never modify `current` inside an **after** BR — changes are silently lost because the record is already committed; if you need to update the same record, use `GlideRecord` with `setWorkflow(false)` and `autoSysFields(false)` and accept the trade-offs

### Naming

Follow the standard: `PREFIX - Description` (e.g. `SN - Set Priority on Create`). Include the timing in the description if it aids clarity (e.g. `SN - Before - Validate Mandatory Fields`).

---

## Client Scripts

Client Scripts run in the user's browser and control the form experience. They are the primary mechanism for client-side logic that goes beyond what UI Policies can handle declaratively.

### Types and When to Use

| Type | Fires when | Use for |
|---|---|---|
| **onLoad** | Form loads | Setting initial field states, populating dynamic defaults, configuring the form based on server data (via `g_scratchpad` from a Display BR) |
| **onChange** | A specific field value changes | Reacting to user input — fetching related data (via GlideAJAX), showing/hiding sections, setting dependent field values |
| **onSubmit** | User clicks Save / Update / Submit | Final validation before the record is saved — return `false` to cancel the save |
| **onCellEdit** | Inline list editing | Validating or reacting to changes made directly on a list view |

### Core Rules

- **No synchronous server calls** — never use `getReference()` or `GlideRecord` without a callback; these block the browser thread and degrade the user experience. Use **GlideAJAX** with `getXMLAnswer()` for all server-side data retrieval
- **Max 1 GlideAJAX call per Client Script** — if you need multiple pieces of server-side data, consolidate into a single AJAX SI that returns everything in one JSON response
- **Wrap in an IIFE** when variable scoping is a concern — prevents naming collisions with other Client Scripts on the same form:
  ```javascript
  (function() {
      // your code here
  })();
  ```
- **Prefer UI Policies** for simple show/hide, mandatory, and read-only control — only use a Client Script when scripting logic is required
- **Avoid `g_form.getReference()`** — it is either synchronous (very bad) or callback-based but still less efficient than GlideAJAX; GlideAJAX is always preferred
- **Minimise DOM manipulation** — do not use `document.getElementById()`, `jQuery`, or direct DOM access; use the `g_form` API exclusively. Direct DOM manipulation breaks on form redesigns, is not supported in Service Portal, and can be overwritten by the platform at any time

### Service Portal Considerations

- `g_scratchpad` (from Display BRs) is **not available** in Service Portal — use GlideAJAX or widget server scripts instead
- `onCellEdit` Client Scripts do not apply in Service Portal
- Test all Client Scripts in both the standard UI and Service Portal if both are in use

### Performance

- Client Scripts run on every form load/change for their table — keep them fast
- If an onChange script calls GlideAJAX, consider debouncing or guarding against rapid consecutive changes (e.g. check if the value actually changed before making the call)
- Use the **Applies to** field (Desktop, Mobile, or Both) to avoid running desktop-only logic on mobile devices

### Naming

Follow the standard: `PREFIX - Description` (e.g. `SN - onChange - Set Category from Assignment Group`). Including the type in the name makes the Client Script list easier to scan.

---

## Access Control Lists (ACLs)

ACLs are the primary mechanism for securing data in ServiceNow. Every table and field that stores sensitive or restricted data must have explicit ACL rules.

### How ACL Evaluation Works

ServiceNow evaluates ACLs in order from most specific to least specific: **field-level → table-level → table wildcard (`table.*`)**. The system looks for a matching rule at each level and stops at the first match. If **no ACL exists** for a given operation on a table, access is granted by default (unless the `glide.sm.default_mode` property is set to `deny`) — this means a missing ACL is effectively an open door.

### Design Principles

- **Least privilege** — start restrictive and grant access explicitly; do not rely on the absence of deny rules
- **Row-level filtering** — use `before` query Business Rules (addEncodedQuery on the current query) to restrict which records a user can see, rather than relying solely on ACLs for row-level security; ACLs control table/field access, BRs control record-level visibility
- **Field-level ACLs** — use sparingly and only for genuinely sensitive fields (e.g. SSN, salary); they add evaluation overhead on every form load and list render
- **Avoid overly broad roles in ACLs** — granting `itil` access to a custom table means every ITSM agent can read/write it; create custom roles scoped to the application
- **Script conditions in ACLs** — use only when role-based and condition-based rules are insufficient; script conditions are harder to audit and slower to evaluate
- **Test as the target persona** — impersonate a user with the intended role and verify they can only see and do what the design specifies; test both the happy path (access works) and the negative path (restricted data is hidden)

### Common Patterns

**Standard CRUD ACLs for a custom table:**

| Operation | Typical approach |
|---|---|
| Read | Role-based (e.g. `x_prefix.table.reader`) |
| Create | Stricter role (e.g. `x_prefix.table.editor`) |
| Write | Same as create, or more restrictive; consider field-level ACLs for sensitive fields |
| Delete | Most restrictive — often limited to admin or a dedicated role; many tables should not allow deletes at all |

**Protecting reference fields:**
When a reference field points to a restricted table, the ACL on the referenced table controls whether the user can see the display value. If users need to see the display value but not access the referenced table directly, use a **before** query BR or a display-only field populated server-side.

### ACLs in Scoped Applications

- Scoped apps should define their own roles and ACLs within the app scope
- Cross-scope ACLs (granting access to tables in another scope) require careful planning — prefer exposing data via a Script Include or Scripted REST API rather than opening ACLs across scopes
- When creating ACLs in a scoped app, ensure the ACL record is captured in the correct update set / app scope

### Debugging ACLs

- Use the **Security Diagnostics** page (`sys_security.do`) to evaluate ACL decisions for a specific user, table, and operation
- Enable the **ACL debugging** session property to see which ACLs are evaluated and their results in the system log
- Check for **conflicting ACLs** — if multiple rules match, the most specific wins; if two rules at the same specificity conflict, the most restrictive wins

> ⚠️ Elevating to `security_admin` is required to create, modify, or delete ACL rules. Always test ACL changes on a sub-production instance first.

---

## Logging

Logging discipline matters more than the specific API. Pick the right tier for the environment, attach a useful source to every message, write at the right level, and make every message traceable to the artifact that produced it.

### Which API to use

| Tier | When | Pattern |
|---|---|---|
| 1 — Project logger | An engagement-deployed logger (e.g. `GSLog`) is available on the target instance | `this.log = new GSLog('com.prefix.module', this.type); this.log.info(…)` |
| 2 — Platform default | No project logger is deployed — most personal dev instances, fresh customer instances, ServiceNow internal | `gs.info(msg, source)` / `gs.warn(msg, source)` / `gs.error(msg, source)` for permanent logging; `gs.debug(msg, source)` for trace-level diagnostics that stay in code |
| 3 — Temporary debug | Active debugging that gets removed before release | `gs.log(msg, 'recognisable-source')` — search-and-destroy before go-live |

Check the project's knowledge / setup notes for whether a project logger is deployed. If unclear, default to Tier 2 — the scoped `GlideSystem` logging methods are documented platform APIs with proper level support, not a sad fallback.

**VA topic scripts:** `GSLog` is not available inside Virtual Agent topic script nodes. Use the Tier 2 platform methods (`gs.info()` / `gs.warn()` / `gs.error()`) directly.

### Source string — required, always

Every permanent log call must pass an explicit source string that identifies the artifact producing the log, so filtering syslog by source jumps straight to the originating code. Convention: use the artifact's name as it exists in ServiceNow.

| Artifact | Source string |
|---|---|
| Script Include | The class name — e.g. `'SNIncidentService'` |
| Business Rule | The BR's full name — e.g. `'SN - Before - Set Priority on Create'` |
| Scheduled Job | The job name |
| Scripted REST API | The resource path or operation name |
| Mail Script | `'mail_script:<name>'` |
| UI Action | The UI Action name |
| Background Script | A descriptive identifier including a date stamp |

In scoped apps the platform auto-attaches scope and script name to log entries, but pass an explicit source anyway — it keeps log analysis consistent across global-scope code and makes per-artifact filtering trivial in syslog.

### Inline prefix in the message body

In addition to the source string, prefix every log message body with the artifact name in square brackets — e.g. `[Update Interaction]`, `[SN - Set Priority on Create]`. This keeps messages self-describing when read inline (without the source column) and supports a single `messageLIKE[Prefix Name]` filter in syslog.

- Never use `*` or `***` in the prefix — `*` is the ServiceNow search wildcard character and breaks syslog filtering
- Keep prefixes consistent across all log lines from the same script

### Log levels

| Level | When to use | Tier 2 API |
|---|---|---|
| Error | Critical failures only | `gs.error()` |
| Warning | Unexpected but non-fatal behaviour | `gs.warn()` |
| Info | Valuable, expected behaviour worth recording | `gs.info()` |
| Debug | Step-by-step trace; only emits when scope debug is enabled | `gs.debug()` |

`gs.debug()` is the right home for permanent trace-level diagnostics — it stays in the code but only emits when an admin flips the scope's debug flag, so it costs nothing in production. Don't confuse it with Tier 3 temp debug.

### Message content

Every log message includes: **what happened / when / where / how / who** + record or event correlation. Include record identifiers (number, sys_id) so syslog entries can be traced back to the originating record. No vague messages like `"Error occurred"`. Use parameter substitution where supported — e.g. `gs.info('Updated {0} records in {1}ms', count, elapsed)` — both for readability and to avoid the cost of string concatenation when the level is filtered out.

```javascript
// ✅ GOOD
gs.info('[Update Interaction] Updating interaction: ' + interactionGR.getValue('number'), 'SNInteractionService');
gs.error('[VA Topic Switch] Failed to switch topic: ' + e, 'VA - Topic Switch');

// ❌ BAD — wildcard characters in prefix
gs.info('*** Update Interaction *** Updating interaction: ' + interactionGR.getValue('number'));

// ❌ BAD — no context
gs.info('Record updated');
```

### Error surfacing

Wrap risky operations (REST calls, GlideRecord operations that may fail ACLs, parse/math operations on untrusted input) in `try/catch` and log the caught error at error level with the exception message and stack where available. Never let exceptions fail silently.

### Before go-live

- Remove all Tier 3 `gs.log()` temp-debug calls
- Remove all `console.log()` calls (these end up in browser console anyway, never in syslog)
- Confirm Tier 1/2 calls are at the right level — not everything at `info`
- Confirm every permanent log call has an explicit source string and inline `[Prefix]`

---

## Operational Hygiene

Review logs and queues regularly throughout development — not just at go-live. Waiting until the end makes root cause analysis much harder.

### Log Review

Check these locations frequently during active development:

| Location | What to look for |
|---|---|
| **System Logs → Errors** | Every entry should be corrected or documented as a known issue |
| **System Logs → Warnings** | Same standard as errors — don't normalize warnings |
| **System Logs → All** (filter: Level is Warning or Error) | Consolidated view; sort by Created desc and add the Created By column |
| **System Diagnostics → Slow Queries** | Queries exceeding 1000ms total execution time — investigate any entries tied to your code |
| **System Logs → Node Log File Browser** | Search for: `Slow evaluate`, `Slow Business Rule`, `Recursive Business Rule`, `Compiler exception`, `Warning - large table limit`, `Extremely large result` |

### Queue Review

| Queue | What to check |
|---|---|
| **System Mailboxes → Outbox / Inbox / Junk** | Stuck emails, bounced deliveries, unprocessed inbound |
| **ECC → Queue** (Queue = output, State = ready) | Records older than ~4 minutes indicate MID Server issue |
| **System Policy → Events → Event Log** | Sort by Processing Duration desc; events >1000ms warrant investigation. Check Processed-is-empty count — a growing backlog indicates the event processor is falling behind |

### Removing Unused Events

If a Business Rule fires `gs.eventQueue()` for an event name that has no active notification or script action listening, every insert/update is logging an event for nothing. On large imports this balloons the event log and wastes processing capacity. Either wire up the listener or remove the `eventQueue` call.

Right-click the Name column on the Events Log and **Group by Name** to quickly see which events have the highest counts, then check whether each one has a responder.

### Pre-Go-Live Review

Before closing out an update set or promoting to production, in addition to the logging cleanup items in the [Logging](#logging) section:

- System Logs error/warning count reviewed for the dev window; each entry either fixed or documented
- Slow Queries log checked for entries attributable to new code
- Event log checked for orphaned events (high count, no processor) from newly added `gs.eventQueue()` calls
- ECC Queue reviewed for stuck records if any MID Server integration was touched

---

## Messages & i18n

- All user-facing messages must be translate-ready via `sys_ui_message`
- Skip for: log messages, troubleshooting output, integration payloads

**Key format:** `prefix.subcategory.description`
- All lowercase
- `_` to join words within a segment
- `.` as subcategory separator
- Prefixed with engagement PREFIX
- Abstract-to-specific ordering

> Example: `prefix.incident.incident_created`

**By context:**

| Context | How to use |
|---|---|
| Server-side | `gs.getMessage('key')` |
| Client Script | Populate the *Messages* field on the script record + `getMessage('key')` in code; async fallback if Messages field unavailable |
| Widget | `gs.getMessage()` in server script; `{{key}}` in HTML for static text |

---

## Notifications

Three-layer structure — never collapse these into one:

1. **Email Layout** — header, footer, and styling only; no complex scripting
2. **Email Template** — reusable body content; no header/footer; **never rename** a template after it has been used
3. **Notification** — trigger conditions, recipients, and any content specific to this notification

**Rules:**
- No hardcoded instance URLs — use the instance suffix only
- Recipients via groups or user fields on the record — not hardcoded specific users
- Always assign a category
- Mail scripts are called via `${mail_script:name}` — spaces in the name will cause the call to silently fail
- Set *Send to event creator* = `FALSE` unless explicitly required

---

## Scheduled Jobs

- Clear the `run_as` field unless a specific user context is genuinely required (defaults to the creating user, which is often wrong)
- Use the **"Force to Update Set"** UI action to capture scheduled jobs in update sets (reliable on Madrid+)
- Max ~5 lines of code in the job itself — delegate all logic to a Script Include
- For user-facing scheduled tasks, prefer a **Flow Designer scheduled flow**; use Scheduled Jobs for core application/platform automation

---

## Multi-row Variable Sets (MRVS)

- Access MRVS data via `ritmGr.variables[multiRowInternalName]` — returns a multi-row object
- Iterate using `.getRowCount()` and `.getRow(i)`
- Extract individual field values using `String(row[fieldName])`
- MRVS data is available on `sc_req_item` records after submission

---

## Service Catalog — Items & Record Producers

### Catalog Item vs. Record Producer

| Use | Artifact |
|---|---|
| User requests a service or product (hardware, software, access) and a fulfillment workflow is needed | **Catalog Item** → creates `sc_req_item` (and parent `sc_request`) |
| User needs to create a record on a specific table directly (e.g. submit an incident, create a change) | **Record Producer** → creates a record on the target table |

Do not use a Catalog Item when a Record Producer would be more direct, and vice versa. If the request needs approval, task generation, or multi-step fulfillment, a Catalog Item is almost always the right choice.

### Variable Design

- **Naming:** `snake_case`, descriptive, prefixed with the engagement prefix if in a shared catalog (e.g. `sn_requested_for`, `sn_business_justification`)
- **Order:** set the `Order` field on every variable to control form layout explicitly — do not rely on creation order
- **Types:** use the most specific variable type available (Reference, Date, Checkbox, Select Box) rather than defaulting to Single Line Text — this gives you free validation and a better user experience
- **Mandatory variables:** mark truly required fields as mandatory on the variable, not via a Catalog Client Script — declarative is always preferred
- **Help text:** populate the `Tooltip` and/or `Help tag` on every variable that is not self-explanatory
- **Default values:** use sparingly and only when a default genuinely represents the most common choice; avoid defaults that users blindly accept without reading

### Variable Sets

- Use **Variable Sets** to group reusable sets of variables that appear on multiple catalog items (e.g. "Requester Details", "Approval Info")
- A variable set is defined once and added to multiple items — changes propagate to all items that use it
- Do not duplicate the same variables across items manually; extract to a Variable Set
- Variable Sets can also contain Catalog Client Scripts and Catalog UI Policies that travel with the set

### Catalog Client Scripts

- Same rules as standard Client Scripts apply (no synchronous calls, max 1 AJAX call, use `g_form`)
- Catalog Client Scripts are scoped to the catalog item or variable set — they do not affect other items
- Set the **Applies on** checkboxes correctly: "Catalog Item" (the request form), "Target record" (the created record), or both
- For Service Catalog, **always use GlideAJAX** for server-side data retrieval — there is no table context to trigger Business Rules from

### Catalog UI Policies

- Prefer Catalog UI Policies over Catalog Client Scripts for declarative field control (show/hide, mandatory, read-only)
- Set the **When to apply** checkboxes correctly — Catalog Item view, Target record view, or both
- See the [UI Policies](#ui-policies) section for general UI Policy rules

### Order Guides

- Use Order Guides when a user needs to request multiple related items as a single bundle (e.g. new hire onboarding: laptop + software + access)
- Define the **included items** and their ordering; use **Rule Base** or **Script** to control which items appear based on earlier answers
- Keep Order Guides focused — if the guide has more than 5–7 items, consider whether some should be fulfilled automatically rather than individually requested

### Two-Step Checkout

- Enable two-step checkout when users need a summary/review page before final submission
- When two-step checkout is enabled, `onSubmit` Catalog Client Scripts fire on the **first** submit (moving to the review page), not the final checkout — design validation scripts accordingly

### Fulfillment

- Use **Catalog Tasks** or **Flow Designer** for multi-step fulfillment, not Business Rules on `sc_req_item`
- When a Catalog Item creates tasks, define the task template on the item's **Process Engine** or via a fulfillment flow — do not rely on after-insert BRs to generate child tasks
- Map catalog variables to task or target record fields using the variable's **Map to field** attribute where possible; use a Flow or Script Include for complex mappings

---

## Update Sets

- **Never back out** an update set — deploy a hotfix update set instead
- Do not deploy **Default** update sets to another instance
- Do not use update sets for **locally developed scoped applications** — use the application repository; update sets in scoped apps impact upgradability
- Do not use update sets inside **custom scoped applications**
- For complex deployments, use a **Runbook template**

**Moving multiple update sets:**
Use **batching**, not merging. Batching:
- Makes it easy to add or remove individual update sets
- Runs collision detection across the full batch before deployment
- Preserves traceability back to the original update set (merging destroys this)

**If an update landed in the wrong update set:**
1. If the record wasn't previously in your current set — move it via the `sys_update_xml` list view
2. If it was changed earlier in the set — copy to a new set, or merge and use the current set
3. When in doubt — undo the change in the wrong set and redo it in the correct one

**Pushing data records into an update set:**
Use **"Create Application File"** from the List Choices menu. No scripting required. Useful for data records that application logic depends on (e.g. custom Group Type records).

### Promotion Discipline

When promoting a batch of update sets from dev → preprod → prod, maintain an **ordered promotion list** in the engagement's migration doc (or update set description). Dependencies between update sets make commit order matter — for example, an update set that modifies a form list layout must be committed *after* the update set that created the table.

Minimum content for a promotion list:

| Order | Update Set Name | Depends On | Notes |
|---|---|---|---|
| 1 | `SN - STRY001 - New Approval Table #001` | — | Creates `u_approval_lookup` |
| 2 | `SN - STRY001 - Approval Table List Layout #001` | 1 | List layout depends on table |
| 3 | `SN - STRY002 - Incident Form Changes #001` | — | Independent of 1–2 |

Also document any **non-update-set steps** required alongside the promotion:

- Plugin activations (must run before the update sets that depend on the plugin)
- System property values (if the value differs per environment — e.g. `glide.authenticate.sso.redirect.idp`)
- MID Server / identity server configuration
- XML data imports (see below)
- Post-commit manual validation steps

### Data That Update Sets Don't Capture

Update sets capture configuration, **not data rows**. Reference data, lookup tables, unit test records, and similar content must be migrated separately via XML export/import. Common examples:

- Custom lookup tables (e.g. approver maps, routing tables)
- Sample or seed records for new features
- User group memberships created during development
- Role assignments
- Some system properties (if created outside the update set)

### XML Data Export / Import

For one-off data promotion alongside update sets:

- **Export (single record):** right-click the form header → **Export → XML (This record)**
- **Export (list):** filter the list → right-click the list header → **Export → XML**
- **Import:** elevate to `security_admin` → navigate to any list → right-click the list header → **Import XML** → select the file

**Important caveats:**

- XML import **does not trigger Business Rules** and does not update the cache — use this deliberately when you want to bypass automation, and be aware if you expect BR side-effects to fire
- Exporting a record **does not export its relationship records** — e.g. exporting a `sys_user` record will not include `sys_user_grmember` or `sys_user_has_role` rows. Export those separately.
- Note XML data requirements in the update set description so the person committing the update set knows to perform the import

If the same reference data will be imported more than once, prefer an Import Set + Transform Map over repeated XML imports.

---

## Flow Designer

- **Use Flow Designer for all new automation** — Workflows are legacy and must not be used for new custom builds
- Do **not** migrate OOTB workflows to Flow Designer yourself — wait for ServiceNow to replace them
- When in doubt about the right approach, consult the project architect

**Design principles:**
- **Single purpose** — each flow should have one clearly defined goal
- **Reusable subflows** — design for reuse from the start; approvals are a classic example
- **Clarity** — flow names and action labels should make purpose obvious without documentation
- Break flows exceeding **~15 actions** into subflows

**Actions & subflows:**
- Set **Accessible From = All application scopes** on actions and subflows unless there is a specific security reason not to — this cannot be changed after creation
- Set **Protection = Read-only** on actions to prevent accidental edits
- Ensure inputs have specific types; mark mandatory inputs as required; use default values for choice inputs
- Only use **End step** in a subflow when it has a parent flow

**Performance:**
- Never use `gs.sleep()` — use **Wait for conditions** instead
- Always set conditions on record triggers — never trigger on all records
- Execute flows in the **background** to release UI threads
- Turn flow **reporting OFF in production** (`com.snc.process_flow.reporting.level` = Off) — enable only on specific flows when needed for debugging

**Error handling:**
- Keep error handling out of the main flow body — use subflows for corrective actions
- **Fail early** — if required inputs are unavailable, don't proceed
- **Suppress subflow errors** to prevent them cascading to the parent flow
- Write short, clear error messages

**Gotchas:**
- Avoid changing a flow's **trigger table** after build — all scripted value references must be manually reconfigured and ServiceNow's error messages are often unhelpful
- When reordering steps, **all scripted values must be updated** to reference the correct step
- For flows that need to run as a **specific user**, trigger via a Scheduled Job with the `run_as` field set — flows can only run as System or the initiating user natively
- Triggering multiple IntegrationHub automation actions in rapid succession can cause failures — add wait actions between them and always include error handling with a manual recovery task

---

## CMDB

- Enable the **CMDB Health Dashboard** jobs — they are disabled by default. Configure a job for each health KPI you want to track (duplicates, required fields, audits)
- Place **attributes as high as possible** in the CI class hierarchy — don't define the same attribute separately on multiple child classes when a parent class could hold it once
- **Custom CMDB tables** must be named starting with `u_cmdb_ci` for easy identification
- Use a **tree picker** for Location reference fields — prevents duplicate or misspelled location values
- **Never alter baseline relationship types** (`cmdb_rel_type`) — changes break Discovery and can cause errors
- Use **OOTB CI classes** wherever possible; do not extend directly off `cmdb_ci`
- Do not **recreate OOTB attributes** as custom fields — leverage what exists
- Enable **suggested relationships only** in the Relationship Editor (`glide.cmdb.suggested_relationship.enabled = true`) — first ensure all valid relationship types between classes are listed as suggested, then enable the property to prevent users creating invalid relationships
- Assign a **Business Owner** to every Business Application CI

---

## UI Builder (Next Experience)

Reference knowledge for working with UI Builder / Next Experience Framework. The MCP does not write directly to `sys_ux_*` tables, but this section covers key patterns useful for advising on UI Builder implementations.

---

### Tab Set Translations

Tab headings in a tab set component are stored as `translated_text` on `sys_ux_app_route` records. To translate them:

1. In UI Builder, click the tab set component → pencil icon → copy the **Component ID**
2. Navigate to `sys_ux_app_route.list` in the platform
3. Filter by `parent_macroponent_composition_element_id = <Component ID>`
4. Open each route record and add translations to the `Name` field (type `translated_text`) by switching the instance language

> The long way: Menu > Developer > Open page definition → `sys_ux_macroponent` → Parent Screens related list → Screen Collection record → `sys_ux_screen_type` → UX App Routes related list → open the `sys_ux_app_route` record.

---

### Navigation Header Buttons

Header buttons in a workspace experience are configured via the `chrome_header` UX Page Property on the UX Application record.

**Path:** Now Experience Framework > Experiences > [your experience] > UX Page Properties tab > `chrome_header`

Add a JSON object to the `primaryItems` or `secondaryItems` array in the value field:

```json
{
  "label": {
    "translatable": true,
    "message": "Button label text"
  },
  "type": "navigation",
  "primaryDisplay": "label",
  "value": {
    "opensWindow": "false",
    "value": {
      "href": "your-destination-url"
    }
  }
}
```

---

### Auto-Refreshing Lists

Auto-refresh is not native ServiceNow functionality but can be implemented in UI Builder using a client state parameter + client script + event.

**Pattern:**
1. Add a **client state parameter** (e.g. `listRefreshTime`, type String) with an initial value — without an initial value the first refresh won't trigger
2. Link the list component's **Refresh requested** property to `@state.listRefreshTime`
3. Add a **page client script** using `setTimeout` to update the state parameter after the desired interval
4. On the list component's **Events** tab, add the client script as a handler for `Data Fetch Succeeded`

> **Agent Workspace compatibility:** Pass an object (not a string) to `setState` — passing a string does not work in Agent Workspace.

> **Tip:** The refresh interval can be driven by a system property rather than hardcoded. Multiple lists sharing the same client state parameter will refresh simultaneously.

---

### Workspace Form Actions

UI actions in a Configurable Workspace record's action bar are managed via the `sys_ux_form_action` table (navigate via "UX Form Actions" in the filter navigator).

Key fields on a `sys_ux_form_action` record:

| Field | Purpose |
|---|---|
| Name | Display name of the action |
| Action Type | `UI Action` (references `sys_ui_action`) or `Declarative Action` |
| Table | The table whose record view shows this action |
| Active | Enables/disables the action |
| Description | Documents the action's purpose |

---

### Page Variants & Audiences

A **page variant** is a version of a page at the same URL targeting a different audience via user criteria (e.g. agents see one layout, managers see another).

**Creating a variant:** UI Builder > open experience > open page > Menu > Create variant (or + Create next to Variants).

**Assigning an audience:** Three-dot menu next to the variant > Edit audiences > + Add > select audience > set order number (lower number = higher priority).

**Troubleshooting audiences not appearing:**
- Check `sys_ux_applicability` to verify audience records were created
- Check `sys_ux_applicability_m2m_list` to verify audiences are linked to the correct modules/lists — the UI Builder flow sometimes fails to create these backend records

---

## Service Portal — Widgets

Widget development requires clear file organisation and separation of concerns across four script areas.

**Widget file structure:**
Each widget has its own folder containing 4 files:

| File | Purpose |
|---|---|
| `*.client.js` | AngularJS controller — client-side logic |
| `*.server.js` | Server script — initial data load only |
| `*.scss` | Widget-scoped styles |
| `*.html` | HTML template |

**Client script rules:**
- Wrap all controller code in a function with proper JSDoc documentation (description, widget name, widget ID, author)
- Use `var c = this;` as the controller alias inside the function
- Inject only the dependencies you actually use (`$scope`, `$timeout`, `$rootScope`, services, etc.)

**Server script rules:**
- Data loading should happen **once** during initial widget load — not on subsequent client interactions
- Set data on the `data` object to transfer it to the client script
- All business logic must be delegated to Script Includes — the server script is for data retrieval and transfer only

---

## Service Portal — AngularJS Providers

Directives, services, and factories are all considered **Angular providers** in ServiceNow Service Portal.

**Bundling:**
- Angular providers are compiled and bundled into a single dependencies file (e.g. via a Gulp build process)
- Output convention: `x_[scope]_[appscope].appNameModule.js`
- Module name: `appNameModule`
- All providers are declared and wrapped under the app module

**External / 3rd-party dependencies:**
- Store in a dedicated `dependencies` folder
- HTML and CSS for external components must be added manually in ServiceNow
- JavaScript is bundled into the dependency file
- CSS can also be included in the master widget or a parent container

**HTML templates:**
- Can be embedded inline or stored as separate files
- Linked inside the Angular provider declaration and added manually in ServiceNow
- Generic templates go in a shared `template` folder; directive-specific templates stay in the directive folder

**Directives:**
- Use `link` instead of `controller` in directive declarations — `link` runs after the DOM is compiled and gives direct access to the element, attributes, and scope

**Services vs. Factories:**
- Prefer **services** over factories
- Store in a `services` folder
- Services can act as: shared business logic, helper classes, or data repositories for sharing state between widgets in a single-page application

**Public and private methods:**
- Public methods expose usable functionality to other components — name them clearly to convey intent and capability
- Private methods start with `_` (e.g. `_recalculateAvailableData`) — cannot be called from outside the provider

---

## Service Portal — Server Communication

**Two patterns for loading data:**

1. **Widget initial load** (`*.server.js`) — data is loaded server-side once during the first render and transferred to the client via the `data` object
2. **REST calls** — the only way to get or process data from/to the server after initial load

**REST call rules:**
- **Do not write custom REST handlers** — reuse existing REST service implementations (e.g. from an app template such as `restUtils.js` or `restTableUtils.js`)
- `restUtils.js` — generic REST helpers for standard operations
- `restTableUtils.js` — helpers targeting ServiceNow's Table API endpoints
- If the existing REST utilities don't cover your use case, update them rather than creating a parallel implementation

---

## Service Portal — SCSS

Best practices for writing maintainable, flexible CSS in Service Portal themes and widgets. Service Portal's modularity means theme styles and widget styles must be managed carefully to avoid conflicts.

**1. Avoid common widget classes in global CSS:**
- Service Portal is built on Bootstrap — many Bootstrap classes (panels, wells, forms, alerts) will appear in widgets
- Overriding these classes globally will leak into all widgets unless they have explicitly defined styles
- Be especially careful with layout properties: `margin`, `padding`, `position`

**2. Minimise specificity in global CSS:**
- Global CSS (Theme CSS, CSS Includes) should provide reasonable defaults that are easy to override
- Keep selectors **2–3 levels deep** maximum — widget styles are already scoped 2 selectors deep by Service Portal's CSS scoping
- **Never use `!important`** in global styles

**3. Keep global styles to a minimum:**
- The power in Service Portal is in the widgets — keep styles there
- Valid uses for global CSS: overriding Bootstrap defaults where variables aren't available, adding external CSS libraries, providing custom layouts (Flexbox, etc.)
- In all cases, use narrowly defined class selectors unlikely to collide with widgets

**4. Explicitly define vital CSS in widgets:**
- Don't trust the theme to respect your widget's required styles
- If a widget depends on specific styles to function, define them directly in the widget SCSS
- In widget SCSS, using `!important` is acceptable — Service Portal's CSS scoping keeps it isolated to your widget

**5. Avoid hardcoding colours in widgets:**
- Use SCSS variables with the `!default` keyword so the theme can override them
- Example: `$specialColor: #FFF !default;` — this sets a sensible default but allows the Portal SCSS field to override it
- Widget Options can also be used for colour configuration when you want to restrict the allowed values

**6. Avoid using IDs:**
- Widgets can have multiple instances on a page — IDs should appear only once per document, which widgets can't guarantee
- In global CSS, a single ID tips the specificity scale and can override widget styles unintentionally
- Exception: dynamically applied IDs using `ng-attr-id`

---

## Service Portal — Styling Conventions

A structured approach to CSS class naming combining **prefixed classes** and **BEM** (Block, Element, Modifier) for readable, maintainable markup and styles. Influenced by OOCSS, SMACSS, and BEM.

**General rules:**
- **Never add styling to IDs** — this can break stylesheets in edge cases
- Avoid IDs in HTML altogether — use prefixed classes; for jQuery hooks use `js-` prefixed classes
- Avoid CSS `float` and `table` for layout — use **Flexbox** instead
- Do not use CSS Grid — ServiceNow's supported browsers historically relied on an older spec; Flexbox is the safer choice
- Separate structure from skin — especially for layouts; components may combine both when practical
- Recognise and codify repeating patterns (DRY) — use variables for recurring values
- Do not mirror DOM structure in SCSS nesting
- Use SCSS mixins for vendor prefixing

**Convention 1 — Class prefixes:**

| Prefix | Use | Examples |
|---|---|---|
| `l-` | Layouts — define structure; reusable containers | `.l-list`, `.l-list__item`, `.l-horizontal-layout` |
| `c-` | Components — concrete, implementation-specific UI pieces | `.c-button`, `.c-card`, `.c-card__header` |
| `u-` | Utilities — reusable single-purpose helpers; not bound to any specific UI | `.u-transparent-background`, `.u-no-select`, `.u-margin-small` |
| `is-` / `has-` | State — temporary, optional, or short-lived styling (replaces BEM state modifiers) | `.is-hidden`, `.is-active`, `.has-items` |
| `_` | Hacks — a class used as a workaround; signals technical debt | `._clear-fix`, `._fix-something` |
| `js-` | Behaviour hooks — JavaScript targets; no styling should be applied to these | `.js-select2-selector`, `.js-draggable` |

> **Important:** For state styling, always use `is-` / `has-` prefixes, **not** BEM modifiers. Write `c-card is-disabled`, not `c-card c-card--disabled`.

**Convention 2 — BEM for components and layouts:**
- **(B)lock** — a reusable component, prefixed with `l-` or `c-`
- **(E)lement** — a child part of a block, connected by double underscore (`__`)
- **(M)odifier** — a variation of a block or element, connected by double hyphen (`--`); used for appearance variants, **not** state
- Keep element names flat — if a card header contains a subtitle, name it `.c-card__subtitle`, **not** `.c-card__header__subtitle`
- Always include both the block class and the modifier class in the HTML (e.g. `class="l-list l-list--horizontal"`)
- Modifiers are not always needed — for single-purpose styles that apply across contexts, use utility classes (`u-`) instead (e.g. directional margins, borders, text centering, font adjustments)

> **ServiceNow limitation:** ServiceNow uses an older SCSS version that does not support the standard `&__element` / `&--modifier` BEM nesting syntax. Write selectors flat instead.

**Convention 3 — SCSS variables (theming):**
- Use the `!default` postfix on every variable declaration — this allows portal themes to override values
- Separate **definitions** (colour values, spacing values) from **usage** (which element uses which variable)
- This separation enables three things: theming a whole application via a single set of variables, tweaking theme colours without touching individual elements, and changing one element's colour without redefining a shared colour variable

**Applying to existing projects:**
- Refactor gradually — when a story touches markup or styling, convert that part to follow these conventions
- For larger refactors that aren't story-driven, get product owner approval first

---

## Service Portal — Accessibility (WCAG)

All Service Portal pages must be usable by screen readers and navigable by keyboard. WCAG (Web Content Accessibility Guidelines) is organised around four themes: Perceivability, Operability, Understandability, and Robustness.

**Perceivability:**
- Provide text alternatives for all non-text content — images, icons, and media cannot be interpreted by screen readers
- Buttons with icons must have `aria-label` attributes (e.g. `aria-label="Close"`)
- Provide text alternatives for text rendered as images
- HTML source order matters — assistive tools follow DOM order, not visual order; don't rely on CSS to reorder content
- Maintain sufficient colour contrast ratios

**Operability (keyboard accessibility):**
- Support full keyboard navigation — many assistive devices register as keyboards
- Use `tabindex` to define a logical tab order and make the correct elements focusable
- Actions must be triggered by both click **and** keyboard (e.g. Space/Enter on a focused item)
- Maintain a visible focus indicator — never hide `:focus` styles with CSS
- Tab order should follow a logical reading flow — no jumping between distant sections
- Notifications and messages must remain visible long enough for users to read them; timing should be adjustable or disableable
- Use proper semantic HTML tags for meaning — if a block has a title, use a heading element so assistive tools associate the content with that heading

**Understandability:**
- Use simple, clear language; limit abbreviations
- Provide definitions for technical terms — either inline or via links
- Ensure consistency — the same action should produce the same result across different parts of the application
- Context changes should be user-initiated, or there should be a setting to disable automatic context changes

**Recoverability / Error prevention:**
- Help users avoid mistakes and fix them when they occur
- Provide clear labels on input validation errors
- Submissions should be either reversible, checked with warnings so users can correct issues, or confirmed by the user with an option to edit before final submission

**Robustness:**
- Write valid, logically nested HTML — don't rely on CSS fixes for structural issues; tools (current and future) need to parse the markup
- Use `name`, `role`, `aria-label`, and `aria-labelledby` attributes to help tools identify and describe elements
- Use `role="status"` for success messages and `role="alert"` for warnings — reserve `alert` for genuinely important notifications only

---

## Service Portal — Moment.js i18n

By default, Moment.js is loaded into Service Portal but ServiceNow's translation system does not automatically translate Moment's formatted date output (e.g. humanised durations like "3 days" won't appear as "3 dagen" for Dutch users).

**Setup steps:**

1. Create a **widget dependency** record (e.g. named `moment languages`)
2. Add **JS Includes** for each locale you need — language files are available from the Moment.js locale repository
3. Add the widget dependency to any widget that needs translated date output
4. In the widget client script, set the locale:
   - `moment.locale('nl')` — set a specific locale
   - `moment.locale(g_lang)` — set the locale to match the user's ServiceNow language preference (falls back gracefully if the locale file isn't included)

---

## Automated Test Framework (ATF)

ServiceNow's Automated Testing Framework enables automated regression testing of back-end and form-based functionality. ATF does **not** support testing Service Portal widgets.

### What to Test

**Must test:**
- **Script Includes** — validate all functions; cover the happy flow and every defined error flow. Script Includes contain the bulk of back-end logic and are the highest-value target for automated tests.
- **Scripted REST APIs** — test input/output for GET calls; for POST/PUT/PATCH/DELETE also verify the outcome of the operation. Test happy flow and defined error flows. The underlying implementation logic should already be covered by Script Include tests, so REST tests focus on the API layer (routing, status codes, payload structure).

**Test when critical:**
- **Forms** — only if a form is vital to the application's functionality. ATF can test forms, but they offer less value in most cases.
- **Business Rules / Scheduled Jobs** — these should contain no logic and instead delegate to a Script Include. Since the Script Include is already tested, a separate test for the trigger component is redundant and not recommended.

**Cannot test:**
- Service Portal widgets (ATF does not support them)
- Flow Designer flows via ATF UI (but flows can be executed and verified via `sn_fd.FlowAPI` in a Run Server Side Script step)

### Environment Rules

- **Never run tests on a production instance.** Tests impersonate users with elevated access, create and modify data that is visible before rollback, and can trigger events such as email notifications. All test execution belongs on sub-production instances.
- Schedule the application's top-level Test Suite to run **daily** on the development instance. Prefer running scheduled tests when no other activity is happening on the instance, because actions performed by the currently logged-in user during test execution can be rolled back along with test data.
- When running tests manually, avoid performing other work on the instance in the same browser session.

### Test Structure — Always Start with Impersonate

Every test must begin with an **Impersonate** step targeting a dedicated test user who has the same roles and permissions as a typical application user. Running tests as an admin user bypasses ACLs and can mask permission bugs — or worse, cause unintended data changes with elevated privileges.

### Test Data Setup

- After impersonation, insert mock records using **Record Insert** steps to create the test data your assertions depend on.
- Use **contextual values** to chain step outputs — for example, pass the impersonated user's sys_id from the Impersonate step into a Record Insert step's reference field, rather than hardcoding a user.
- When testing a form or inserting a mock record, fill in **all fields critical to the application** — not just mandatory fields. This ensures every relevant field is validated on every test run.
- Verify inserted records with a **Record Query** step (query by sys_id using the contextual value from the insert step) before proceeding to assertions.

### Common Pitfall — Record Insert Succeeds but Values Are Null

A Record Insert step can return a success result even when it partially fails. If the application's table access settings do not have **Can create** and **Can update** checked, the record is created but all non-auto-generated field values are set to null. A subsequent Record Query on sys_id will find the record, but queries on any other field will not. Always verify that application access permissions are correct on tables under test.

### Assertions — Server Side Scripts and Jasmine

Use the **Run Server Side Script** step (under the Server category) to test Script Include logic. ATF provides two assertion approaches:

**Built-in `assertEqual`:**
```javascript
var testAssertion = {
    name: "my test assertion",
    shouldbe: "expected value",
    value: "actual value"
};
assertEqual(testAssertion); // throws Error on failure, logs to step output
```

**Jasmine framework** (recommended for richer assertions — uncomment `jasmine.getEnv().execute();` outside the function body to enable):
```javascript
(function(outputs, steps, stepResult, assertEqual) {
    describe("getListsForUser Test", function() {
        var userID = steps("impersonate_step_sys_id").user;
        var service = new ListService();
        var lists = service.getListsForUser(userID);

        it("should not return null or undefined", function() {
            expect(lists).not.toBeUndefined();
            expect(lists).not.toBeNull();
        });

        it("should have at least one list", function() {
            expect(lists.hasNext()).toBe(true);
        });
    });
})(outputs, steps, stepResult, assertEqual);
jasmine.getEnv().execute();
```

> ⚠️ Jasmine does not work on instances running the Jakarta release or earlier.

### Test Scope — Don't Over-Test, Don't Under-Test

- Test the happy flow and every explicitly defined error flow for each function or endpoint.
- Do **not** attempt to test every conceivable scenario upfront. If an untested scenario later causes a bug, fix it and then add a test case for that scenario — this prevents the same bug from recurring without wasting time on speculative tests.
- Group test steps logically: keep server steps together and UI steps together within a test. Mixing them (e.g. open form → server validation → check UI button) forces redundant steps because you must reopen the form after server steps.

### Base Tests — Reusable Setup

When multiple tests need the same setup (impersonation + test data), define a **Base Test** containing the shared Impersonate and Record Insert steps. To create a new test from the base, open the Base Test record and click **Copy Test** — this duplicates all setup steps so you can rename the copy and add your specific assertion steps without repeating setup work.

**Guidelines for Base Tests:**
- A proper Base Test contains one or more steps to create test data and one or more steps to perform impersonation.
- Do **not** create a single Base Test that tries to cover every test in the application — it will become large and slow to execute. Create multiple, focused Base Tests for different functional areas.
- Custom Test Steps can also be defined for frequently repeated server-side operations that the OOTB step library does not cover. Custom steps are server-side only and cannot test UI directly.

### Test Suite Hierarchy

Structure Test Suites hierarchically by component type. This keeps the test base maintainable and allows logical execution ordering — for example, Script Include tests should pass before REST API tests run, since the APIs depend on the Script Includes.

**Recommended hierarchy:**

```
APP_NAME Suite                                          ← top-level, run nightly
├── APP_NAME - Script Include Suite                     ← all SI suites
│   ├── APP_NAME ScriptIncludeName - Suite              ← per SI
│   │   ├── ScriptIncludeName - FunctionA Test
│   │   └── ScriptIncludeName - FunctionB Test
│   └── APP_NAME AnotherSI - Suite
│       └── AnotherSI - FunctionC Test
└── APP_NAME - Scripted REST Suite                      ← all REST suites
    ├── APP_NAME EndpointName - Suite                   ← per endpoint
    │   ├── EndpointName - Normal Flow Test
    │   └── EndpointName - Missing Params Test
    └── APP_NAME AnotherEndpoint - Suite
        └── AnotherEndpoint - Normal Flow Test
```

**Naming conventions:**

| Component | Convention | Example |
|---|---|---|
| App Suite | `APP_NAME Suite` | `TodoList4U Suite` |
| Script Include Suite (parent) | `APP_NAME - Script Include Suite` | `TodoList4U - Script Include Suite` |
| REST API Suite (parent) | `APP_NAME - Scripted REST Suite` | `TodoList4U - Scripted REST Suite` |
| Individual SI Suite | `APP_NAME SI_NAME - Suite` | `TodoList4U ListService - Suite` |
| Individual Endpoint Suite | `APP_NAME ENDPOINT_NAME - Suite` | `TodoList4U Get Lists - Suite` |
| Function Test | `SI_NAME - FUNCTION_NAME Test` | `ListService - GetListsForUser Test` |
| Endpoint Test | `ENDPOINT_NAME - TEST_DESC Test` | `Get Lists - Normal Flow Test` |

### Test Suite Schedules

- Schedule the top-level App Suite to run daily on the development instance.
- A single schedule record can be attached to multiple Test Suites.
- Optionally configure a browser for UI test steps and add team members to the **watchlist** so they are alerted on failures.
- Tests with UI steps require an open **Scheduled Client Test Runner** page matching the schedule's browser conditions. The runner must be on an unlocked machine with the browser already open. A dedicated ATF test user account should stay logged in for this purpose.
- Server-only tests (no UI steps) do not require a Client Test Runner.

### Parameterized Tests

Available from the Orlando release onwards. Parameterized tests let you run the same test with different data sets by enabling the **Enable parameterized testing** checkbox on the test record.

**Two components:**
- **Parameter definitions** — custom parameters with a label and data type. Parameters are either *shared* (usable in any parameterized test) or *exclusive* (only in the test where they were created). Prefix data set values with the scoped application prefix they belong to.
- **Test run data sets** — each data set triggers a separate test execution.

> ⚠️ Parameterized tests fail if no data sets are defined.

### Naming — Tests and Data Sets

- Test case names should follow `APP_NAME - Description of test purpose` (e.g. `Deviation Management - Test deviation`).
- Parameter and data set variable names should be clear and descriptive so the purpose of each value is obvious without reading the test steps.

### Troubleshooting

- Use **Test Logs** and **Test Transactions** (related lists on the Test Result record) to diagnose failures and performance issues.
- If ATF modules are not visible on a fresh instance, navigate to the Application Menus list, find the Automated Test Framework record, and enable the necessary modules. Assign the roles `atf_test_admin`, `atf_test_designer`, and `admin` to your user profile.

### ATF via MCP

ATF test creation is a UI-only activity, but tests can be **executed** programmatically:

```javascript
var testRunner = new sn_atf.TestRunner();
var result = testRunner.runTest('test_sys_id_here');
gs.info('Test result: ' + result.getStatus());
```

This is useful for smoke tests after deployments or for integrating ATF execution into automated pipelines via background scripts.

---

## Import Sets & Transform Maps

Import Sets are ServiceNow's general-purpose mechanism for loading external data into production tables. They are used by LDAP imports, file-based imports (CSV, Excel, XML), JDBC connections, and Integration Hub Data Streams. This section covers general best practices; see [LDAP User Import](#integrations--ldap-user-import) for LDAP-specific guidance.

### Architecture

External data → **Data Source** → **Staging Table** (import set table) → **Transform Map** → **Target Table**

Data is always loaded into a staging table first, never directly into the target table. The transform map controls how staging rows map to target records, including field mappings, coalesce logic, and scripted transformations.

### Staging Table Design

- Staging table fields should be **plain types** (string, integer) — never reference fields; reference resolution happens in the transform map
- **Field lengths:** verify that auto-created field lengths are sufficient for the source data; fields that are too short silently truncate data. Common offenders: distinguished names, email lists, JSON payloads, and description fields
- **One staging table per data source** — do not reuse a staging table for unrelated imports; it creates column clutter and makes troubleshooting harder
- When adding new source fields, they are auto-created on the staging table at first import — but always check the length and type afterwards
- When removing source fields, delete the corresponding staging table column to keep the table clean

### Coalesce Fields

The coalesce field is how ServiceNow decides whether to **insert** a new record or **update** an existing one on the target table. Getting this wrong causes duplicates or overwrites.

- Choose a field that **uniquely identifies a record** on the target table — typically a natural key (e.g. `user_name`, `email`, `asset_tag`), not sys_id
- **Test your coalesce** with realistic data before running a full import — an incorrect coalesce will either create thousands of duplicates or overwrite unrelated records
- For complex environments (e.g. multi-domain, multi-source), coalesce on a synthetic unique identifier (e.g. `objectGUID` for LDAP)
- After configuring the coalesce, **add a database index** on the coalesce field(s) on the target table — without an index, every row triggers a full table scan during transform

### Transform Map Best Practices

**Field mappings:**
- Map simple fields declaratively (source field → target field) — do not use a script when a direct mapping works
- For reference fields, use the **Reference value field** (e.g. `name`, `user_name`) to let ServiceNow resolve the reference by display value rather than sys_id
- Set the **Choice action** appropriately for choice/reference fields: `create` (auto-create if not found), `ignore` (skip if not found), or `reject` (fail the row if not found)

**Transform scripts:**
- **onBefore:** runs before each row is mapped — use for input validation, data cleansing, and skipping rows (`ignore = true`)
- **onAfter:** runs after each row is mapped and the target record is saved — use for post-processing that requires the target record's sys_id (e.g. creating related records, setting reference fields that need a lookup)
- **onComplete:** runs once after all rows are processed — use for summary logging, cleanup, or triggering downstream processes
- **onStart:** runs once before the first row — use for initialising variables, caches, or hash maps that will be reused across rows
- Delegate complex logic to a **Script Include** — keep transform scripts as thin wrappers, just like Business Rules

**Reference field gotcha:**
Never map a Distinguished Name, external ID, or non-sys_id string directly to a reference field via a simple field mapping — it will fail silently or create garbage data. Always use a transform script to look up the correct sys_id.

### Error Handling

- Transform maps have a **Row error handling** setting: `stop`, `skip`, or `log and continue` — for production imports, use `log and continue` so that one bad row does not halt the entire import
- Review the **Import Log** (`sys_import_log`) and the **Import Set Rows** (`sys_import_set_row`) table after every import run — filter by state `error` to find failed rows
- For critical imports, build a **post-import validation** step (scheduled job or flow) that checks record counts, null fields, and referential integrity

### Cleanup

- Import set tables and their row data grow continuously — ServiceNow auto-cleans OOTB import tables, but **custom staging tables are not auto-cleaned**
- Implement a **scheduled cleanup job** that deletes import set rows older than a retention period (30–90 days is typical)
- Monitor staging table sizes — tables with hundreds of thousands of rows degrade list performance and can become inaccessible in the UI

### Scheduled Imports

- For recurring imports (e.g. daily user sync, nightly asset refresh), attach a **Scheduled Import** to the data source
- Set the schedule to run during off-peak hours to minimise platform impact
- Ensure the import account / data source credentials do not expire without notice — set up monitoring or alerting on import failures

---

## Integrations — General

Before building any interface, gather and lock down **requirements and field mappings** before choosing a technical approach. Mappings are typically the most time-consuming part and are rarely dependent on the technology used.

**Pre-build checklist:**
- Understand the external system's capabilities and limitations — misunderstandings about the other side are a common source of rework
- Check with an architect whether an OOTB connector, a ServiceNow Store spoke, or a pre-built solution (e.g. Connector4U for transactional data) already covers the requirement
- Never build what you can buy or configure — check vendor-provided spokes (Microsoft, SAP, Salesforce, etc.) in the ServiceNow Store first

**Know the platform boundaries:**
- ServiceNow is not a data lake and should not be used for high-volume bulk storage — table size affects performance
- Only interface data that will actually be consumed; do not import bulk data because you can
- Platform customisation records (update set content) should only be interfaced via the appropriate ServiceNow APIs (e.g. Catalog API for catalog items)

**Scope and error philosophy:**
- Start with a small functional scope and expand iteratively — do not try to cover every edge case in the first release
- Design for errors from the start: discuss and document what should happen for each class of failure (HTTP 4xx, 5xx, timeouts, malformed payloads)
- Include the minimum non-repudiation elements in every interface (see below)

**Build scoped when possible:**
- ServiceNow recommends building interfaces as scoped applications for portability and reusability
- Evaluate on a case-by-case basis using the scoped vs. global decision criteria for the engagement

### Non-Repudiation

Every interface must provide enough evidence to prove — or disprove — that a message was sent, received, and processed correctly. Without adequate logging, any unrelated error will be blamed on your interface.

**Outbound message logging:**
- Store the exact outbound payload (headers, body, method, endpoint) **before** sending
- On response, store the HTTP status code and response body
- Update a state field or status indicator on the source record based on the response

**Inbound message logging:**
- Store inbound messages as intact as possible **before** any processing begins — if processing fails, you still have the raw message
- Maintain control over the response you return to the caller

**Error handling and reporting:**
- Capture and classify errors at every stage (send, receive, transform, process)
- Provide reporting or a dashboard view of interfacing errors
- Where possible, automate remediation or offer retries to the user
- For mission-critical data, send notifications on failure — but implement throttling to prevent email flooding

### Performance

- Estimate expected message volume (guess high), then **load-test at twice that volume**
- Run processing **asynchronously** wherever possible — outbound messages should almost always be async; scoped apps do not support synchronous outbound REST
- For inbound messages, decide based on load and requirements — transactional records typically need a synchronous response, but bulk data imports should be queued
- Request or send **only the fields that will be used** — e.g. when querying the Table API, select only the needed fields instead of returning all columns
- Clean up log and queue tables on a schedule — tables with hundreds of thousands of records degrade performance and eventually become inaccessible in the UI; import sets and OOTB logging tables are auto-cleaned, but custom tables are not

### Preventing Loops in Bi-Directional Interfaces

- In any trigger mechanism (Business Rule, Flow, etc.), filter out updates made by the integration user so the interface cannot re-trigger itself
- Alternatively, use a boolean flag field if user-based filtering is not practical
- Audit the instance for non-best-practice configurations (e.g. after-insert Business Rules that update the same record) that could cause double-sends

---

## Integrations — Scripted REST API

Use Scripted REST APIs when OOTB REST endpoints do not meet requirements — typically when you need custom payloads, aggregated data from multiple tables, or custom business logic during the request.

### REST Conventions

Follow standard HTTP method semantics:

| Method | Purpose | Modifies data? |
|---|---|---|
| GET | Query / retrieve data | No — never modify on GET |
| POST | Create a new record | Yes |
| PUT / PATCH | Update an existing record | Yes |
| DELETE | Remove a record | Yes |

### Versioning

- Always version your API from the start (e.g. `/api/x_prefix/my_api/v1/...`)
- Never introduce breaking changes to a published version — create a new version instead
- Encourage or require consumers to specify a version in the URL; optionally omit a default version to force consumers to be explicit
- New optional parameters may be added to an existing version without creating a new one

### Response Standards

**HTTP status codes — return the correct code for every outcome:**

| Code | Meaning |
|---|---|
| 200 | Request completed successfully |
| 201 | Record created successfully |
| 204 | Record deleted successfully (no body) |
| 4xx | Client error — 400 bad request, 401 unauthorized, 404 not found, etc. |
| 5xx | Server error — problem on the ServiceNow side |

**Error responses:**
- Always return a helpful error message alongside the status code — the consumer should understand the problem without needing to consult your documentation
- Example: for a 404, return `"The specified record does not exist. Ensure a record with the ID of <id> exists in the application."` — not just `"Not found"`
- Use the pre-configured error objects available in the Scripted REST API framework; use the customisable `ServiceRequest` error object when the built-in options do not fit

### Testing

- Build automated tests for each resource **as part of development**, not after the fact
- Tests should validate: response codes, response headers, response body content, authentication/authorisation requirements, and that error conditions return useful messages
- Use a REST client that supports repeatable test collections (e.g. Postman)
- Re-run tests after every version change to confirm no regressions

### Documentation

Every Scripted REST API must be documented. At minimum, cover:

1. **Purpose and scope** — what problem the API solves
2. **Endpoints** — organised logically
3. **Parameters** — query params, path params, headers for each endpoint
4. **Responses** — status codes, error messages, and data structures for each endpoint
5. **Code examples** — in at least one language or via Postman collections / Platform API Docs
6. **Links** to related API reference docs or developer tools
7. **Keep documentation up to date** — update it whenever endpoints, parameters, or responses change

---

## Integrations — Integration Hub & Custom Spokes

Integration Hub is ServiceNow's low-code integration platform. Prefer Integration Hub spokes over legacy scripted approaches (Outbound REST, Scripted REST, `RESTMessageV2`) when a spoke exists or can be extended — spokes offer built-in usage tracking, reusability across multiple flows, and simpler upgrades.

### When to Use What

- **OOTB spoke exists and meets requirements** — use it directly; do not customise the baseline spoke actions
- **OOTB spoke exists but lacks needed actions** — extend via a custom spoke that pairs with it, or clone/create new actions in a new Update Set within the existing spoke's scope
- **No spoke exists for the target system** — build a standalone custom spoke
- **Simple one-off integration or legacy requirement** — legacy approaches (RESTMessageV2, Scripted REST) are acceptable but carry higher maintenance cost

> Legacy web service features such as `RESTMessageV2` do not consume Integration Hub transactions when used outside of Flow Designer.

### Custom Spoke Standards

**Application scoping:**
- One scoped application per spoke — each spoke handles a single integration target
- A spoke is a scoped app containing actions, subflows, flow templates, and supporting files

**Connection and Credential Alias:**
- Always use a **Connection and Credential alias** instead of defining connection details inline — an alias lets you update credentials once without reconfiguring every action
- Create the alias in the scope of the spoke
- Name the alias after the spoke name — do **not** include the word "spoke" in the alias name

**MID Server considerations:**
- A MID Server is required for communication with systems behind a firewall
- Avoid switching execution between the instance and MID Server repeatedly within an action — group instance-side record operations separately from MID Server integration steps
- The MID Server only has access to `sys_id` references from GlideRecord objects — inputs of type "Reference" do not work on a MID Server; pass the needed field values as explicit action inputs instead

### Creating Actions

- Create actions in the spoke they belong to — do not duplicate the same action across multiple spokes
- Set **Accessible from = All application scopes** by default
- Assign a **category** to every action (unless the spoke has only 1–2 actions total)
- Every action must have a **unique name** within its scope
- Actions must be **published**
- After finalising an action, set its properties to **Read-Only** to prevent accidental edits

**Naming actions:**
- Human-readable names, space-separated, each word capitalised (e.g. `Create Incident`, `Look Up User`)
- Prefix with **"Look Up"** if the action searches for objects
- Prefix with **"Get"** if the action retrieves details of a specific object

### Designing Action Steps

A typical action follows this step sequence: Inputs → Input Pre-Processing and Validation → Core Integration Steps → Error/Response Handling → Outputs.

- Delegate pre-processing and error handling to **separate Script Includes** called from Action Designer script steps — do not put complex logic inline
- Eliminate code repetition across actions
- Error handling must validate all outputs of REST steps for null values before further processing
- Provide a **default error message** as a fallback
- Strip null/undefined inputs from the request body before sending

**REST steps:**
- Use binary or multipart REST step types for attachment transfers
- Reference the API version via a **Connection Attribute variable**, not a hardcoded value
- Limit each action to a **single integration call**
- Note: the Resource Path in a REST step is URL-encoded

**JDBC steps:**
- The JDBC step in a regular action has a ~5 MB data limit — suitable for simple CRUD or single-record lookups, not bulk data
- For large datasets, use a **Data Stream action** (supports JDBC); consume via Import Sets using the IntegrationHub Data Stream data source option
- Avoid consuming data stream actions directly in a flow for very large datasets

### Error Handling

- Decouple platform error messages from API error messages — the user-facing message should make sense to a process analyst, not expose raw API internals
- Keep error messages short and self-explanatory
- Document all possible API error codes in the **Action description**

### Script Includes in Spokes

- Spoke Script Includes should **not** be client-callable
- If cross-scope or public access is needed, expose via a Scripted REST API that calls the Script Include
- Create separate Script Includes for utilities vs. error handling

### Inbound Webhooks / Callbacks

Three patterns for receiving events from external systems:

| Pattern | When to use |
|---|---|
| **Webhook** (Scripted REST API) | External system can push events — protect with basic or token auth; register the webhook URL as a listener in the target system; invoke a Flow on receipt |
| **Polling** (Scheduled Flow) | No ability to set up a callback — periodically check the remote system for updates |
| **Inbound Email** (Email Trigger/Flow) | External system supports email notifications — parse the email for data or use a lookup ID to fetch details via an outbound call |

### Extending OOTB Spokes

When cloning or extending baseline spoke functionality, establish a **review and test process** for each new spoke version release. This ensures your custom actions pick up the latest features and do not conflict with updated baseline actions.

---

## Integrations — OAuth 2.0

OAuth 2.0 is the standard authorisation protocol for token-based access in ServiceNow integrations. Use OAuth instead of basic authentication whenever the target system supports it.

### Outbound OAuth Flows in ServiceNow

| Flow | How it works | When to use | Token refresh |
|---|---|---|---|
| **Client Credentials** (preferred) | App exchanges client ID + secret for an access token | Server-to-server integrations with no user interaction — best for maintainability as the token does not expire in the traditional sense | No refresh token — a new access token is obtained automatically |
| **Authorization Code** | User authenticates and authorises; code is exchanged for an access token | Integrations that act on behalf of a specific user with a trusted third-party service | Supports refresh tokens; an admin must re-authenticate once the refresh token expires |
| **Resource Owner Password** | Username and password are sent directly to the authorisation server | Internal or low-trust systems where no interactive user consent flow is practical | Optional refresh token |

**Prefer Client Credentials** when the target API supports it — it removes the need for manual admin re-authentication and is the easiest to maintain for automated integrations.

**Key best practices:**
- Always register OAuth providers and profiles in ServiceNow rather than managing tokens manually in scripts
- Store client secrets in credential records, never in clear text in scripts or system properties
- When using Authorization Code flow, document which admin is responsible for token refresh and set up monitoring or alerting before tokens expire
- Use Connection and Credential aliases (same pattern as Integration Hub spokes) to centralise OAuth configuration

---

## Integrations — LDAP User Import

LDAP import is the standard mechanism for provisioning users, groups, and group memberships from Active Directory (or other LDAP directories) into ServiceNow. ServiceNow acts as the LDAP client and is a **consumer** of user data, not the source.

### When LDAP Import Is Needed

- Even with SSO, ServiceNow needs user records for authorisation (role assignments, group memberships) — LDAP import provides these unless auto-provisioning is in use
- Use cases beyond authentication: group memberships, HR-related user details, manager hierarchies, department/location data

### Architecture Components

The LDAP import chain consists of: **LDAP Server** → **MID Server** (in most cases) → **OU Definitions** (search queries) → **Data Sources** → **Staging Tables** → **Transform Maps** → **Target Tables** (`sys_user`, `sys_user_group`).

### LDAP Server Setup

- Create **one LDAP Server record per independent directory** the customer wants to import from
- Add **all available LDAP URLs** per server for redundancy — ServiceNow tries each in sequence until one connects
- Communication is typically via MID Server; direct LDAPS is rare
- The import account only needs **read-only browse access** to the LDAP store (e.g. a member of "Domain Users" for AD)

### OU Definitions

- At minimum, create **two OU definitions**: one for users, one for groups
- The combination of OU search queries must cover all required user/group objects without including unwanted objects
- Use appropriate LDAP filters (e.g. `(&(objectClass=person)(sn=*)(!(objectClass=computer)))` for users; `(objectClass=group)` for groups)

### Attributes

- Only import attributes that will actually be used in the transform map — do not request unnecessary fields
- Mandatory/highly recommended attributes for users: `givenName`, `sn`, `distinguishedname`, `mail`, `userprincipalname`, `manager`
- Mandatory/highly recommended attributes for groups: `samAccountName`, `description`, `managedBy`
- User passwords are **never** retrieved from LDAP — and deletions in AD are not pushed to ServiceNow; they only disappear on the next full import

### Staging Tables

- Watch out for **field lengths** — auto-created staging table fields are often too short; increase lengths for fields like `u_dn`, `u_manager`, `u_source`, `u_mailaddress` (255+), `u_memberof`, `u_member` (4000+), and `u_thumbnailPhoto` (16000+)
- Field length adjustments must be made on **all** staging tables (at least two: users and groups)
- All staging table fields must be **plain** (no reference type fields)
- If an attribute is removed from the import, delete the corresponding staging table field; new attributes are auto-created on import

### Transform Maps

**Manager field — critical rule:**
The `manager` field coming from LDAP is a Distinguished Name string. It **must not** be mapped via a simple field mapping — always use a transform script to resolve the DN to a `sys_user` reference. The same applies to `managedBy` on group imports.

**Coalesce strategy:**

| Transform | Simple case | Complex case (e.g. name changes, multi-domain) |
|---|---|---|
| Users | Coalesce on `user_name` | Coalesce on `u_guid` (objectGUID) |
| Groups | Coalesce on `name` | Coalesce on `u_guid` (objectGUID) |

- After configuring transform maps, **index the coalesce fields**
- Leave all OOTB transform scripts intact — they handle group memberships and logging

### Operational Considerations

- Changes made directly in ServiceNow to LDAP-imported records may be **overwritten** on the next import — communicate this to the customer
- For tracking active/inactive status, map `userAccountControl` to `sys_user.active` and `sys_user.locked_out`
- Consider adding a custom `u_ldap_last_seen` field (DateTime) updated on every import — useful for identifying and deactivating users that have been removed from LDAP
- For thumbnail photos, set the system property for binary attributes (`objectsid,objectguid,thumbnailphoto`) on both the instance and the MID Server, and restart the MID Server after the property change

---

## Integrations — Security

### Authentication

- Prefer **OAuth 2.0** (Client Credentials or Authorization Code) over basic auth for all new integrations — see the [OAuth 2.0 section](#integrations--oauth-20) for flow selection guidance
- When OAuth is not supported by the target system, use **token-based or mutual authentication** as the next-best option
- Basic auth is the weakest option: if used, enforce a strong password, and **use different passwords for DEV and PROD** — `password2` fields in ServiceNow (e.g. on Basic Auth profiles) can be decrypted by admins
- Use **separate integration users and auth profiles per interface** — this allows you to configure the minimum required access per interface and to rotate credentials independently
- On every integration user record, enable **"Web service access only"** — this prevents the credentials from being used to log in to the ServiceNow UI

### Authorisation and Data Security

- Limit every interface user's access to the **bare minimum** tables and fields required — granting a broad role like `itil` gives read/write access to all ITSM task tables via the Table API, even if the interface only needs access to incidents
- In Scripted REST APIs, always use `GlideRecordSecure` to enforce table-level ACLs — without it, a user with no roles could potentially read or modify data depending on your code
- Require **stricter ACLs** for operations that modify data (POST, PUT, DELETE) than for read-only operations (GET)
- Test authentication, authorisation, and ACL enforcement **before releasing** the API

### IP Address Access Control

When instances use IP Address Access Control (System Security → IP Address Access Control), factor this into integration planning:

- **Whitelist integration partner IPs** — any inbound integration source must have its IP range added to the allow list; cloud-hosted partners (AWS, Azure) may have large or changing IP ranges, so evaluate whether a MID Server-based outbound pattern is more practical
- **Whitelist other ServiceNow instances** — add target instance IPs as exceptions on the source instance to prevent update set transfers from failing
- **Outbound calls bypass IP restrictions** — if managing inbound IP ranges becomes impractical, consider restructuring the integration so ServiceNow initiates the call (outbound via MID Server or direct), avoiding the IP whitelist problem entirely
- **Document all whitelisted ranges** and assign an owner responsible for maintaining them; review periodically
- Reference: ServiceNow KB0598826 for the full IP address information landing page
