#!/usr/bin/env python3
"""Regenerate the Open WebUI import JSONs from the .py sources.

Open WebUI's Import button (Admin Settings -> Functions / Workspace ->
Tools) accepts its JSON export format only — an array of objects whose
`content` field carries the Python source — not raw .py files. This script
wraps each artifact in that format.

Run it from this directory after ANY edit to glidegrail_filter.py or
glidegrail_tool.py so the JSONs never drift from the sources:

    python make_import_json.py
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent

ARTIFACTS = [
    ("glidegrail_filter.py", "glidegrail_filter.json", "glidegrail_standards_enforcement"),
    ("glidegrail_tool.py", "glidegrail_tool.json", "glidegrail_standards_lookup"),
]


def frontmatter(source: str) -> dict:
    """Parse the leading docstring frontmatter (title: ..., version: ...)."""
    match = re.match(r'\s*"""(.*?)"""', source, re.DOTALL)
    meta = {}
    if match:
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
    return meta


def main() -> None:
    for py_name, json_name, artifact_id in ARTIFACTS:
        source = (HERE / py_name).read_text(encoding="utf-8")
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
        (HERE / json_name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {json_name} (id={artifact_id}, "
              f"version={manifest.get('version', '?')}, "
              f"content={len(source)} chars)")


if __name__ == "__main__":
    main()
