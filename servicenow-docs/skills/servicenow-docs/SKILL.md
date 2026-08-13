---
name: servicenow-docs
description: Use this skill whenever you need authoritative ServiceNow product documentation - platform capabilities, APIs, application development, security/ACLs, ITSM/ITOM/HRSD, Flow Designer, integrations, Service Portal, scripting, and more. It reads ServiceNow's official documentation (published as Markdown for LLMs) live from GitHub via the Fetch MCP server, so answers reflect the current published docs. Prefer this skill over training-data recall for anything ServiceNow-specific, version-sensitive, or where an authoritative citation is helpful.
---

# ServiceNow Docs (live, index-first)

This skill gives you authoritative, up-to-date ServiceNow documentation by fetching it
directly from the official `ServiceNow/ServiceNowDocs` repository on GitHub. The docs are
published as one Markdown file per topic and include a machine-readable index (`llms.txt`)
designed for exactly this "read index, then fetch the file you need" workflow.

You have access to the **Fetch** MCP server (bundled with this plugin). Use it to retrieve
URLs and read them as Markdown.

## If you have no fetch tool

If no fetch/web-retrieval tool is available to you, the plugin's bundled MCP server is not
running - almost always because `uv` (which provides `uvx`) is not installed. Say so plainly
and give the user the fix:

1. Install `uv` - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`;
   Windows PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Reopen the terminal so `uvx` is on `PATH`.
3. Restart Claude, then run `/mcp` - a `fetch` server should be listed and connected.

**Do not silently answer from memory as if you had consulted the docs.** If you answer
anyway, state up front that the live documentation was unavailable and the answer comes from
prior knowledge, which may be outdated or wrong on version-specific details.

## Base locations

- **Index (always read this first):**
  `https://raw.githubusercontent.com/ServiceNow/ServiceNowDocs/main/llms.txt`
- **Raw file base** (for any path you find in the index):
  `https://raw.githubusercontent.com/ServiceNow/ServiceNowDocs/main/`
- **Human-browsable repo** (for citing back to the user):
  `https://github.com/ServiceNow/ServiceNowDocs`

## Retrieval workflow (follow this order)

1. **Fetch the index first.** Retrieve `llms.txt` and scan it for the topic(s) that match
   the user's question. The index lists topics with short descriptions and their file paths.
2. **Resolve to specific file(s).** Pick the 1-3 most relevant entries. Build each file's
   raw URL by joining the raw file base with the path from the index.
3. **Fetch the file(s).** Retrieve the actual Markdown topic file(s) with the Fetch server.
4. **Answer from the fetched content**, and cite the topic (and its GitHub URL) so the user
   can open the source. If the docs and your prior knowledge disagree, trust the fetched docs.

## Good practices

- **Always index-first.** Do not guess file paths from memory; read `llms.txt` and use the
  paths it gives you. Paths and topic organization change as the docs are refreshed.
- **Fetch narrowly.** Grab only the files you actually need (usually 1-3), not large swaths
  of the corpus, to keep context focused.
- **Multi-part questions:** resolve each sub-topic against the index separately, then fetch
  each relevant file.
- **If a fetch fails or a path 404s,** re-read the index (the topic may have moved) and try
  the updated path before giving up.
- **Cite your source.** Point the user to the topic's GitHub URL so they can verify or read more.

## Notes

- This is **online, file-at-a-time** retrieval. It requires internet access and reads the
  `main` branch live, so it reflects the latest published docs (the corpus is refreshed
  periodically by ServiceNow). There is no local copy to keep in sync.
- If a user needs **offline** access or **whole-corpus search**, that requires a local clone
  of the repo with a filesystem/git MCP server instead - out of scope for this skill.
