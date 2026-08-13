# servicenow-docs

Live access to ServiceNow's official product documentation, straight from the
[`ServiceNow/ServiceNowDocs`](https://github.com/ServiceNow/ServiceNowDocs) repo.

ServiceNow publishes its AI Platform docs as one Markdown file per topic, plus a
machine-readable `llms.txt` index. This plugin bundles the **Fetch** MCP server and a skill
that teaches the agent to read that index first, then pull only the topic files it actually
needs — so answers come from the current published docs rather than training-data recall,
and there is no local clone to keep in sync.

## Prerequisite: `uv`

The Fetch server runs via `uvx`. Install [`uv`](https://docs.astral.sh/uv/) if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Install

```bash
/plugin marketplace add bikemeardsley/GlideGrail.md
/plugin install servicenow-docs@glidegrail
```

Restart Claude Code afterwards so the bundled MCP server starts. Verify with `/mcp` — you
should see a `fetch` server listed.

## Why `mcp<2` is pinned

`.mcp.json` launches the server as `uvx --with "mcp<2" mcp-server-fetch`. Under MCP Python
SDK 2.0 the Fetch server crashes on launch with:

```
AttributeError: 'Server' object has no attribute 'list_tools'
```

The pin holds the SDK on the 1.x line so the server starts cleanly. Leave it in place until
`mcp-server-fetch` ships a 2.0-compatible release.

## Tradeoffs

This is **online, file-at-a-time** retrieval against the `main` branch:

- ✅ Always current — reflects the docs as ServiceNow publishes them, nothing to re-sync.
- ✅ Light on context — the agent fetches 1–3 topic files per question, not the whole corpus.
- ❌ Requires internet access.
- ❌ No whole-corpus search and no offline use. If you need either, clone the docs repo
  locally and point a filesystem or git MCP server at it instead.

## Relationship to GlideGrail

[`glidegrail`](../) is the judgment layer — how you want ServiceNow code written. This plugin
is the reference layer — what the platform actually does. They install independently and
work well together.
