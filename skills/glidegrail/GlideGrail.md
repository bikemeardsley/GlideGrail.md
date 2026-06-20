# ServiceNow Development Standards

> Engagement-agnostic best practices for ServiceNow development.  
> PREFIX is engagement-specific: use the client prefix, `SN` (ServiceNow), or equivalent as appropriate per project.

> **Authoritative platform reference.** These standards capture *judgment and conventions*. For *current, authoritative platform behavior* (APIs, feature specifics, release changes), consult ServiceNow's official documentation published as markdown for LLM consumption: https://github.com/ServiceNow/ServiceNowDocs . If a rule here and the official docs ever conflict on a platform *fact*, the official docs win on facts; this doc governs style and conventions. These sections deliberately avoid restating platform mechanics the official docs already cover; where a mechanic *is* summarised here, it is because it directly shapes a design rule. Agents: check that repo for any feature detail you are unsure about before generating code.

> **Authoring scoped-app structure — ServiceNow SDK (Fluent).** Deterministic app metadata (tables, fields, ACLs, REST Messages, properties, Scripted REST APIs) is authored in TypeScript via the **ServiceNow SDK** and deployed with the `now-sdk` CLI — *not* clicked together in the UI (see [Application Scope](#application-scope) / [Update Sets](#update-sets)). Fluent has little presence in model training data, so generated Fluent is hallucination-prone: **never invent a Fluent signature.** The authoritative, version-published API reference is the Fluent docs hub at https://servicenow.github.io/sdk/ , which also exposes machine-readable grounding (`llms.txt`, per-version `llms-full.txt`, and `versions.json`). Agents: resolve the project's `@servicenow/sdk` version from `package.json`, then ground against that version's reference — or, on recent SDKs, use the official **`now-sdk-explain`** agent skill (bundled in the npm package), which feeds live API signatures straight from the installed CLI. Generative artifacts (flow logic, Script Include bodies, UI) remain a Now Assist / NASK concern; this blurb governs the deterministic structure the SDK owns.

> **Learning, not just rules.** Rules that are not self-evident carry a collapsible **Why?** block underneath — expand it when you want the reasoning, ignore it when you just need the rule. Agents: the Why blocks are context you may read; the rules themselves are the directives to follow.

---

## Table of Contents

1. [Agent Ground Rules](#agent-ground-rules)
2. [Technical Debt](#technical-debt)
3. [Naming Conventions](#naming-conventions)
4. [General Coding Standards](#general-coding-standards)
5. [Application Scope](#application-scope)
6. [Configurability](#configurability)
7. [Code Readability](#code-readability)
8. [Official API Preference](#official-api-preference)
9. [Do Not Use](#do-not-use)
10. [Tables, Fields & Choices](#tables-fields--choices)
11. [Database Views](#database-views)
12. [System Properties](#system-properties)
13. [GlideRecord](#gliderecord)
14. [Performance at Scale](#performance-at-scale)
15. [GlideForm](#glideform)
16. [GlideAJAX](#glideajax)
17. [Script Includes](#script-includes)
18. [UI Policies](#ui-policies)
19. [Business Rules](#business-rules)
20. [Events](#events)
21. [Client Scripts](#client-scripts)
22. [UI Actions](#ui-actions)
23. [Access Control Lists (ACLs)](#access-control-lists-acls)
24. [Logging](#logging)
25. [Error Handling](#error-handling)
26. [Operational Hygiene](#operational-hygiene)
27. [Messages & i18n](#messages--i18n)
28. [Notifications](#notifications)
29. [Scheduled Jobs](#scheduled-jobs)
30. [Multi-row Variable Sets (MRVS)](#multi-row-variable-sets-mrvs)
31. [Attachments](#attachments)
32. [Service Catalog — Items & Record Producers](#service-catalog--items--record-producers)
33. [Update Sets](#update-sets)
34. [Flow Designer](#flow-designer)
35. [CMDB](#cmdb)
36. [UI Builder (Next Experience)](#ui-builder-next-experience)
37. [Service Portal — Widgets](#service-portal--widgets)
38. [Service Portal — AngularJS Providers](#service-portal--angularjs-providers)
39. [Service Portal — Server Communication](#service-portal--server-communication)
40. [Service Portal — Client-Side State](#service-portal--client-side-state)
41. [Service Portal — SCSS](#service-portal--scss)
42. [Service Portal — Styling Conventions](#service-portal--styling-conventions)
43. [Service Portal — Accessibility (WCAG)](#service-portal--accessibility-wcag)
44. [Service Portal — Moment.js i18n](#service-portal--momentjs-i18n)
45. [Automated Test Framework (ATF)](#automated-test-framework-atf)
46. [Import Sets & Transform Maps](#import-sets--transform-maps)
47. [Integrations — General](#integrations--general)
48. [Integrations — Scripted REST API](#integrations--scripted-rest-api)
49. [Integrations — Integration Hub & Custom Spokes](#integrations--integration-hub--custom-spokes)
50. [Integrations — OAuth 2.0](#integrations--oauth-20)
51. [Integrations — LDAP User Import](#integrations--ldap-user-import)
52. [Integrations — Security](#integrations--security)

---

## Agent Ground Rules

These standards exist to remove guesswork. Where ambiguity remains anyway, **confirm with the user instead of guessing** — but only at the decision points below. Asking about everything is as unhelpful as asking about nothing; one consolidated question beats five small ones.

**Confirm before:**

- Creating a **new table**
- Creating a **new Script Include** when an existing custom SI could plausibly own the logic (see [Reuse Before You Create](#script-includes))
- Creating or modifying **ACLs, roles, or anything security-relevant**
- Any **destructive or mass operation** — deletes, `updateMultiple()`/`deleteMultiple()`, data migration
- Creating a **new application scope**, or putting anything in global scope (see [Application Scope](#application-scope))
- Creating a **database index** or other instance-wide performance change
- Building project infrastructure such as a **Tier 1 logger** (see [Logging](#logging))
- **Deviating from any rule in this document**

**Do not confirm for:** routine artifacts that follow these standards — adding a method to the correct SI, a Business Rule built per the rules, system properties, messages, UI Policies. Just build them correctly.

---

## Technical Debt

Agents accrue debt silently — a shortcut here, a skipped test there — and the cost surfaces months later. The directive is the inverse of how an agent defaults: **recognise debt and surface it; never bury it.**

**Stop and confirm before incurring structural debt.** Treat these as [Agent Ground Rules](#agent-ground-rules) confirm-before gates:

- The only way to make something work is to **modify a baseline/OOB record** (Business Rule, Script Include, UI Policy, view) or change a **base/extended table** (e.g. `task`). Surface the trade-off — upgrade risk, blast radius — and let the user decide rather than proceeding (see [Do Not Use](#do-not-use)).
- The clean path is blocked and the only route is a **documented anti-pattern** — a synchronous AJAX call, DOM access, a nested GlideRecord, a dot-walk past three levels, a hardcoded sys_id. Name it as debt, propose the correct approach, and only take the shortcut on explicit acknowledgement.
- A change **leaves a known gap** — missing ATF coverage, an untranslated user-facing string, a `TODO` the requirement implies but time didn't allow.

**When debt is taken on deliberately, leave a marker.** A code comment stating *what* was deferred and *why*, plus a backlog/story reference where the engagement tracks one. Invisible debt is the expensive kind; a flagged shortcut is a decision, an unflagged one is a landmine.

**Do not gold-plate, either.** The opposite failure is manufacturing scope — speculative configurability, abstractions for a second case that does not exist yet, defensive code for inputs that cannot occur. Match effort to the requirement. Flag genuine debt; do not invent work to avoid imagined debt.

<details><summary><b>Why make this a rule?</b></summary>

- **Silent debt compounds** — a shortcut nobody recorded is indistinguishable from an intentional design choice to the next reader (human or agent), so it never gets revisited until it breaks. Naming it converts an invisible liability into a tracked, prioritisable item.
- **Modifying baseline records is the highest-interest debt on the platform** — it blocks the affected record from upgrading and can break in ways no test predicted; that is precisely why it warrants a human decision, not an agent's unilateral call.
- **Gold-plating is debt too** — every speculative abstraction is more surface to read, test, and maintain for a requirement that may never arrive. "Match effort to the requirement" cuts both directions.

</details>

---

## Naming Conventions

| Artifact | Convention | Example |
|---|---|---|
| PREFIX | Engagement-specific | `SN` or your client prefix |
| Tables | `snake_case` singular | `my_asset` |
| Fields | `snake_case` | `assigned_group` |
| Script Includes | `PascalCase` | `IncidentService`, `IncidentServiceAjax` |
| Business Rules / Client Scripts | `PREFIX - Description` | `SN - Set Priority on Create` |
| Functions / variables | `camelCase` with type hint | `grIncident`, `membersArr` |
| Glide object variables | Glide-type prefix + table/purpose | `grUser` (GlideRecord/GlideRecordSecure on sys_user), `gaIncident` (GlideAggregate), `gdtStart` (GlideDateTime) |
| Constants | `UPPERCASE_SNAKE` | `MAX_RETRY_COUNT` |
| Widget name | Title Case | `My Task Board` |
| Widget ID | `kebab-case` | `my-task-board` |
| Update sets | `PREFIX - STRY# - Description #00N` | `SN - STRY001 - Incident Form Changes #001` |
| Flow actions / subflows | `PREFIX - Action Name` | `SN - Add Movie to Radarr` |
| Many-to-many (join) tables | `m2m` segment after the scope/`u_` prefix | `u_m2m_group_asset` |
| Data-lookup tables (extend `dl_matcher`) | `dl` segment after the scope/`u_` prefix | `u_dl_assignment` |

> Join and lookup tables earn a role segment so their utilitarian purpose is obvious at a glance: `u_m2m_*` for many-to-many join tables, `u_dl_*` for data-lookup tables (which extend `dl_matcher` to drive Data Lookup & Record Matching). In a scoped app the application scope prefix replaces `u_`; the `m2m` / `dl` segment still applies.

---

## General Coding Standards

- Use `getUniqueValue()` for the current record's sys_id; `getValue('field')` for reference field sys_ids
- Never dot-walk sys_ids — dot-walking a field returns a `GlideElement` object, not a string value
- Server-side array iteration: prefer `for` / `map` / `filter` / `reduce` / `sort`; `while` for `.next()` loops. Avoid `forEach` server-side — not because it fails, but because you cannot `break` out of it and it invites side-effect loops where `map`/`filter`/`reduce` state intent directly
- Constants Script Include: use `Object.freeze`, `UPPER_CASE` for category keys, `lower_snake_case` for values
- Use `GlideDateTime` server-side; pass Unix ms timestamps to the client
- Use `GlideRecordSecure` for any Script Include callable from the client side
- Widget server scripts must delegate all business logic to Script Includes — no logic directly in the widget
- Wrap single-context scripts (transform map scripts, background scripts, ad-hoc scripts) in a self-executing function `(function() { ... })();` to prevent global scope leakage. Business Rules and Client Scripts are already wrapped by the platform default — keep the default wrapper intact.
- Never hardcode the instance URL — read it from the platform (`gs.getProperty('glide.servlet.uri')` server-side); hardcoded URLs break on every clone and rename
- Prefer `getDisplayValue()` over hardcoded display field names (`gr.cmdb_ci.getDisplayValue()` instead of `gr.cmdb_ci.name`) so code survives dictionary display-field changes.

### Dates, Times & Timezones

- The database stores every datetime in **UTC**. `getValue()` returns the raw UTC value; `getDisplayValue()` returns it in the **session user's timezone and format**. Know which one you are holding at all times — most timezone bugs are one of these used as the other
- Do date math with **GlideDateTime methods** (`addSeconds()`, `addDays...()`, `before()`/`after()`, `compareTo()`) — never with string slicing or manual offset arithmetic
- GlideDateTime exposes explicit **`...UTC` and `...LocalTime` method variants** — pick one deliberately; mixing them silently shifts values by the user's offset
- **Scheduled Jobs and scheduled Flows: always set the Time zone field explicitly.** An unset timezone follows the system default, which rarely matches the business schedule the cron expression was written for — a 07:30 job is meaningless until you say 07:30 *where*
- Client side stays on the existing rule: pass **Unix ms timestamps**, never formatted date strings
- **Match the JavaScript level to the runtime** — use modern JS (`const`/`let`, arrow functions, template literals) only where the engine supports it: UI Builder client scripts, and **scoped server code** (the ES12 engine has been available per application since Tokyo — confirm it is enabled for the app). **Global scope historically ran ES5 (Rhino); since Xanadu, ES12 is also available there for many script types (Script Includes, Business Rules, Fix Scripts) — though not universally (background scripts, for instance, still lack the toggle), so confirm per script rather than assuming.** Anything that must run everywhere sticks to classic ES5 style. The safe baseline when unsure is ES5; never mix styles within one artifact.

<details><summary><b>Why these rules?</b></summary>

- **Never dot-walk sys_ids** — `gr.assigned_to.sys_id` forces the platform to query and instantiate the *referenced* record just to read an ID that `getValue('assigned_to')` already holds on the current row. It returns a `GlideElement` (not a string) and costs a needless database round trip per row.
- **Avoid `forEach` server-side** — it runs fine; the objection is that `forEach` cannot `break`, so it always walks the entire array even after you've found what you need, and it encourages side-effect loops where `map`/`filter`/`reduce` state the intent directly. GlideRecord result sets aren't arrays at all — they're iterators, which is why `while (gr.next())` is the correct shape there.
- **`Object.freeze` constants** — without freezing, any script can silently mutate a shared constant at runtime; with it, accidental writes fail instead of corrupting every later reader.
- **`GlideDateTime` server-side / Unix ms to the client** — server date strings are formatted per user locale and timezone, so passing them around invites parsing bugs. An epoch-milliseconds number is unambiguous in both directions.
- **`GlideRecordSecure` for client-callable SIs** — anything callable from the browser is an attack surface: parameters can be forged. `GlideRecordSecure` enforces ACLs on every row and field it touches, so a tampered call can't read or write what the user's roles don't allow.
- **Widgets delegate to Script Includes** — logic in a widget server script can only ever run in that widget; the same logic in an SI is reusable from BRs, jobs, other widgets, and tests, and can be reviewed in one place.

</details>


---

## Application Scope

**All new functionality is built in an application scope. Global is the exception, never the default.**

- Scopes are the platform's tracking mechanism for "what was added on top of the system" — everything custom is identifiable, exportable, and upgrade-isolated. Work dumped into the default global application loses all of that.
- A user adding functionality should rarely, if ever, be touching global scope. If something genuinely must live in global (rare — certain platform extension points), create a **dedicated custom application in global scope** so the work is still tracked as a named application. Never add artifacts to the default [Global] application.
- **Cross-scope access:** expose capability deliberately — a documented Script Include API or a Scripted REST endpoint — rather than opening cross-scope table access. Set *Accessible from* consciously at creation (it cannot be changed later on actions/subflows).
- Scoped runtime differences are real: some global-only APIs are unavailable or behave differently in scope. When a script fails in scope but worked globally, check the scoped API documentation before reaching for workarounds.

<details><summary><b>Why scope-first?</b></summary>

- **Traceability** — a scope answers "what did we build?" instantly; global custom artifacts mixed with baseline take archaeology to identify.
- **Upgrade isolation** — scoped apps declare dependencies and version as units; global customisations entangle with platform upgrades.
- **Conflict prevention** — scope namespacing makes name collisions with other apps (and future ServiceNow features) structurally impossible.

</details>

---

## Configurability

A single principle ties together [System Properties](#system-properties), the no-hardcoding rule, and scope discipline: **anything that varies by environment, deployment, or operator choice is configuration, not a literal baked into code.** If a value could differ between dev/preprod/prod, or might need changing without a code edit, it does not belong as a hardcoded string.

What this covers in practice:

- **Instance URLs** — read from the platform (`gs.getProperty('glide.servlet.uri')`), never hardcoded; covered in [General Coding Standards](#general-coding-standards).
- **Hardcoded sys_ids are a defect.** A sys_id of a specific group, user, or record pasted into a script breaks the moment that record is rebuilt in another environment or the person leaves. Resolve the record by a stable key at runtime, or make the sys_id **configuration** (a system property or a config-table row) so it is set per environment in one place.
- **Endpoints, thresholds, feature toggles, retry counts, batch sizes** — values an operator might tune live in properties (or a config table), not constants in a Script Include.
- **Secrets are never configuration values in `sys_properties`.** Credentials and tokens belong in **Connection & Credential aliases** (the credential store), referenced by integrations — not in a property, not in a script. See [Integrations — Security](#integrations--security).

Route each value to the right mechanism — set-once/instance-wide → **System Property**; per-user → **User Preference**; many instances of the setting → **config table** — using the decision table in [System Properties](#system-properties). The environment-specific ones (SSO IdP, MID Server names, external base URLs) must also appear on the promotion checklist so the correct value is set in each environment (see [Promotion Discipline](#promotion-discipline)).

<details><summary><b>Why treat this as one principle?</b></summary>

- **Clone-and-promote is the test.** A scoped app that is properly configurable installs into a fresh instance and runs once its properties are set; one riddled with hardcoded URLs and sys_ids needs a code edit per environment, which defeats versioned promotion.
- **A hardcoded sys_id is invisible until it breaks.** Nothing flags it; it simply points at nothing (or the wrong thing) in the next instance. Making it configuration turns a silent cross-environment failure into a visible, settable value.

</details>

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
function deleteIfCanceled(grTask, defaultAnswer, stateValue) { /* ... */ }
```

Short loop counters (`i`, `j`) are fine. One- or two-letter names for anything else are not.

### Function Design

- **Single responsibility** — every function does one thing. If the name needs "and" to describe it, split it. This applies inside Script Includes too: many small focused methods beat one method that orchestrates everything inline.
- **Prefer a ternary for simple conditional assignment** — `var label = isVip ? 'Priority' : 'Standard';` reads better than a four-line `if/else` that only assigns. Use `if/else` when branches have side effects or logic; **never nest ternaries** — a nested ternary is always less readable than the `if/else` it replaced.
- **Private helpers start with `_`** — inside a Script Include, methods not intended to be called from outside the class are prefixed with an underscore (e.g. `_recalculateTotals`). The platform does not enforce privacy; the prefix is the documented signal "call this from inside this SI only," and reviewers (and agents) must treat it as such.
- **Nested / inner functions are fine in Script Includes** — a parent method may define small inner helper functions when they are only meaningful to that method. The single-responsibility goal still applies to each inner function; if an inner helper is useful to more than one method, promote it to a `_private` method on the class.
- **JSDoc on every method** — the [JSDoc Headers on Functions](#code-readability) rule above is not optional polish. Agents: generate the header with every method you write; a method without `@param`/`@return` documentation is incomplete.

### Cache Repeated Function Results

If a function returns the same value throughout a code block, call it once and store the result. This improves both readability and performance.

```javascript
// ❌ BAD — four identical calls
if (gs.getUserID() == grCurrent.getValue('assigned_to') ||
    gs.getUserID() == grCurrent.getValue('u_coordinator') ||
    gs.getUserID() == grCurrent.getValue('caller_id') ||
    gs.getUserID() == grCurrent.caller_id.manager.toString()) { /* ... */ }

// ✅ GOOD — single call, named intermediates
var currentUserId = gs.getUserID();
var isOwner       = currentUserId == grCurrent.getValue('assigned_to');
var isCoordinator = currentUserId == grCurrent.getValue('u_coordinator');
var isCaller      = currentUserId == grCurrent.getValue('caller_id');
var isCallerMgr   = currentUserId == grCurrent.caller_id.manager.toString();

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

if (!saveRecord(grCurrent)) {
    gs.addErrorMessage(gs.getMessage('record.save_failed'));
}
```

### Guard Against Undefined Values Before Use

Dot-walking through empty references, reading `vaVars` that may be coerced to `"null"`, or accessing fields that may not exist will produce unpredictable results and warning messages. Check before you use.

```javascript
// ❌ BAD — throws warnings if cmdb_ci or installed_on is empty
var tableName = current.cmdb_ci.installed_on.sys_class_name;

// ✅ GOOD — getElement() officially supports dot-walked paths and returns a guardable element
var classEl = current.getElement('cmdb_ci.installed_on.sys_class_name');
if (classEl && !classEl.nil()) {
    var tableName = classEl.toString();
    // safe to use
} else {
    gs.warn('[MyBR] sys_class_name unavailable for ' + current.getDisplayValue());
}
```

When several fields are needed from the referenced record, call `getRefRecord()` once and check `isValidRecord()` instead of guarding each path. Note that `getValue('field')` exists on **GlideRecord only** — there is no `GlideElement.getValue(field)`, so it cannot be chained onto a dot-walk.

**vaVars gotcha:** null values in `vaVars` can be coerced to the literal string `"null"` — which is *truthy*, so a plain truthy check passes exactly the case being guarded against. Check explicitly: `if (val && val != 'null' && val != 'undefined')`.

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
- **Reference-field hygiene** — `current.assigned_to = grUser` (passing a `GlideRecord`) silently coerces in ways that differ from `setValue('assigned_to', grUser.getUniqueValue())` and can break on upgrade
- **Reviewability** — the principle makes intent explicit at the call site, which is the single biggest factor in code-review speed for ServiceNow scripts

---

## Do Not Use

Consolidated quick-reference of banned or near-banned patterns. Each links back to the section with the full rule and reasoning.

| Never (or almost never) use | Use instead | Section |
|---|---|---|
| `eval()` | Direct code; redesign | [Code Readability](#code-readability) |
| `getReference()` (any form) | GlideAJAX | [GlideAJAX](#glideajax) |
| Synchronous GlideRecord / GlideAjax client-side | GlideAJAX with callback | [Client Scripts](#client-scripts) |
| DOM manipulation (`document.*`, jQuery, `g_form.getElement()`/`getControl()`, `gel()`) in Client Scripts | `g_form` value/state API | [Client Scripts](#client-scripts) |
| `getRowCount()` for counting | `GlideAggregate` | [GlideRecord](#gliderecord) |
| Nested GlideRecord loops | Hash map / `addJoinQuery()` | [GlideRecord](#gliderecord) |
| `forEach` server-side | `map`/`filter`/`reduce`; `while` for `.next()` | [General Coding Standards](#general-coding-standards) |
| Dot-walking sys_ids | `getValue('field')` | [General Coding Standards](#general-coding-standards) |
| Collecting `gr.field` / `gr.sys_id` objects into arrays or JSON | `getValue()` / `getUniqueValue()` at the point of collection | [GlideRecord](#gliderecord) |
| Nested ternaries | `if/else` | [Code Readability](#code-readability) |
| `current.update()` in a before BR | Nothing — the save is coming | [Business Rules](#business-rules) |
| `setWorkflow(false)` without documented reason | Let automation run | [Business Rules](#business-rules) |
| `gs.sleep()` | Wait-for-condition (flows); event-driven design | [Flow Designer](#flow-designer) |
| `gs.log()` / `console.log()` in permanent code | Tiered logging APIs | [Logging](#logging) |
| Hardcoded sys_ids | Properties, queries by attribute | [Script Includes](#script-includes) |
| Hardcoded instance URLs (anywhere) | `glide.servlet.uri` property; instance suffix in notifications | [General Coding Standards](#general-coding-standards) |
| Renaming a used email template | Leave the name; create new | [Notifications](#notifications) |
| Workflows (legacy) for new automation | Flow Designer | [Flow Designer](#flow-designer) |
| Merging update sets | Batching | [Update Sets](#update-sets) |
| Backing out update sets | Roll forward with a hotfix set | [Update Sets](#update-sets) |
| Modifying OOTB Script Includes | New custom SI in your scope | [Script Includes](#script-includes) |
| Unprefixed Script Include calls | `new scope.ClassName()` always | [Script Includes](#script-includes) |
| GlideQuery in new code | GlideRecord | [GlideRecord](#gliderecord) |
| `getXML()` in GlideAjax | `getXMLAnswer()` | [GlideAJAX](#glideajax) |
| External data written directly to target tables | Import Set + Transform Map | [Import Sets & Transform Maps](#import-sets--transform-maps) |
| Copying attachments | Move or reference | [Attachments](#attachments) |

---

## Tables, Fields & Choices

Naming is covered in [Naming Conventions](#naming-conventions); this section covers how the columns themselves behave once created. These are platform mechanics that directly shape design decisions — and that generated code routinely gets wrong.

### Choice & State Fields

- **A State field stores its *value*, not its label.** On Task-derived tables State is an integer; the dropdown text is the display label. Code and queries operate on the value (`current.state == 2`), never the label.
- **Don't repurpose or renumber existing choice values.** Changing what an existing value *means* silently rewrites the meaning of every stored record and every script that tests it. Add new choices with new values instead.
- **Value vs. Sequence are different fields.** The choice *Value* is what gets stored; the *Sequence* only controls dropdown order. Reordering the list does not (and must not) change stored values.
- **State models on Task-based and custom tables follow the active/inactive convention:** values **< 7 are treated as active**, **≥ 7 as inactive**, for compatibility with legacy state-handling code. If you run out of active values below 7, use **negative numbers** rather than crossing the threshold. The mechanism that actually drives close/deactivate behaviour is the **`close_states`** (and `default_close_state`) dictionary attributes consumed by `TaskStateUtil` — set those when extending a state model rather than hardcoding numbers anywhere.
- **Express a custom state model as a frozen-constants Script Include** (per the Constants SI rule in [General Coding Standards](#general-coding-standards)) so code reads `States.ON_HOLD` instead of the literal `3`. Expose it to the client through a GlideAjax wrapper or a Display Business Rule + `g_scratchpad` (see [GlideAJAX](#glideajax)), not by duplicating the numbers client-side.

> For **open/closed queries**, still filter on the `active` field rather than enumerating state values — that rule lives in [GlideRecord](#gliderecord). This subsection governs how you *design* the state/choice model; that one governs how you *query* it.

### Field Value Strategy: Default vs. Calculated vs. Derived

Three different mechanisms put a value in a field. They are not interchangeable, and the most common platform bug here is treating a default as if it were calculated.

| Mechanism | When it runs | Re-evaluated on update? | Use for |
|---|---|---|---|
| **Default value** | On insert, and computed for *display* on the new-record form | **No** — set once, never recomputed | An initial/seed value the user may then change |
| **Calculated value** (dictionary *Calculated* flag) | On every insert **and** update | **Yes** — always overwrites | A value that is always a pure function of this record's other fields |
| **Derived / dot-walked field** (added via Form Layout) | Read live through a reference — not stored at all | Always current; nothing to recompute | Showing a value that lives on a *referenced* record |

- **The default-value trap:** on a *new-record form* the `current` object is mostly empty, so a `javascript:` default that reads `current.some_field` produces a blank — and if the user saves that blank-derived value, it sticks, because the default is **not** re-evaluated on insert once the field holds anything. Defaults are for static or independent initial values, not for deriving from other fields.
- **Prefer a derived (dot-walked) field over a custom field that just copies a referenced value.** If you find yourself scripting a field to mirror `request_item.short_description`, delete the field and add the dot-walked field on the form instead — zero storage, zero sync logic, always current. The cheapest field is the one you never created.
- **Calculated fields run server-side only** and should be set read-only on the client so users don't type into a value the platform will overwrite.

Decision shortcut: *value from a referenced record* → derived/dot-walked (don't create a column); *value computed from this record's own fields, always current* → calculated; *seed value the user can edit* → default.

---

## Database Views

A Database View joins multiple tables for reporting. Before building one, check whether a **reference field plus dot-walk** already gives you what you need — it almost always does, and it is cheaper. Build a view only when you must report across tables that aren't connected by a usable reference.

When a view is genuinely warranted:

- **Prefix the view name with `dv_`** and let the rest name the joined tables (`dv_incident_problem`).
- **Put the smaller table (fewer rows) on the left/primary** side of the join — it makes the view materially cheaper to build.
- **Coalesce only on indexed fields**, and avoid **SQL reserved words** in the table short-labels used inside the view.
- **Views need their own ACLs.** Access to the underlying tables does **not** carry over — a user with rights to both source tables still can't read the view until you grant it.
- **Views are read-only** — you cannot insert or update through one.
- A Database View over large tables can be **compute-heavy**; treat building one as a confirm-first decision (see [Agent Ground Rules](#agent-ground-rules) / [Performance at Scale](#performance-at-scale)).

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

<details><summary><b>Why the split?</b></summary>

- **Properties are instance-wide and cached** — `gs.getProperty()` reads from cache, which is what makes them cheap; but *writing* a property flushes that cache across the instance. A value that changes often (or per record) written into `sys_properties` causes repeated cache flushes that degrade the whole instance — which is exactly why the rule says "set once, rarely changed, single instance."
- **User Preferences exist for per-user state** — they're keyed per user with a global default, so reinventing that on `sys_properties` means building name-mangling (`property.username`) the platform already does for you.
- **A settings table wins when there are N instances of a setting** — properties are a flat key/value namespace; the moment a setting varies per board/team/integration, rows in a table give you references, ACLs, and a UI for free instead of JSON stuffed into one property.

</details>


---

## GlideRecord

**General rules:**
- Use `getValue('field')` to extract field values — dot-walking returns a `GlideElement` object, not the value
- Variable naming: **Glide-type prefix + table/purpose** — `grUser` is a GlideRecord (or GlideRecordSecure) on `sys_user`, `gaIncident` a GlideAggregate on incident. The prefix tells the reader the API; the rest tells them the data. Standard prefixes: `gr` (GlideRecord and GlideRecordSecure), `ga` (GlideAggregate), `gdt` (GlideDateTime), `gd` (GlideDate), `gsa` (GlideSysAttachment). Non-Glide variables keep the type-hint style (`membersArr`, `configObj`).
- Never nest GlideRecord queries inside other GlideRecord loops — use hash maps or join queries

**Query efficiency:**
- Use `addEncodedQuery()` for complex queries instead of chaining `addQuery()` / `addOrCondition()`
- Use `GlideAggregate` for counting records — not `getRowCount()` (getRowCount retrieves all records first, causing performance issues at scale)
- Use `setLimit(1)` when only confirming existence — this tells the database to stop after one match instead of returning and counting the whole result set:
  ```javascript
  // ❌ BAD — retrieves every active incident just to check one exists
  var grInc = new GlideRecord('incident');
  grInc.addQuery('active', true);
  grInc.query();
  if (grInc.hasNext()) { /* ... */ }

  // ✅ GOOD — database returns at most one row
  var grInc = new GlideRecord('incident');
  grInc.addQuery('active', true);
  grInc.setLimit(1);
  grInc.query();
  if (grInc.hasNext()) { /* ... */ }
  ```
- Use `addJoinQuery()` instead of nesting a GlideRecord inside another GlideRecord loop
- Use Related List Query (RLQUERY) when filtering by a specific count of related records — `addJoinQuery()` can only test for existence (≥1), not exact counts

<details><summary><b>Why these query rules?</b></summary>

- **No nested GlideRecords** — a query inside a `while (grOuter.next())` loop is the classic N+1 problem: 10,000 outer rows means 10,001 database queries. Loading the lookup side once into a hash map (or using `addJoinQuery()`) turns that into 2 queries total. The difference is seconds vs. minutes on real data sets.
- **`addEncodedQuery()` for complex conditions** — an encoded query is copy-pasteable from a list filter (build it in the UI, copy query, paste in code), reads as one auditable string, and avoids subtle operator-precedence mistakes when mixing `addQuery`/`addOrCondition` chains.
- **`GlideAggregate` for counting** — `getRowCount()` only knows the answer after the platform has retrieved and instantiated every row; `GlideAggregate` asks the database for `COUNT(*)` and transfers one number.
- **`setLimit(1)` for existence checks** — same principle: tell the database to stop at the first match instead of materialising the full result set you're about to throw away.

</details>


**Always test queries on a sub-production instance before deploying to production.** An invalid encoded query silently drops the invalid condition and may return all records — running `update()`, `deleteRecord()`, or `deleteMultiple()` on that result can cause data loss.

**Active field vs. state field:**
- When determining whether a record is open or closed, query the `active` field — not individual state values. This leverages ServiceNow's OOB state-to-active mapping configured per table, keeping scripts resilient to state value changes.
- Only query specific `state` values when the business logic requires a particular state (e.g. "In Progress" vs "On Hold"), not for simple open/closed checks.
- If the target table does not have an `active` field, then fall back to state value checks.
```javascript
// ✅ GOOD — open vs. closed check
grInteraction.addQuery('active', true);

// ❌ BAD — hardcoding state values for a simple open/closed check
grInteraction.addQuery('state', '!=', '7');
grInteraction.addQuery('state', 'NOT IN', '3,7,8');

// ✅ OK — querying a specific state for business logic
grIncident.addQuery('state', '2'); // Need specifically "In Progress"
```

### GlideElement — Extract Early, Hold Deliberately

Every field access on a GlideRecord (`gr.field`, any dot-walk) returns a **GlideElement** — it is the platform's field wrapper, not an alternative API you opt into. The standard is about *when to let go of it*:

- **Default: extract immediately** — `getValue()` / `getDisplayValue()` / `getUniqueValue()` at the point of access, then operate on plain strings and numbers. Direct element comparisons in conditions stay fine (`if (current.state == 6)`) — see [Official API Preference](#official-api-preference)
- **The aliasing trap (the reason the rule exists):** a GlideElement is a **live reference to the query cursor's current row**. Collect elements in a loop and every entry points at the same object — after the loop they all hold the *last* row's value, and `JSON.stringify` on them misbehaves:

  ```javascript
  // ❌ BAD — N references to one live element; every entry ends up as the last row
  var idsArr = [];
  while (grTask.next()) {
      idsArr.push(grTask.sys_id);
  }

  // ✅ GOOD — primitives copied out at the point of collection
  var idsArr = [];
  while (grTask.next()) {
      idsArr.push(grTask.getUniqueValue());
  }
  ```

- **Hold the element deliberately** only for the operations that exist nowhere else: `changes()` / `changesTo()` / `changesFrom()` (Business Rules), `nil()`, `getRefRecord()` (hop to the referenced record), `getED()` (dictionary metadata), `dateNumericValue()` (epoch ms straight off a date/time field — pairs with the Unix-ms-to-client rule), and the guarded dot-walk read via `getElement('a.b.c')`
- **Never pass a GlideElement across a boundary** — into a JSON payload, an array, an event parm, or anything that outlives the loop iteration. Coerce first

> **Name-collision warning:** server-side `GlideElement` and `GlideRecord.getElement()` have nothing to do with the DOM — they are pure data APIs. The *client-side* `g_form.getElement()` is an unrelated method that returns a DOM node and falls under the no-DOM rule in [Client Scripts](#client-scripts).

### Snapshot a Record to a Plain Object

To copy a whole record's field values into a plain JavaScript object — instead of hand-writing a `getValue()` per field, or (worse) pushing live GlideElements into an array — use the OOB `GlideRecordUtil`:

```javascript
var snapshot = {};
new GlideRecordUtil().populateFromGR(snapshot, grRecord, { sys_created_on: true, sys_updated_on: true });
// populateFromGR() fills the object you pass in: snapshot is now field → value,
// safe to JSON.stringify or hand across a boundary (no live GlideElements inside)
```

`getFields(gr)` returns just the list of populated field names if that's all you need. (Some older guides cite a `.toHashMap()` method here; `populateFromGR()` is the current documented helper — confirm specifics against the [API reference](https://github.com/ServiceNow/ServiceNowDocs).)

### GlideQuery

**Use GlideRecord. Do not introduce GlideQuery into new code.** GlideQuery is an alternative API, not a successor — maintain it where you find it in existing code, but these standards build on GlideRecord.

<details><summary><b>Why not GlideQuery?</b></summary>

- **It is a wrapper over GlideRecord**, so it always carries overhead the underlying API does not — and these standards prefer the speed.
- **Its main selling point is mitigated here.** GlideQuery's fail-fast behaviour (throwing on invalid field names where GlideRecord silently drops the condition) protects developers from typo-class mistakes — a real GlideRecord trap, covered by the sub-production testing rule above. Code written to these standards, with queries tested before deployment, gets that protection without the wrapper.
- **It is not the platform direction.** In the words of GlideQuery's own creator: "GlideRecord is never going away. GlideQuery is merely an alternative API available." Standardising on the alternative buys inconsistency with every other pattern in this document for no platform-strategic gain.
- **It is itself a global-scope Script Include** (baseline since Paris — no plugin needed on current releases, though very old instances distributed it as an app). That means scoped code must call it as `new global.GlideQuery(...)` — and an unprefixed call fails exactly the way the scope-prefix rule in [Script Includes](#script-includes) warns about. One more way for generated code to break subtly.
- If a project has deliberately adopted GlideQuery wholesale, that is a defensible team choice — but it is a deviation from these standards, and the never-mix-paradigms-in-one-artifact rule still applies.

</details>

---

## Performance at Scale

The [GlideRecord](#gliderecord) rules cover query hygiene; this section covers what changes when tables get big and jobs run long.

- **Indexes:** if a new query filters or sorts a large table on unindexed fields — especially if it shows up in *Slow Queries* — request a database index on those fields. Index creation on a large table is itself an impactful operation: schedule it and confirm with the user first (see [Agent Ground Rules](#agent-ground-rules)).
- **Order filters cheapest-first:** when a query mixes selective/indexed conditions with expensive ones (`CONTAINS` / `LIKE` / `STARTSWITH`), add the cheap conditions first so the costly comparison runs on a smaller candidate set. On a cold cache this can cut query time dramatically; once results are cached the order matters less — write for the cold path. An unindexed `CONTAINS` on a large table is the classic offender, and pairs with the index rule above.
- **Chunk large jobs:** never process tens of thousands of rows in one unbounded loop/transaction. Window the work — `setLimit(N)` batches ordered by `sys_id` (cursor = last processed sys_id), or split by query slices — so each transaction stays well under platform quotas and a failure loses one window, not the whole run.
- **`updateMultiple()` / `deleteMultiple()`** beat per-row loops for uniform changes, but inherit the encoded-query danger: an invalid condition silently broadens the result. Test the exact query on sub-production first, and treat these as confirm-first operations.
- **Cache lookups:** anything you would query repeatedly inside a loop belongs in a hash map built once before the loop (same principle as the nested-query ban). `gs.getProperty()` is cache-backed and fine to call freely.
- **Async when nobody is waiting:** heavy post-processing belongs in async BRs, events, or scheduled work — never in the user's transaction (see [Business Rules](#business-rules)).
- **Watch the evidence:** *Slow Queries*, transaction logs, and scheduled-job duration trends are the feedback loop — review them while developing, not after go-live (see [Operational Hygiene](#operational-hygiene)).

---

## GlideForm

- Client-side only — always accessed via the global `g_form` object
- Never use `g_form` in UI Policies — use a Client Script if scripting is required

<details><summary><b>Why keep scripts out of UI Policies?</b></summary>

- **Declarative actions are upgrade-safe and self-documenting** — a reviewer (or an upgrade-impact tool) can read a UI Policy's conditions and actions without executing anything. Script buried in a policy's *Execute if true* hides logic where nobody looks for it.
- **Execution-order surprises** — UI Policies and Client Scripts run at defined but different points in form lifecycle; mixing `g_form` mutations into policies creates ordering interactions that are painful to debug. Keeping scripting in Client Scripts means all imperative form logic lives in one reviewable place.

</details>


### setValue on Reference Fields

When setting a reference field with `g_form.setValue()`, **always pass the display value as the third argument**. Omitting it forces a synchronous AJAX round-trip to the server to fetch the display value, blocking the browser.

```javascript
// ❌ BAD — synchronous server call to fetch display value
g_form.setValue('assigned_to', userSysId);

// ✅ GOOD — no server call needed
g_form.setValue('assigned_to', userSysId, userDisplayName);
```

When the display value isn't known client-side, retrieve both via a single GlideAJAX call and set them together in the callback.

### setVisible() vs. setDisplay()

Both hide a field client-side, but they differ in what happens to the space it occupied:

- `g_form.setDisplay(field, false)` removes the field **and collapses** the empty space — the rest of the form closes up. This is the usual choice.
- `g_form.setVisible(field, false)` hides the field but **leaves the blank gap** where it was. Use it only when you deliberately want the layout position preserved.

Hiding a field with either method does **not** clear its value — see the gotcha under [UI Policies](#ui-policies).

---

## GlideAJAX

**Choose the right pattern by trigger:**

| Trigger | Preferred approach |
|---|---|
| `onChange` (field change) | GlideAJAX |
| `onLoad` (before record loads) | Display Business Rule + `g_scratchpad` (not available in Service Portal) |
| After save | Business Rule or Flow |

**Avoid:**
- `getReference()` with callback — avoid; GlideAJAX answers the same question with a leaner payload
- Client-side GlideRecord with callback — avoid, for the same reason
- `getReference()` without callback — **never** (synchronous, blocks the browser)
- Client-side GlideRecord without callback — **never** (synchronous, blocks the browser)

**Implementation rules:**
- Client side: always use `getXMLAnswer()` + `JSON.parse()` to handle the response — **never `getXML()`**, which is the older pattern that returns the full XML response document and forces manual DOM walking for the same answer
- Max 1 AJAX call per client script
- For Service Catalog, always use GlideAJAX — the item form is not backed by a record before submission, so Display BRs / `g_scratchpad` cannot supply data

<details><summary><b>Why these AJAX rules?</b></summary>

- **Synchronous calls freeze the browser** — `getReference()` / GlideRecord without a callback block the UI thread until the server answers; on a slow connection the form simply hangs. Every server trip from a Client Script must be asynchronous.
- **`getXMLAnswer()` + `JSON.parse()`** — `getXMLAnswer` hands you just the `answer` attribute (skipping manual XML DOM walking), and returning one JSON object lets a single round trip carry every value the script needs, parsed in one line.
- **Max 1 AJAX call per Client Script** — each call is a full network round trip triggered by user interaction. Two calls double the latency the user feels and can race each other; one consolidated AJAX SI method returning a single JSON payload is faster and deterministic.
- **Display BR + `g_scratchpad` for onLoad** — the form is already making a server trip to load the record; the Display BR piggybacks the extra data on that same trip, so the form arrives with everything it needs and zero additional requests.

</details>


---

## Script Includes

- Must be a **class**, not a standalone function
- Avoid generic names (e.g. `AbcUtils`) — name reflects the target table or responsibility
- No `eval`; no hardcoded sys_ids
- Single responsibility — separate functions for reusability across server-side components
- **Always call Script Includes with the scope prefix** — `new global.SNIncidentService()`, `new x_vaultflip.VaultService()` — even from within the same scope. Cross-scope calls *require* the prefix and fail without it (often silently, or with a misleading error that points nowhere near the real cause); prefixing everywhere costs nothing, makes every call site unambiguous about where the class lives, and means code keeps working when it is copied into another scope's context (flows, fix scripts, background scripts).

**Server-side SI:**
- One SI per target table
- Named `[PREFIX][TargetTable]Service` e.g. `SNIncidentService`

**AJAX SI:**
- Named `[PREFIX][TargetTable]ServiceAjax` e.g. `SNIncidentServiceAjax`
- Extends `AbstractAjaxProcessor`
- No `initialize()` method
- Thin wrapper only — the standard call chain is **Client Script → AJAX (client-callable) SI → non-client-callable server SI**. The AJAX class reads/validates parameters and delegates; all real logic lives in the server SI where BRs, jobs, flows, and tests can also call it
- **Trivial-lookup exception:** tiny, logic-free reads that a Client Script cannot do itself (e.g. returning a system property value) may live directly in the AJAX SI — but the moment there is actual logic, it routes through the server SI
- Returns JSON, not plain strings
- Always coerce parameters at the boundary: `var value = String(this.getParameter('sysparm_value'));` — and name every GlideAjax parameter with the `sysparm_` prefix

<details><summary><b>Why these Script Include rules?</b></summary>

- **Class, not a loose function** — the platform's client-callable machinery (and `AbstractAjaxProcessor`) expects a prototype whose name matches the SI record; classes also give you `this`-scoped state and extension. Bags of global functions can't be safely extended or called from the AJAX layer.
- **One SI per table, named `[PREFIX][Table]Service`** — everyone (including an AI assistant) can predict where the logic for a table lives without searching. Generic `Utils` grab-bags grow until nobody knows what's safe to change.
- **AJAX SI is a thin wrapper** — the AJAX layer is transport + security only. If logic lives in the server SI, it's callable from BRs, jobs, flows, and tests; if it lives in the AJAX class, it's reachable only from a browser.
- **No `initialize()` in AJAX SIs** — `AbstractAjaxProcessor` supplies its own `initialize()` that wires up request parameters; overriding it breaks `getParameter()` silently.
- **`String(this.getParameter(...))`** — parameters arrive as Java string objects, not JavaScript strings; comparisons and `JSON.parse` can misbehave until coerced. Coerce once at the boundary and everything downstream behaves.

</details>

### Reuse Before You Create

**Before creating any new Script Include or method, check what already exists.** Duplicated logic is the fastest way to rot a codebase: two copies drift, and every future fix lands in only one of them. This rule is directed at human developers and AI agents equally — agents are especially prone to generating a fresh SI for every task.

The check is two-step, in order:

1. **Does a relevant Script Include already exist?** Search by the naming convention first (`[PREFIX][TargetTable]Service` — the table you are working on tells you the expected name), then search SI names and contents for the domain term. If it exists, you are *adding to it*, not creating a sibling.
2. **Does the function/method already exist on it?** Read the existing SI's methods before writing. If the capability exists, call it. If it almost exists, extend or parameterise the existing method rather than writing a near-duplicate beside it. Only when the SI exists but the capability genuinely does not: **add a new method to the existing SI** — do not create a new Script Include for one new function.

Creating a *new* SI is correct only when no SI owns that table/responsibility yet (per the one-SI-per-table rule above).

**Discovery takes judgment, not just the naming convention.** The `[PREFIX][Table]Service` convention is the *first* place to look, not the only one — previous developers or agents may not have followed it. Also search Script Include names, descriptions, and contents for the table name and the business/domain terms, and skim near-miss custom SIs to judge whether the new logic plausibly belongs in one of them. If it is a genuine judgment call which existing SI should own it, confirm with the user (see [Agent Ground Rules](#agent-ground-rules)) rather than guessing.

**Never modify out-of-the-box Script Includes.** Customising a baseline SI breaks upgrade safety and is forbidden. Extending an OOTB SI (class extension) is technically possible and occasionally the right tool, but the default for new logic is a **separate custom SI in your scope** that calls or wraps platform APIs as needed.

**The Constants SI is a singleton — never duplicate it.** The entire purpose of a central constants Script Include is one authoritative home for shared values. If a constants SI exists for the scope, every new constant goes in it. A second constants SI (or constants scattered into other SIs) silently forks the source of truth and defeats `Object.freeze` discipline. Agents: search for an existing constants SI before declaring any new constant container.



---

## UI Policies

- **Prefer UI Policies over Client Scripts** for controlling field visibility, mandatory state, and read-only state
- If scripting is required, use a **Client Script** instead of a UI Policy — **except** for simple date/time validations (see below)
- Use a single UI Policy for initialization
- Bundle multiple field actions into a single UI Policy where possible
- Mandatory fields **cannot** be hidden
- Mandatory fields **cannot** be made read-only

> **Hiding a field does not clear its value.** A value entered while a field was visible stays in the field when a UI Policy (or `g_form.setDisplay` / `setVisible`) later hides it — it is still submitted, still written to the database, and can still trigger Business Rules and be read by scripts. If hiding must also clear, clear the value explicitly. And because UI Policies are client-side only, a value that must *never* be set under a condition is enforced with a Data Policy or Business Rule (see [UI Policy vs. Data Policy](#ui-policy-vs-data-policy) below), not by hiding the field.

**Date/Time validation exception:**
Simple date/time validations in record producers or catalog items may use a UI Policy with a scripted message, because handling timezone and user format correctly in a Client Script is complex. Acceptable validations:
- Date/time is before or after another date/time
- Date/time is N days from now
- Date/time is older than N hours

**Catalog UI Policies:**
- Set the *When to apply* checkboxes correctly — determine whether the policy should run on the catalog item, the target record, or both

### UI Policy vs. Data Policy

UI Policies act **client-side only** — they shape the form and nothing else. Records arriving through imports, REST/Table API, flows, or scripts never see them. When the rule is about **data integrity** (a field that must always be present, or must never change past a state), use a **Data Policy**: it enforces mandatory/read-only server-side on every write path, and can additionally be pushed to forms with *Use as UI Policy on client*.

Rule of thumb: cosmetics and UX → UI Policy; integrity → Data Policy (optionally surfaced on the form as well). Never hand-maintain the same rule as both — that is two records to drift apart.

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

- If an after BR updates the same record, it re-triggers before/after BRs on that table — guard by avoiding `current.update()`, or use a recursion flag (`gs.getSession().putClientData()` or a script-scoped variable)
- For bi-directional integrations, filter out updates by the integration user (see the Integrations — General section on loop prevention)
- Never modify `current` inside an **after** BR — changes are silently lost because the record is already committed; if you need to update the same record, use `GlideRecord` with `setWorkflow(false)` and `autoSysFields(false)` and accept the trade-offs

### Naming

Follow the standard: `PREFIX - Description` (e.g. `SN - Set Priority on Create`). Include the timing in the description if it aids clarity (e.g. `SN - Before - Validate Mandatory Fields`).

---

## Events

`gs.eventQueue()` is an architectural tool, not just a notification trigger. Use it to **decouple**: the Business Rule stays a thin detector ("this happened"), and a Script Action or notification responds asynchronously.

- **Register every event** in the Event Registry before queuing it; name it `prefix.table.action` (e.g. `sn.incident.escalated`)
- **Use events when** the side effect does not need to block the transaction: notifications, kicking off integrations, metrics, downstream record creation
- **Do not use events for** synchronous validation or anything the user must see in the same transaction — that is before/after BR territory
- The record reference *is* the payload — use `parm1`/`parm2` sparingly for context the responder cannot derive from the record
- **Every queued event must have a responder** (notification or Script Action). An event nobody listens to is pure waste — see [Operational Hygiene](#operational-hygiene) on detecting orphaned events

<details><summary><b>Why decouple with events?</b></summary>

- **Transaction speed** — the user's save returns as soon as the event is queued; the heavy work happens on the event processor.
- **Independent evolution** — adding a second responder (a new notification, an extra integration) requires zero changes to the BR that fires the event.
- **Failure isolation** — a failing responder doesn't abort the user's transaction the way a failing inline after-BR can.

</details>

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
- **No DOM manipulation** — do not use `document.getElementById()`, `jQuery`, or direct DOM access; use the `g_form` API exclusively. **"The g_form API" means its value/state methods** — `g_form.getElement()` and `g_form.getControl()` return DOM nodes and are part of the ban, as is the legacy `gel()` shorthand. Direct DOM manipulation breaks on form redesigns, is not supported in Service Portal or workspaces, and can be overwritten by the platform at any time

### Service Portal Considerations

- `g_scratchpad` (from Display BRs) is **not available** in Service Portal — use GlideAJAX or widget server scripts instead
- `onCellEdit` Client Scripts do not apply in Service Portal
- Test all Client Scripts in both the standard UI and Service Portal if both are in use

### Performance

- Client Scripts run on every form load/change for their table — keep them fast
- If an onChange script calls GlideAJAX, consider debouncing or guarding against rapid consecutive changes (e.g. check if the value actually changed before making the call)
- **UI Type: default to All (Desktop + Mobile)** — always create Client Scripts with UI Type = All unless the logic is genuinely desktop-only (e.g. DOM-adjacent behaviour that mobile does not render). A script left on Desktop-only silently does nothing for mobile users, and the resulting "validation works on my machine" bugs are expensive to trace. Restricting to one UI type is the documented exception, not the default.

### Naming

Follow the standard: `PREFIX - Description` (e.g. `SN - onChange - Set Category from Assignment Group`). Including the type in the name makes the Client Script list easier to scan.

---

## UI Actions

UI Actions put buttons, links, and context-menu entries on forms and lists. They are glue, not a home for logic.

**Core rules:**

- **Keep them thin** — a UI Action body is a condition check plus a Script Include call (server) or a `g_form` interaction plus submit (client). Business logic lives in the SI, exactly as for Business Rules
- **Always set the Condition field** — an unconditioned action appears everywhere the table does, including places it makes no sense
- **Set `Action name`** (`lower_snake_case`, e.g. `sn_request_approval`) on any action submitted programmatically — it is the stable handle; the label is for humans and may be reworded
- **Set the Insert / Update checkboxes deliberately** — the wrong combination shows save-style actions on records that do not exist yet, or hides them after first save
- **No hardcoded redirect URLs** — use `action.setRedirectURL(current)` / `action.setReturnURL()`; hardcoded paths break across UIs and instances

### Classic forms — client + server in one action

When an action needs client-side validation *and* server-side work, use one UI Action with *Client* checked. On classic forms, `g_form` is a page **global** and the server portion is triggered with `gsftSubmit`:

```javascript
// Onclick: validateAndSubmit()  — g_form is a global here
function validateAndSubmit() {
    if (!g_form.getValue('assignment_group')) {
        g_form.addErrorMessage(getMessage('prefix.task.group_required'));
        return false;
    }
    gsftSubmit(null, g_form.getFormElement(), 'sn_request_approval'); // Action name, not the label
}

// Server block in the same UI Action — runs only on the submit above
if (typeof window == 'undefined')
    new x_scope.SNTaskService().requestApproval(current);
```

### The same action in a Workspace

A UI Action can run on classic forms, in Configurable / Agent Workspace, or both — but the two surfaces execute the **client** portion on completely different frameworks. A UI Action built for a classic form does **not** automatically work in a workspace, and its client script almost always has to be rewritten.

**Enabling it:** the action must be marked **Client**, and surfaced via **Workspace Form Button** / **Workspace Form Menu** (plus **Format for Configurable Workspace**). The client logic goes in the **Workspace Client Script** field — a different field from the classic Script field. (A Declarative / UX Form Action is the alternative when you want the button defined in UI Builder rather than on the UI Action record — see [UI Builder](#ui-builder-next-experience).)

**What differs, concretely:**

| | Classic form | Workspace |
|---|---|---|
| `g_form` | page global | **passed in**: `function onClick(g_form) { … }` |
| Trigger the server portion | `gsftSubmit(null, g_form.getFormElement(), 'action_name')` | `g_form.submit('action_name')` — **returns a Promise** |
| Modal / prompt | `GlideModal` / form dialogs | `g_modal.confirm` / `g_modal.showFields` / `g_modal.showFrame` (Promise- or callback-based) |
| In-app navigation | `action.setRedirectURL()` (server) | `g_aw.openRecord(table, sysId, params)` (client) |
| DOM | reachable (but banned — see [Client Scripts](#client-scripts)) | not available at all |

```javascript
// Workspace Client Script field (referenced from the Onclick field)
function onClick(g_form) {              // g_form is an argument, not a global
    g_modal.showFields({               // Promise-based prompt — replaces GlideModal
        title: getMessage('Provide a reason'),
        fields: [{ type: 'textarea', name: 'work_notes', label: getMessage('Reason'), mandatory: true }],
        size: 'lg'
    }).then(function(fieldValues) {
        g_form.setValue('work_notes', fieldValues.updatedFields[0].value);

        var result = g_form.submit('sn_request_approval'); // runs the server block below
        if (!result) return;                                // falsy if the submit was blocked
        result.then(function() {                            // server work is done — now navigate
            g_aw.openRecord('change_request', -1, { sysparm_parent_sys_id: g_form.getUniqueValue() });
        });
    });
}

// Script field — server portion: SAME typeof guard and SAME Script Include as the classic action
if (typeof window == 'undefined')
    new x_scope.SNTaskService().requestApproval(current);
```

**Make the server portion surface-agnostic.** The `typeof window == 'undefined'` block calls the same Script Include no matter where the click came from — `new x_scope.SNTaskService().requestApproval(current)` behaves identically whether triggered by `gsftSubmit` or `g_form.submit`. Only the thin client wrapper changes per surface. **Never fork the real server logic** between a classic action and a workspace action; if both surfaces are in scope, that is one server implementation and two ~5-line client wrappers.

**Workspace client APIs worth knowing** (full surface lives in SN Docs — verify for your release):

- `g_form.submit('action_name')` — runs the named action's server portion; **returns a Promise**, so chain post-server work (navigation, refresh) in `.then()`. A falsy return means the submit was blocked
- `g_form.save()` — persists the record **without** invoking a named action
- `g_modal.showFields({ fields }).then(v => v.updatedFields[i].value)` — prompt for field values; `g_modal.confirm(...)` for yes/no; `g_modal.showFrame({ url })` to host a UI page in a modal (reusing classic UI pages this way is awkward — prefer native fields)
- `g_aw.openRecord(table, sysId, params)` and the other `g_aw` navigation helpers
- `getMessage('key')` for i18n — same as classic

<details>
<summary><strong>Why does a working classic client script go dead in a workspace?</strong></summary>

They run on different client frameworks. Classic forms expose `g_form` and `gsftSubmit` as page globals and submit the whole form; a workspace is a component-based single-page app where `g_form` is handed to your function as a parameter, `gsftSubmit` does not exist, and server work is invoked through the Promise-returning `g_form.submit()`. A classic client script doesn't throw a clean error in a workspace — it silently does nothing, because the globals it reaches for aren't there. Treat "works on the form, dead in the workspace" as the expected default until the Workspace Client Script is written.
</details>

> **Not to be confused with** the standalone **Workspace Client Scripts** artifact — onLoad / onChange / onSubmit logic for workspace forms, the workspace analogue of classic Client Scripts. It uses the same passed-in-`g_form` model and follows the [Client Scripts](#client-scripts) rules; its event API is in SN Docs. The above is specifically the client script *attached to a UI Action*.

**Naming:** the label is what users see — Title Case, verb-first (`Request Approval`). The internal `Action name` follows `prefix_description`.

---

## Access Control Lists (ACLs)

ACLs are the primary mechanism for securing data in ServiceNow. **This section deliberately does not restate how ACL evaluation works** — the official docs cover the mechanics and stay current as the platform changes. What follows is the judgment layer: design rules, hardening, and verification.

Three platform facts shape every design decision below. Verify the details in the official docs, but do not design against a different mental model:

1. **Table and field ACLs are both required** — a user must pass the matching table ACL *and* the matching field ACL to touch a field. Failing the table rule denies everything, regardless of field rules.
2. **Multiple matching rules at the same level are OR'd** — passing any one grants access. Adding another ACL on the same object/operation can only *widen* access, never narrow it; to tighten, change the existing rule.
3. **Modern instances are default-deny** — High Security Settings (active on current instances) ships wildcard table ACLs plus `glide.sm.default_mode = deny`, so the absence of a specific rule falls through to the wildcards, not to open access. Never *rely* on fall-through in either direction: every custom table gets explicit ACLs.

### Design Principles

- **Least privilege** — start restrictive and grant access explicitly; do not rely on the absence of deny rules
- **Row-level filtering** — use `before query` Business Rules to restrict which records a user can see; ACLs control table/field access, query BRs control record-level visibility. **Exempt `admin` in the query BR** (`if (gs.hasRole('admin')) return;`) — a query BR that hides rows from administrators turns every support session into a phantom data-loss investigation
- **Field-level ACLs** — use sparingly and only for genuinely sensitive fields (e.g. SSN, salary); they add evaluation overhead on every form load and list render
- **Avoid overly broad roles in ACLs** — granting `itil` access to a custom table means every ITSM agent can read/write it; create custom roles scoped to the application
- **Script conditions in ACLs** — use only when role-based and condition-based rules are insufficient; script conditions are harder to audit and slower to evaluate
- **Test as the target persona** — impersonate a user with the intended role and verify both the happy path (access works) and the negative path (restricted data is hidden). Results as admin prove nothing — admin bypasses ACLs

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

### Verifying and Debugging ACLs

- **Debug Security Rules** (System Security → Debugging → Debug Security Rules; equivalently System Diagnostics → Session Debug → Debug Security, or append `&sysparm_debug=security` to the URL) — shows which ACLs were evaluated for the session and which passed or failed
- **Access Analyzer** (newer releases) — evaluates a chosen user's access to tables, records, fields, UI pages, client-callable Script Includes, and REST endpoints, with the evaluation trace. The fastest answer to "why can('t) this user see this?"
- **Impersonation is part of every ACL test** — combine it with the debuggers above
- **Check for same-level rule stacking** — rules at the same specificity are OR'd; a "tightening" ACL added beside a loose one changes nothing

> ⚠️ Elevating to `security_admin` is required to create, modify, or delete ACL rules. Always test ACL changes on a sub-production instance first.

---

## Logging

Logging discipline matters more than the specific API. Pick the right tier for the environment, attach a useful source to every message, write at the right level, and make every message traceable to the artifact that produced it.

### Which API to use

| Tier | When | Pattern |
|---|---|---|
| 1 — Project logger | An engagement-deployed logger (e.g. `GSLog`) is available on the target instance | `this.log = new global.GSLog('com.prefix.module', this.type); this.log.info(…)` |
| 2 — Platform default | No project logger is deployed — most personal dev instances, fresh customer instances, ServiceNow internal | `gs.info(msg)` / `gs.warn(msg)` / `gs.error(msg)` for permanent logging; `gs.debug(msg)` for trace-level diagnostics that stay in code. The artifact identity travels **in the message** — see below |
| 3 — Temporary debug | Active debugging that gets removed before release | `gs.log(msg, 'recognisable-source')` — search-and-destroy before go-live |

Check the project's knowledge / setup notes for whether a project logger is deployed. If unclear, default to Tier 2 — the scoped `GlideSystem` logging methods are documented platform APIs with proper level support, not a sad fallback.

**VA topic scripts:** `GSLog` is not available inside Virtual Agent topic script nodes. Use the Tier 2 platform methods (`gs.info()` / `gs.warn()` / `gs.error()`) directly.

### Building a Tier 1 Logger (when none exists)

Most instances will **not** have a project logger deployed — that is fine; Tier 2 is the default, not a downgrade. Build a Tier 1 logger only when the project genuinely benefits (long engagement, many artifacts, need for runtime-adjustable verbosity), and **confirm with the user before building it** (see [Agent Ground Rules](#agent-ground-rules)).

If building one, the shape is:

- **One Script Include per scope**, named `[PREFIX]Logger` — a thin wrapper over the platform logging APIs, never a replacement for them
- **Constructor takes the source**: `new x_scope.SNLogger('SNIncidentService')` — the logger injects the source and `[Prefix]` message prefix on every call so call sites stay one line
- **Level methods** `debug()` / `info()` / `warn()` / `error()` delegating to the corresponding `gs.*` methods
- **Level threshold from a system property** (e.g. `x_scope.log.level`, default `info`): the logger checks the property and suppresses calls below the threshold — verbosity becomes a runtime setting instead of a code edit. Property reads are cache-backed, so the check is cheap
- **Optional, rarely needed:** writing to a custom log table — only when syslog genuinely cannot serve (e.g. operator-facing run history). Default is syslog via `gs.*`
- Keep it under ~60 lines. If the logger grows features (formatting engines, transports), it has become a project of its own — stop

### Identify the producing artifact — required, always

Every permanent log line must be traceable to the artifact that produced it. The mechanism differs by tier:

- **Tier 1 (project logger / GSLog):** the source is set once at construction — `new x_scope.SNLogger('SNIncidentService')` — and attached to every call.
- **Tier 2 (`gs.info` / `gs.warn` / `gs.error` / `gs.debug`):** these methods have **no source parameter.** Their additional arguments are `{0}`–`{4}` MessageFormat substitution values, not a source — `gs.info('msg', 'SNIncidentService')` silently discards the second argument unless the message contains `{0}`. The artifact identity therefore lives **in the message body** via the `[Prefix]` convention below. (In scoped apps the platform also attaches scope and script context to the entry automatically.)
- **Tier 3 (`gs.log`):** the legacy API *does* take a source as its second parameter — `gs.log(msg, 'recognisable-source')` — which is exactly what makes temp-debug lines easy to search and destroy.

**The artifact identifier** is the artifact's name as it exists in ServiceNow:

| Artifact | Identifier |
|---|---|
| Script Include | The class name — e.g. `'SNIncidentService'` |
| Business Rule | The BR's full name — e.g. `'SN - Before - Set Priority on Create'` |
| Scheduled Job | The job name |
| Scripted REST API | The resource path or operation name |
| Mail Script | `'mail_script:<name>'` |
| UI Action | The UI Action name |
| Background Script | A descriptive identifier including a date stamp |

### Inline prefix in the message body

Because Tier 2 has no source parameter, prefix every log message body with the artifact name in square brackets — e.g. `[Update Interaction]`, `[SN - Set Priority on Create]`. This keeps messages self-describing when read inline (without the source column) and supports a single `messageLIKE[Prefix Name]` filter in syslog.

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
gs.info('[SNInteractionService] Updating interaction {0}', grInteraction.getValue('number'));
gs.error('[SN - VA Topic Switch] Failed to switch topic: {0}', e);

// ❌ BAD — gs.info() has no source argument; 'SNInteractionService' is a discarded {0} substitution value here
gs.info('Updating interaction: ' + grInteraction.getValue('number'), 'SNInteractionService');

// ❌ BAD — wildcard characters in prefix (* is the syslog search wildcard)
gs.info('*** Update Interaction *** Updating interaction: ' + grInteraction.getValue('number'));

// ❌ BAD — no context
gs.info('Record updated');
```

### Error surfacing

Wrap risky operations (REST calls, GlideRecord operations that may fail ACLs, parse/math operations on untrusted input) in `try/catch` and log the caught error at error level with the exception message and stack where available. Never let exceptions fail silently.

### Before go-live

- Remove all Tier 3 `gs.log()` temp-debug calls
- Remove all `console.log()` calls (these end up in browser console anyway, never in syslog)
- Confirm Tier 1/2 calls are at the right level — not everything at `info`
- Confirm every permanent log call carries the inline `[Prefix]` (and that Tier 1 loggers were constructed with the correct source)

---

## Error Handling

Logging tells you what happened; error *handling* decides what happens next. The conventions:

### Where to try/catch

- Wrap operations that can fail **for reasons outside your code's control**: REST/SOAP calls, JSON parsing of external input, CRUD that ACLs might block, type coercion of untrusted values
- Do **not** blanket-wrap entire methods — a try/catch around everything hides which operation actually failed and encourages catch-and-ignore
- **Prevent over catch when the failure is predictable.** If you can test the condition cheaply — an API that may be absent (`typeof gel !== 'undefined'`), a value that may be null (`gs.nil(x)`), a record that may not exist (`if (grRef.get(id))`) — guard with that check rather than relying on try/catch to mop it up afterward. A guard states the condition you expect; a catch hides it. Reserve try/catch for failures you genuinely cannot prevent (external calls, parsing untrusted input).
- **An empty catch block is a defect.** Catch in order to *act*: log with context, then recover, return a failure contract, or rethrow. Never swallow silently.

### Return contracts

Pick a failure convention per project and apply it uniformly so callers never guess:

- **Simple lookups** return the value or `null` — caller checks truthiness
- **Operations** return a consistent result object: `{ success: boolean, message: string, data: object|null }`
- Document the contract in the method's JSDoc `@return` — the next developer (or agent) reads the signature, not the body

### User-facing vs. log-facing

- Users get a friendly, translated message (`gs.addErrorMessage(gs.getMessage('key'))`); logs get the technical detail (exception message, record sys_id, stack where available)
- **Never** expose stack traces, sys_ids, or raw exception text to end users; **never** log-only a failure the user needed to know about

### Throwing and aborting

- Low-level helpers may `throw` when the caller is expected to catch — but every **entry point** (BR, scheduled job, Scripted REST resource, AJAX method) catches everything; an uncaught exception there fails the transaction with a generic error nobody can act on
- To stop a save deliberately in a before BR, use `gs.addErrorMessage()` + `current.setAbortAction(true)` — an *intentional, explained* abort, not an exception escape
- Scripted REST resources map failures to correct HTTP status codes — see [Integrations — Scripted REST API](#integrations--scripted-rest-api)

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

<details><summary><b>Why message keys instead of inline text?</b></summary>

- **Translation without code changes** — `sys_ui_message` rows carry per-language values; hardcoded strings mean every wording or language change is a code deployment.
- **Stable keys survive copy edits** — keying by `prefix.subcategory.description` (rather than using the English sentence as the key) means rewording the message doesn't orphan every translation of it.
- **Logs and payloads are exempt on purpose** — log messages are for engineers and must stay greppable in one language; integration payloads are contracts with other systems, not UI copy.

</details>


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

<details><summary><b>Why these notification rules?</b></summary>

- **Three layers = three change cadences** — branding (layout) changes rarely, body copy (template) changes sometimes, trigger/recipients (notification) change per use case. Collapsing them means every copy tweak risks the trigger logic and every rebrand touches dozens of records.
- **Never rename a used template** — templates are referenced by name from notifications and `${template}` calls; renaming silently breaks every consumer with no error until an email goes out wrong (or not at all).
- **No hardcoded instance URLs** — emails authored with full URLs point at *dev* forever after a clone; the instance suffix resolves correctly in every environment.
- **Recipients via groups/record fields** — named individuals leave, change roles, go on leave; groups and record user fields keep the notification correct without maintenance.
- **Send to event creator = FALSE** — the person whose action triggered the email almost never needs to be told what they just did; defaulting to true generates noise that trains users to ignore notifications.

</details>


---

## Scheduled Jobs

- Clear the `run_as` field unless a specific user context is genuinely required (defaults to the creating user, which is often wrong)
- Verify the job record is actually captured in your update set — `sysauto` records are not always tracked automatically. If missing, force-capture it (**Add to Application File** in a scoped app — via *Actions on selected rows*; a force-to-update-set script/UI action in global scope). The `sys_update_xml` list can only *move* captures that already exist between sets — it cannot create a missing one
- Max ~5 lines of code in the job itself — delegate all logic to a Script Include
- For user-facing scheduled tasks, prefer a **Flow Designer scheduled flow**; use Scheduled Jobs for core application/platform automation

<details><summary><b>Why these job rules?</b></summary>

- **Clear `run_as`** — a job silently defaults to running as whoever created it. When that account is deactivated (people leave), the job starts failing — or worse, keeps running with a departed user's permissions. Empty means system context: predictable and durable.
- **≤5 lines, delegate to an SI** — the job record is *scheduling configuration*, not code. Logic in an SI is testable from a background script, reusable by a manual "run now" UI Action, and editable without touching (and re-capturing) the schedule record.
- **Verify capture** — `sysauto_script` records are data-ish artifacts the update-set tracker doesn't always capture automatically; checking (and force-capturing if needed) guarantees the job actually arrives in the next environment.

</details>


---

## Multi-row Variable Sets (MRVS)

- Access MRVS data via `grRitm.variables[multiRowInternalName]` — returns a multi-row object
- Iterate using `.getRowCount()` and `.getRow(i)`
- Extract individual field values using `String(row[fieldName])`

<details><summary><b>Why the String() coercion?</b></summary>

- **Row values are objects, not strings** — `row[fieldName]` returns an element wrapper; pass it into JSON, comparisons, or string concatenation and you get object identity surprises (`[object Object]`, failed equality). `String()` at the point of extraction makes every downstream use behave.

</details>

- MRVS data is available on `sc_req_item` records after submission

---

## Attachments

- Server-side attachment operations go through **`GlideSysAttachment`** — never raw-write `sys_attachment` records
- **Do not copy attachments — move or reference.** Copying duplicates the stored file: storage doubles and the "same" document forks into two diverging copies. Move the attachment to the target record (`GlideSysAttachment` write to the new `table_name`/`table_sys_id`) when ownership transfers, or keep a reference to the record that owns it when it doesn't
- Attachment visibility follows the **ACLs of the record it is attached to** — attaching a sensitive file to a widely-readable record exposes it
- Respect the instance attachment size/type properties rather than overriding them per-table without cause
- Never store file content as base64 in string fields — that is what attachments are for

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
- For Service Catalog, **always use GlideAJAX** for server-side data retrieval — there is no record behind the item form before submission, so Display BRs / `g_scratchpad` cannot supply data

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
- Do not use update sets for **custom scoped applications** — scoped apps move through the application repository and/or source control (a Studio-linked repo, or ServiceNow SDK / Fluent builds deployed via the `now-sdk` CLI). Update sets inside a scoped app create a second source of truth and impact upgradability; update sets remain the vehicle for global-scope configuration only
- For complex deployments, use a **Runbook template**

<details><summary><b>Why never back out, and why batch?</b></summary>

- **Backing out only reverts what the set captured** — related records modified outside the set, data created by the deployed code, and downstream changes all survive the back-out, leaving the instance in a state nobody designed. Rolling *forward* with a hotfix set keeps every change deliberate and auditable.
- **Batching preserves identity; merging destroys it** — a merged set is one irreversible blob: you can no longer pull one story out, see which set a change came from, or re-run collision detection per set. Batches keep each set intact while still committing in one operation, in order.
- **No update sets inside scoped apps** — scoped apps version through the application repository (install/upgrade semantics, version numbers, dependency checks). Mixing update sets into that lifecycle creates two competing sources of truth and breaks clean upgrades.

</details>


### Keep One Update Set to One Scope

A single update set must contain updates from **only one application scope**. The platform mostly prevents cross-scope capture, but it leaks: some tables live in one scope while the records in them are owned by another, so an update can silently land in a different scope than the set it is meant to belong to. The set then cannot be committed until every update in it shares the set's scope.

When a change touches more than one scope (or global plus a scope), keep a **separate update set per scope** and switch the active set as you switch scope. Before completing any set, open its `sys_update_xml` rows, add the **Application** column, and confirm every update's scope matches the set. (This is a global / cross-scope concern; scoped apps move through the application repository per the rules above, which sidesteps it.)

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
Select the rows, open the **Actions on selected rows** menu, and choose **Add to Application File** (this opens the *Create Application File from Record* dialog). No scripting required. Useful for data records that application logic depends on (e.g. custom Group Type records).

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

### Fix Scripts

A Fix Script is the **deployable** form of one-time scripted work — data migrations, backfills, post-deploy corrections. Background scripts are for ad-hoc investigation only and are never a deployment artifact: if it must run in another environment, it is a Fix Script.

- Wrap in the standard IIFE; delegate anything non-trivial to a Script Include
- **Idempotent by design** — guard so a re-run is safe (query for the un-migrated state rather than assuming a clean slate); deployments get retried
- Log a run summary (records examined / changed / skipped) with the standard `[Prefix]`
- Note in the update set description (or the promotion list) whether the fix script runs before or after commit

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

<details><summary><b>Why?</b></summary>

- **`gs.sleep()` holds a worker thread hostage** — the platform has a finite pool of background workers; a sleeping flow occupies one doing nothing, and a few concurrent sleepers can starve every other scheduled job on the node. *Wait for condition* parks the flow and frees the thread until the condition wakes it.

</details>

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
- **Custom CMDB tables** are named starting with `u_cmdb_ci` for easy identification — this is the global-scope convention; CMDB class extension is one of the legitimate global-scope exception cases under [Application Scope](#application-scope), and classes created inside a scoped app take the scope's `x_` prefix instead
- Use a **tree picker** for Location reference fields — prevents duplicate or misspelled location values
- **Never alter baseline relationship types** (`cmdb_rel_type`) — changes break Discovery and can cause errors
- Use **OOTB CI classes** wherever possible; do not extend directly off `cmdb_ci`

<details><summary><b>Why these CMDB rules?</b></summary>

- **Attributes high in the hierarchy** — the same attribute defined separately on three child classes is three columns the platform can't treat as one: reporting, identification rules, and IRE reconciliation all see them as unrelated fields. Defined once on the right parent, every descendant inherits a single consistent column.
- **Don't extend `cmdb_ci` directly** — identification rules, reconciliation, dependent relationships, and Discovery patterns are wired to the *specific* OOTB classes. A class hung straight off `cmdb_ci` inherits none of that and becomes invisible to the machinery that keeps a CMDB healthy. Extend the closest matching OOTB class instead.
- **Baseline `cmdb_rel_type` is load-bearing** — Discovery, service mapping, and OOTB dashboards create and traverse relationships by those exact types; altering one corrupts every existing edge of that type.

</details>

- Do not **recreate OOTB attributes** as custom fields — leverage what exists
- Restrict the Relationship Editor to **suggested relationships** — first ensure every valid relationship type between classes is listed in the Suggested Relationship [`cmdb_rel_type_suggest`] table (maintained via CI Class Manager or Configuration → Suggested Relationships), then enable the restriction so users cannot create invalid relationships *(the enabling property name varies by release — verify on the target instance before scripting it)*
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
- The server script runs once for the **initial render** (load the widget's starting data there) and again on every `c.server.get()` / `c.server.update()` round trip — branch on `input`: `if (input) { /* handle the interaction */ } else { /* initial load */ }`, and keep the branches disjoint
- Set data on the `data` object to transfer it to the client script
- All business logic must be delegated to Script Includes — the server script is for data retrieval, dispatch, and transfer only

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
- Private methods start with `_` (e.g. `_recalculateAvailableData`) — **must not** be called from outside the provider; the underscore is the documented signal (JavaScript does not enforce it — same rule as [Function Design](#code-readability))

---

## Service Portal — Server Communication

**Three patterns, in order of preference:**

1. **Widget initial load** (`*.server.js`) — data for the first render is loaded server-side once and transferred via the `data` object. The server script's no-`input` branch *is* the initial load.
2. **Widget round trip** — after load, client interactions go through the widget's own channel: `c.server.get({action: '...', ...})` for a targeted call, or `c.server.update()` to re-run the server script with the current `c.data` as `input`. This is the standard mechanism for post-load server work inside a widget. The server script branches on `input` and delegates to Script Includes; treat everything in `input` as untrusted client input (validate it; `GlideRecordSecure` per the standard rule).
3. **REST** (Table API / Scripted REST) — for Angular services/providers shared across widgets, for data needs that outlive a single widget, or for consumers outside the portal. Not the default *inside* a widget: the round trip above is simpler and carries the widget's server context.

**Round-trip rules:**
- Send an explicit `action` discriminator in `c.server.get()` payloads so the `input` branch is a readable dispatch, not a guess from payload shape
- Never re-run the initial-load work inside the `input` branch
- **One round trip per user interaction** (same spirit as the 1-AJAX-call rule) — consolidate what the interaction needs into a single `get`/`update`
- If the project has an established REST utility service for pattern 3, reuse or extend it — do not write a parallel implementation per widget

---

## Service Portal — Client-Side State

Where client-side state lives is a decision ladder — reach for the smallest scope that survives long enough:

| State must survive | Mechanism |
|---|---|
| One widget, one page view | Controller state (`c.data`, scope variables) |
| Multiple widgets, same page | Angular service as a data repository (see [AngularJS Providers](#service-portal--angularjs-providers)), or `$rootScope` events for notifications |
| Page navigations within the tab | `sessionStorage` — every portal navigation re-bootstraps Angular, so in-memory state dies; this is the legitimate web-storage case |
| Sessions / browser restarts | **User Preferences** (server-side, follows the user across devices and is server-visible) — `localStorage` only for low-value, device-local convenience |
| The server's session (server-set, client-read) | `gs.getSession().putClientData()` — exposed to the widget via its server script; session-scoped, so clear flags when done |

**Web storage rules (`sessionStorage` / `localStorage`):**

- **Never store sensitive data** — web storage is plaintext, readable by any script on the origin, and (for `localStorage`) outlives the session. No PII, no tokens, nothing authorization-shaped. Access decisions are enforced server-side by ACLs, always; client state is UX convenience, never a security boundary
- **Namespace every key** — the whole instance shares one origin, so every portal and widget shares the same storage. Prefix keys: `x_scope.widget-id.key`
- **Key user-specific state by user** — storage survives impersonation switches and shared machines; include the user sys_id (passed from the server script) in the key, or stale state leaks across identities
- **Strings only, so serialise deliberately** — `JSON.stringify` on write; `JSON.parse` inside `try/catch` on read (corrupted or legacy values), and treat a shape mismatch as absence
- **Treat it as a cache, not a source of truth** — users clear storage, private-browsing modes restrict it, and `setItem` can throw (quota, Safari private mode): wrap writes in `try/catch` and always be able to rebuild from the server
- **`localStorage` never expires** — store a written-at timestamp and treat stale entries as absent; remove keys a widget no longer uses
- Do **not** use web storage for same-page widget-to-widget messaging — that is what services and `$rootScope` events are for

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
- CSS Grid is fully supported by all current platform-supported browsers (the old-IE-era restriction no longer applies); Flexbox remains the house default for consistency with existing widget code, and Grid is acceptable for genuinely two-dimensional layouts — pick one approach per widget and stay with it
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

### Coverage Expectations

A minimum bar for what must have a test before go-live — without a stated bar, the answer is always "skip":

- **Client-callable Script Includes** (AJAX) — they are an attack surface; test both the happy path and an unauthorised/invalid-input path
- **Script Includes with business logic** — at least the primary path and one failure path per public method
- **Scripted REST resources** — one test per verb covering a success and a failure status code
- **Critical flows** — happy path plus the most likely failure branch
- **Declarative-only changes** (UI Policies, layouts, simple field changes) may ship without ATF coverage

Keep the suite runnable after every clone (see base-test guidance below) — a suite that fails post-clone stops being run at all.

ServiceNow's Automated Test Framework enables automated regression testing of back-end, form-based, and — since Orlando, via **Custom UI test steps** — Service Portal functionality (buttons, links, page text, UI controls, catalog items in the portal).

### What to Test

**Must test:**
- **Script Includes** — validate all functions; cover the happy flow and every defined error flow. Script Includes contain the bulk of back-end logic and are the highest-value target for automated tests.
- **Scripted REST APIs** — test input/output for GET calls; for POST/PUT/PATCH/DELETE also verify the outcome of the operation. Test happy flow and defined error flows. The underlying implementation logic should already be covered by Script Include tests, so REST tests focus on the API layer (routing, status codes, payload structure).

**Test when critical:**
- **Forms** — only if a form is vital to the application's functionality. ATF can test forms, but they offer less value in most cases.
- **Business Rules / Scheduled Jobs** — these should contain no logic and instead delegate to a Script Include. Since the Script Include is already tested, a separate test for the trigger component is redundant and not recommended.

**Cannot test (directly):**
- **Custom widget internals** — portal pages and their components are testable via Custom UI steps, but a widget's controller logic is not directly assertable; cover it through the Script Includes the widget delegates to
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

**Jasmine framework** (recommended for richer assertions — the trailing `jasmine.getEnv().execute();` outside the function body is what runs the spec):
```javascript
(function(outputs, steps, stepResult, assertEqual) {
    describe("getListsForUser Test", function() {
        var userID = steps("impersonate_step_sys_id").user;
        var service = new x_scope.ListService();
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
- Tests with UI steps require an open **Scheduled Client Test Runner** page matching the schedule's browser conditions — on an unlocked machine, with a dedicated ATF test user staying logged in — or use the platform's **headless browser** runner option, which removes the unlocked-machine requirement (see [Running ATF Programmatically](#automated-test-framework-atf)).
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

### Running ATF Programmatically

ATF test *creation* is a UI activity, but execution can be automated. The supported programmatic path is the **CI/CD REST API**:

```
POST /api/sn_cicd/testsuite/run?test_suite_sys_id=<suite_sys_id>
```

The call returns a progress resource to poll for the result. **Suites — not individual tests — are the unit of remote execution**, which is one more reason to maintain the suite hierarchy above. Suites containing UI steps still need a runner: a Scheduled Client Test Runner session, or the platform's **headless browser** option ("Headless Browser for Automated Test Framework" in the official docs). This is the pattern for post-deployment smoke tests and pipeline gates.

---

## Import Sets & Transform Maps

**All inbound data goes through an Import Set + Transform Map — never write external data directly to target tables.** This applies to *custom* integrations as much as file loads: a Scripted REST endpoint, MID-relayed feed, or Flow Designer integration should insert into an import set (staging) table and let the transform own the target-table writes. A working pattern: a Flow receives/fetches the payload and creates import set rows; the Transform Map does the rest.

<details><summary><b>Why staging-first?</b></summary>

- **Validation and cleansing have a home** — onBefore scripts inspect, fix, or reject each row before it touches real data; direct writes have no such gate.
- **Coalesce gives you dedup/upsert for free** — direct writes force you to hand-roll exists-checks for every integration.
- **Failures are visible and replayable** — a bad row sits in the staging table with an error state, inspectable and reprocessable; a failed direct write is just a log line and lost data.
- **Decoupling** — the payload shape can change without touching the target data model; only the map changes.

</details>

Import Sets are ServiceNow's general-purpose mechanism for loading external data into production tables. They are used by LDAP imports, file-based imports (CSV, Excel, XML), JDBC connections, and Integration Hub Data Streams. This section covers general best practices; see [LDAP User Import](#integrations--ldap-user-import) for LDAP-specific guidance.

### Architecture

External data → **Data Source** → **Staging Table** (import set table) → **Transform Map** → **Target Table**

Data is always loaded into a staging table first, never directly into the target table. The transform map controls how staging rows map to target records, including field mappings, coalesce logic, and scripted transformations.

### Staging Table Design

- A staging table **is** an import set table: it always extends `sys_import_set_row`. Load Data and IntegrationHub create them that way; a manually created staging table must extend it too. A standalone table used as "staging" gets none of the import set machinery — row state tracking, transform history, or scheduled cleanup
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

- Because every staging table extends `sys_import_set_row`, the OOTB **Import Set Deleter** scheduled job (System Import Sets → Scheduled Cleanup) cleans them all — custom ones included — deleting import sets and their row data older than the retention period (**7 days** by default)
- **Verify the deleter is active and the retention fits the project.** If non-repudiation needs a longer trail, archive what must be kept elsewhere — do not solve it by disabling the deleter
- Only a staging table that does *not* extend `sys_import_set_row` (an anti-pattern — see Staging Table Design) needs its own cleanup job
- Monitor staging table sizes regardless — very large daily imports can outpace the cleanup window, and tables with hundreds of thousands of rows degrade list performance

### Scheduled Imports

- For recurring imports (e.g. daily user sync, nightly asset refresh), attach a **Scheduled Import** to the data source
- Set the schedule to run during off-peak hours to minimise platform impact
- Ensure the import account / data source credentials do not expire without notice — set up monitoring or alerting on import failures

---

## Integrations — General

**Ground rule for anything inbound:** external data lands in an **Import Set and is written to target tables by a Transform Map** — integrations never write directly to target tables. See [Import Sets & Transform Maps](#import-sets--transform-maps).

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
- Clean up log and queue tables on a schedule — tables with hundreds of thousands of records degrade performance and eventually become inaccessible in the UI. Import set tables (they extend `sys_import_set_row`) and OOTB logging tables are auto-cleaned; **custom log/queue tables are not**

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
- Use the pre-configured error objects available in the Scripted REST API framework; use the customisable `ServiceError` error object (`setStatus()` / `setMessage()` / `setDetail()`) when the built-in options do not fit

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
- Reference: the "ServiceNow IP address information" landing page on Now Support (search the KB for the current article)
