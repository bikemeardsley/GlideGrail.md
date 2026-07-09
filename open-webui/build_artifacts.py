#!/usr/bin/env python3
"""Build the Open WebUI artifacts from the canonical GlideGrail.md.

Two jobs, both idempotent — run this after ANY edit to
skills/glidegrail/GlideGrail.md OR to the filter/tool .py sources:

  1. Embed the doc. A gzip+base64 snapshot of GlideGrail.md is written into
     each .py between the "BEGIN/END EMBEDDED DOCUMENT" markers. This is the
     offline FLOOR the filter/tool fall back to when no live source works,
     so hub/JSON/paste installs need zero configuration and no network.

  2. Wrap for import. Open WebUI's Import button (Admin -> Functions /
     Workspace -> Tools) accepts its JSON export format, not raw .py, so each
     .py is wrapped into a matching .json (the .py source rides in `content`).

Safety checks that fail the build rather than ship a broken artifact:
  - blob roundtrip (decode == LF-normalized source doc) before any write;
  - exactly ONE marker region per file (a duplicated pair would otherwise be
    rewritten silently);
  - the spliced source must still compile();
  - all writes use newline="\\n" so the on-disk .py is byte-identical to the
    JSON `content` field on every platform (no CRLF churn on Windows).

    python open-webui/build_artifacts.py
"""

import base64
import gzip
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
DOC = HERE.parent / "skills" / "glidegrail" / "GlideGrail.md"

# (py source, wrapped import json, Open WebUI artifact id) — single table;
# everything else derives from it.
ARTIFACTS = [
    ("glidegrail_filter.py", "glidegrail_filter.json", "glidegrail_standards_enforcement"),
    ("glidegrail_tool.py", "glidegrail_tool.json", "glidegrail_standards_lookup"),
]

_REGION_RE = re.compile(
    r"(# --- BEGIN EMBEDDED DOCUMENT ---\n).*?(\n# --- END EMBEDDED DOCUMENT ---)",
    re.DOTALL,
)

WRAP = 116  # base64 line width inside the triple-quoted literal


def _write(path: Path, text: str) -> None:
    """All build outputs are LF regardless of platform, so the .py bytes
    always match the JSON `content` field and git stays churn-free."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def embed_document() -> dict:
    """Splice the gzip+base64 doc into each .py; return {py_name: new_text}
    so wrap_json() consumes exactly what was written (no re-read, no
    ordering coupling). The doc is normalized to LF (read_text applies
    universal newlines) so the embedded copy matches what the runtime file
    branch produces when reading source_path in text mode."""
    raw = DOC.read_text(encoding="utf-8").encode("utf-8")
    # mtime=0 -> deterministic gzip header -> reproducible builds.
    blob = base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")

    # Roundtrip check BEFORE touching any file.
    restored = gzip.decompress(base64.b64decode(blob))
    if restored != raw:
        raise SystemExit("FATAL: gzip+base64 roundtrip did not match source doc")

    wrapped = "\n".join(blob[i : i + WRAP] for i in range(0, len(blob), WRAP))
    literal = '_EMBEDDED_DOCUMENT_GZ_B64 = """\n' + wrapped + '\n"""'

    texts: dict = {}
    for py_name, _json_name, _artifact_id in ARTIFACTS:
        p = HERE / py_name
        text = p.read_text(encoding="utf-8")
        regions = _REGION_RE.findall(text)
        if len(regions) != 1:
            raise SystemExit(
                f"FATAL: expected exactly 1 embedded-document region in "
                f"{py_name}, found {len(regions)}"
            )
        # Function replacement avoids any backreference interpretation.
        new_text = _REGION_RE.sub(lambda m: m.group(1) + literal + m.group(2), text)
        # A syntactically broken artifact must never be written or wrapped.
        compile(new_text, py_name, "exec")
        _write(p, new_text)
        texts[py_name] = new_text
        print(f"embedded {len(blob)} b64 chars into {py_name} "
              f"(raw {len(raw)} -> gz+b64 {len(blob)}, {round(len(blob)/len(raw)*100)}%)")
    return texts


def frontmatter(source: str) -> dict:
    """Parse the leading docstring frontmatter (title:, version:, ...)."""
    match = re.match(r'\s*"""(.*?)"""', source, re.DOTALL)
    meta = {}
    if match:
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
    return meta


def wrap_json(texts: dict) -> None:
    """Wrap each embedded .py (as just written) into Open WebUI import JSON."""
    for py_name, json_name, artifact_id in ARTIFACTS:
        source = texts[py_name]
        manifest = frontmatter(source)
        payload = [
            {
                "id": artifact_id,
                "name": manifest.get("title", artifact_id),
                "content": source,
                "meta": {
                    "description": manifest.get("description", ""),
                    "manifest": manifest,
                },
            }
        ]
        _write(
            HERE / json_name,
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        )
        print(f"wrote {json_name} (id={artifact_id}, "
              f"version={manifest.get('version', '?')}, content={len(source)} chars)")


if __name__ == "__main__":
    wrap_json(embed_document())
    print("done.")
