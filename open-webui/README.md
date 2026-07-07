# GlideGrail — Open WebUI Filter & Tool

Two [Open WebUI](https://openwebui.com) artifacts that bring the [GlideGrail](https://github.com/bikemeardsley/GlideGrail.md) ServiceNow coding standards to any model you run:

| Artifact | File | Mechanism | Install if… |
|---|---|---|---|
| **Filter** (recommended) | [`glidegrail_filter.py`](glidegrail_filter.py) | **Push — enforcement.** Runs on every request; detects ServiceNow topics (or a pipeline sentinel) and injects the matching standards sections before the model answers. Works with any model, needs no model cooperation. | Always, if you're an admin. This is the guarantee. |
| **Tool** (companion) | [`glidegrail_tool.py`](glidegrail_tool.py) | **Pull — lookup.** Exposes `get_glidegrail_guidance(topic)` / `list_glidegrail_sections()` as function-calls the *model* can invoke mid-conversation for a rule outside the injected sections. | Alongside the filter, if your models have solid function-calling (cloud models; some local models). |

Install both when you can: the filter guarantees the standards arrive; the tool lets capable models look up more on their own. Don't rely on the Tool alone for enforcement — a model that never calls it gets nothing (many local models have weak or no function-calling).

## Install

Three ways to get each artifact into your instance — pick whichever suits you:

1. **Community hub (recommended):** open the listing and click **Get** — it imports straight into your instance.
   - Filter: [GlideGrail ServiceNow Coding Standards Enforcement](https://openwebui.com/posts/glidegrail_servicenow_coding_standards_enforcement_00c849c7)
   - Tool: [GlideGrail ServiceNow Coding Standards Lookup](https://openwebui.com/posts/glidegrail_servicenow_coding_standards_lookup_871d3d99)
2. **Import the JSON:** download [`glidegrail_filter.json`](glidegrail_filter.json) / [`glidegrail_tool.json`](glidegrail_tool.json) from this repo, then click **Import** (next to **+** on the Functions / Tools page) and select it. (The Import button expects Open WebUI's JSON export format — the raw `.py` won't import. The JSONs here are those same `.py` sources pre-wrapped in that format; regenerate them with `make_import_json.py` if you fork and edit.)
3. **Paste:** click **+** (new function / new tool), paste the entire `.py` file contents, save.

Then finish setup:

**Filter** — Open WebUI → **Admin Settings → Functions**:

- **Enable** the function, and toggle **Global** so it applies to all models (or assign it per-model instead).
- The filter is always-on by design (no per-chat toggle): the three-tier keyword gating (see below) keeps it silent on non-ServiceNow conversations, so there is nothing to switch off.

**Tool (optional companion)** — Open WebUI → **Workspace → Tools**:

- Enable it on the models that should have it (model settings → Tools), or toggle it per-chat with the **+** control.
- The tool reads the same document via the same `source_path`/`source_url` valves as the filter — configure them identically. Its `char_budget` (default 16000) caps each lookup's size independently of the filter's budget.

## API / MCP usage

Filters run on Open WebUI's native **`/api/chat/completions`** endpoint when the function is enabled **Global** (or assigned to the model being called) — so API clients, scripts, and MCP bridges that talk to that endpoint get the same standards injection as the chat UI. Filters do **not** run on the `/ollama` or `/openai` passthrough proxy routes; those forward requests untouched.

## Where the standards come from (two source valves)

The filter needs the `GlideGrail.md` document. It tries, in order:

1. **`source_path`** (preferred) — a local file inside the Open WebUI container, default `/app/backend/data/glidegrail/GlideGrail.md`. Mount or copy the file there, e.g.:

   ```bash
   # docker cp one-off
   docker exec <container> mkdir -p /app/backend/data/glidegrail
   docker cp skills/glidegrail/GlideGrail.md <container>:/app/backend/data/glidegrail/GlideGrail.md
   ```

   or add a volume/bind mount in your compose file. The file is re-read automatically whenever its mtime changes — edit it live, no restart needed.

2. **`source_url`** — if the path does not exist, the filter fetches the GitHub raw URL (default points at this repo's `main` branch) and caches it in memory for `cache_ttl_minutes`. Zero setup, but requires outbound network access from the container. If a fetch fails, the filter backs off for **60 seconds** before retrying (serving any stale cache in the meantime), so an outage never adds a network timeout to every message.

If both fail, the filter silently does nothing — it never breaks a chat.

## Pipelines & bridge callers (sentinel)

Automation that calls Open WebUI programmatically (an MCP bridge, a script, a scheduled job) shouldn't depend on keyword heuristics — it needs **guaranteed** injection. For that, the filter supports a deterministic trigger: include the sentinel token (valve `sentinel_token`, default `<<<GLIDEGRAIL_ENFORCE>>>`) anywhere in any message. When the filter sees it, it:

1. **Strips the token from every message** — the model never sees it.
2. **Arms ServiceNow context unconditionally** (keyword gating is bypassed).
3. **Injects standards** per `sentinel_inject`:
   - `sections` (default) — the relevant sections chosen from the task text, within `char_budget`. Right for local models.
   - `full` — the entire document, ignoring `char_budget`. **Only for big-context cloud models**: the document is ~40–50k tokens, and Ollama-class models will silently truncate.

The same trick gives any custom model always-on enforcement: put the sentinel in the model's System Prompt.

```bash
curl http://localhost:8080/api/chat/completions \
  -H "Authorization: Bearer <api-key>" -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:14b",
    "messages": [
      {"role": "system", "content": "<<<GLIDEGRAIL_ENFORCE>>>\n\nYou are assisting with ServiceNow work."},
      {"role": "user", "content": "Refactor these business rules to use setWorkflow correctly"}
    ],
    "stream": false
  }'
```

Set `sentinel_token` to an empty string to disable the feature entirely.

## Three-tier keyword gating

The rule of thumb: **one API token, or two independent ServiceNow-flavored concepts, at least one strong.** Concretely:

- **Specific** keywords are ServiceNow-unique API tokens (`GlideRecord`, `gs.info`, `sys_user`, `g_form`, `service portal widget`) — one hit injects its section and establishes ServiceNow context.
- **Vocab** keywords are ServiceNow-flavored but ecosystem-ambiguous phrases ("business rule", "acl", "update set", "flow designer"). A single one in isolation does nothing. Arming counts *witnesses*: matches are collected as text spans, overlapping spans merge into one occurrence ("service catalog items" is one witness, not two), and near-synonyms belong to one *concept group* ("before insert" + "before update" is one witness; so is "acl" + "access control"). At the default threshold (2), context arms when two distinct concept groups are witnessed **and at least one is a strong term** — one a developer usually only says about ServiceNow ("business rule", "flow designer", "transform map", "mid server") rather than a weak one shared with other ecosystems ("acl", "cmdb", "before insert"). Once armed, every vocab hit fires its section.
- **Generic** keywords are ordinary developer vocabulary ("try catch", "oauth", "flexbox") — they only count once context exists via a ServiceNow signal (e.g. "ServiceNow", `sys_id`, an `sn_*` scope name, a `u_*` custom-table name, an `x_vendor_app` scope), a specific hit, or a vocab witness pair. Non-ServiceNow conversations get nothing injected.

**Platform veto:** unambiguous competitor/other-product tokens (Salesforce, Power Automate, Dynamics 365, Purview, Zendesk, iTop, SharePoint, ...) suppress vocab-pair arming — "should this be a business rule or a Power Automate flow designer flow?" stays silent. Real ServiceNow signals override the veto: "In ServiceNow, is a business rule or flow designer better? We're migrating from Power Automate" fires normally.

### Known residual risks

- Contrived low-realism pairings of strong terms can still arm — e.g. prose that happens to say "record producer" next to another strong term. `char_budget` bounds the cost of any false injection.
- The veto has a recall cost: a genuine ServiceNow prompt that names **only** a vetoed product ("we're migrating off BMC Remedy — how should I organize update sets?") can stay silent. Say "ServiceNow" once, or use the profile valves.
- At defaults, a bare two-weak-term question ("should this be a business rule or a client script?") needs a third witness or a signal — deliberate, since ITSM competitors share that exact vocabulary. `vocab_arm_threshold: 1` removes the requirement.
- "customer service portal" is treated as ordinary English (it's a common web-dev phrase); ServiceNow CSM users discussing theirs need one more witness or a signal.

## Deployment profiles

| Profile | Valve settings | Effect |
|---|---|---|
| General / shared instance | defaults | Strictest gating: only unambiguous API tokens or a pair of ServiceNow-flavored terms trigger injection. |
| ServiceNow-leaning | `vocab_arm_threshold: 1` | A single ServiceNow-flavored term ("acl", "business rule") fires alone. |
| Dedicated ServiceNow instance or model | `assume_servicenow_context: true` | ServiceNow context is always armed — vocab and generic keywords fire like specific ones. Recommended when the filter serves a ServiceNow-focused custom model or an MCP/API pipeline. |

## Tuning for small local models

`char_budget` (default **24000** chars ≈ 6k tokens) caps how much standards text is injected. For small local models with 4k–8k context windows, lower it to **6000–10000** and consider setting `search_top_k` to 1 and trimming `always_include` (e.g. only `Agent Ground Rules`). Sections are dropped lowest-priority-first (search results → keyword matches → always-include) and a lone oversized section is truncated rather than dropped.

## Valves

| Valve | Default | Description |
|---|---|---|
| `priority` | `0` | Filter execution order relative to other filters (lower runs earlier). |
| `source_path` | `/app/backend/data/glidegrail/GlideGrail.md` | Local path to GlideGrail.md inside the container; preferred when it exists, re-read on mtime change. |
| `source_url` | GitHub raw URL of `skills/glidegrail/GlideGrail.md` | Fallback source when the path is missing; response cached in memory. |
| `cache_ttl_minutes` | `1440` | How long the URL-fetched document is cached (minutes). |
| `char_budget` | `24000` | Max characters of injected standards; sections dropped/truncated to fit. |
| `scan_last_n_user_messages` | `3` | How many recent user messages are scanned for triggers. |
| `vocab_arm_threshold` | `2` | Distinct vocab concept-group witnesses (span-merged, synonym-grouped) needed to establish ServiceNow context; at 2+ one must be a strong term and no veto token present. Set to `1` for ServiceNow-leaning instances (any single witness arms). |
| `assume_servicenow_context` | `false` | Treat ServiceNow context as always established: vocab and generic keywords fire like specific ones, and the search fallback's ServiceNow-signal gate is satisfied. For dedicated ServiceNow deployments. |
| `search_fallback` | `true` | If no topical keyword hits (matches on `always_include` sections alone don't count) but the prompt mentions ServiceNow generally, run a token-overlap search over the document. |
| `search_top_k` | `2` | Max sections the search fallback may add. |
| `min_search_score` | `3` | Minimum overlap score for a section to qualify in the search fallback. |
| `always_include` | `Agent Ground Rules, Do Not Use` | Comma-separated section titles injected whenever anything else fires. |
| `sentinel_token` | `<<<GLIDEGRAIL_ENFORCE>>>` | Deterministic trigger for pipelines/bridges: found in any message → stripped everywhere, context armed, standards injected. Empty string disables. |
| `sentinel_inject` | `sections` | What a sentinel trigger injects: `sections` (relevant sections, budget-capped) or `full` (entire document, ignores `char_budget` — big-context models only). |
| `show_status` | `true` | Show a status line in the UI ("GlideGrail: injected N section(s): ..."). |
| `debug` | `false` | Print `[glidegrail]` diagnostics to the server log. |

## Behavior notes

- Injected text is wrapped between `<!-- GLIDEGRAIL-STANDARDS v1 -->` and `<!-- /GLIDEGRAIL-STANDARDS -->` markers; on every turn the previous block is replaced, never stacked.
- If a system message already exists the block is appended to it; otherwise a new system message is inserted at the top.
- On turns where nothing ServiceNow-related fires, the payload passes through untouched.

## No admin rights? Knowledge-base fallback

Installing Functions requires **admin** on the Open WebUI instance. If you're a regular user:

1. **Workspace → Knowledge → +**, upload `skills/glidegrail/GlideGrail.md`.
2. Reference it in any chat by typing `#` and selecting it, **or** create a custom model (**Workspace → Models → +**) with the knowledge attached and a system prompt like *"For any ServiceNow code, follow the attached GlideGrail standards over your defaults."*

That path uses RAG retrieval rather than deterministic keyword-triggered injection — it works well, it just isn't automatic or guaranteed per-turn the way the filter is. Both can coexist on the same instance.
