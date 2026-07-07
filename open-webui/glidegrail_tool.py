"""
title: GlideGrail ServiceNow Coding Standards Lookup
author: Michael Beardsley
author_url: https://github.com/bikemeardsley
version: 1.0.0
license: CC-BY-4.0
description: LOOKUP (pull) — lets the MODEL fetch specific GlideGrail ServiceNow coding-standard sections on demand via function-calling (get_glidegrail_guidance / list_glidegrail_sections). Requires a model with solid function-calling; many local models never call tools, so do NOT rely on this alone for enforcement — install the "GlideGrail ServiceNow Coding Standards Enforcement" FILTER for guaranteed automatic injection, and add this tool as a companion for capable models.
required_open_webui_version: 0.6.0
"""

# ---------------------------------------------------------------------------
# GlideGrail Standards Lookup — an Open WebUI TOOL (model-invoked).
#
# This is the PULL side of the GlideGrail pair:
#   - glidegrail_filter.py (a Function/filter) PUSHES the relevant standards
#     into every request automatically — enforcement.
#   - this Tool lets a capable model PULL a specific rule on demand
#     ("what does GlideGrail say about ATF suites?") — lookup.
#
# Install both if you can. If your model has weak/no function-calling
# (many local models), the filter alone is what guarantees standards reach
# the model; this Tool will simply go uncalled.
#
# Document loading mirrors the filter: local file preferred (re-read on
# mtime change), GitHub raw URL fallback (TTL cache + 60s failure backoff).
# All loading failures degrade to a helpful message — never an exception.
# ---------------------------------------------------------------------------

import asyncio
import os
import re
import threading
import time
from collections import OrderedDict
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

FETCH_RETRY_BACKOFF_S = 60

_TOKEN_RE = re.compile(r"[a-z0-9_$.]{3,}")
_STOPWORDS = frozenset(
    """
    the and for with that this from are was were has have had not you your
    can could should would will shall may might must про how what when where
    which who whom why all any each our their its his her out use used using
    into onto over under between про does did doing done get got make made
    """.split()
)


def _normalize_title(title: str) -> str:
    """casefold, strip, collapse whitespace, em/en-dash -> '-' (identical to
    the filter's normalizer so section keys can never drift)."""
    t = title.replace("—", "-").replace("–", "-")
    t = " ".join(t.split())
    return t.casefold()


def _parse_sections(text: str) -> "OrderedDict[str, Tuple[str, str]]":
    """Split into ordered h2 sections; fence-aware; skips Table of Contents.
    Keys are normalized titles; values are (original_title, full_text)."""
    sections: "OrderedDict[str, Tuple[str, str]]" = OrderedDict()
    current_title: Optional[str] = None
    buffer: List[str] = []
    in_fence = False

    def flush() -> None:
        if current_title is None:
            return
        norm = _normalize_title(current_title)
        if norm == "table of contents":
            return
        body = "\n".join(buffer).strip()
        if body:
            sections[norm] = (current_title, body)

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            if current_title is not None:
                buffer.append(line)
            continue
        if not in_fence and line.startswith("## "):
            flush()
            current_title = line[3:].strip()
            buffer = [line]
        elif current_title is not None:
            buffer.append(line)
    flush()
    return sections


class Tools:
    class Valves(BaseModel):
        source_path: str = Field(
            default="/app/backend/data/glidegrail/GlideGrail.md",
            description="Local path to GlideGrail.md (preferred; re-read on change).",
        )
        source_url: str = Field(
            default=(
                "https://raw.githubusercontent.com/bikemeardsley/GlideGrail.md/"
                "main/skills/glidegrail/GlideGrail.md"
            ),
            description="Fallback URL when the local path is missing.",
        )
        cache_ttl_minutes: int = Field(
            default=1440, description="URL cache lifetime in minutes."
        )
        char_budget: int = Field(
            default=16000,
            description="Max characters returned per lookup (sections dropped/truncated to fit).",
        )
        top_k: int = Field(
            default=2, description="Max sections returned per lookup."
        )
        debug: bool = Field(
            default=False, description="Print [glidegrail-tool] diagnostics to the server log."
        )

    def __init__(self):
        self.valves = self.Valves()
        self._lock = threading.Lock()
        self._sections: "OrderedDict[str, Tuple[str, str]]" = OrderedDict()
        self._source_sig = ""
        self._file_state: Tuple[str, float] = ("", -1.0)
        self._url_fetched_at = 0.0
        self._last_failure_at = 0.0

    # -- diagnostics --------------------------------------------------------

    def _log(self, message: str) -> None:
        if bool(self.valves.debug):
            print(f"[glidegrail-tool] {message}")

    # -- document loading (mirrors the filter; blocking, call via to_thread) --

    def _fetch_url(self, url: str) -> str:
        import requests  # lazy import by design

        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "glidegrail-openwebui-tool/1.0.0"},
        )
        response.raise_for_status()
        return response.text

    def _ensure_document(self) -> "OrderedDict[str, Tuple[str, str]]":
        # 1. Local file (mtime-keyed).
        path = (self.valves.source_path or "").strip()
        if path and os.path.isfile(path):
            try:
                mtime = os.path.getmtime(path)
                sig = f"file:{path}:{mtime}"
                with self._lock:
                    if sig == self._source_sig:
                        return self._sections
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                parsed = _parse_sections(text)
                with self._lock:
                    cached_path, cached_mtime = self._file_state
                    if self._source_sig != sig and not (
                        cached_path == path and mtime < cached_mtime
                    ):
                        self._sections = parsed
                        self._source_sig = sig
                        self._file_state = (path, mtime)
                        self._log(f"loaded {len(parsed)} sections from file {path}")
                    return self._sections
            except OSError as exc:
                self._log(f"file read failed ({path}): {exc}")

        # 2. URL with TTL cache + failure backoff.
        url = (self.valves.source_url or "").strip()
        if not url:
            with self._lock:
                return self._sections

        ttl_seconds = max(int(self.valves.cache_ttl_minutes), 1) * 60
        url_sig = f"url:{url}"
        now = time.time()
        with self._lock:
            if (
                self._source_sig == url_sig
                and (now - self._url_fetched_at) < ttl_seconds
            ):
                return self._sections
            if (
                self._last_failure_at
                and (now - self._last_failure_at) < FETCH_RETRY_BACKOFF_S
            ):
                return self._sections

        try:
            text = self._fetch_url(url)
            parsed = _parse_sections(text)
        except Exception as exc:
            self._log(f"url fetch failed ({url}): {exc}")
            with self._lock:
                self._last_failure_at = time.time()
                return self._sections

        with self._lock:
            fetched_at = time.time()
            if not (
                self._source_sig == url_sig
                and (fetched_at - self._url_fetched_at) < ttl_seconds
            ):
                self._sections = parsed
                self._source_sig = url_sig
                self._url_fetched_at = fetched_at
                self._file_state = ("", -1.0)
                self._log(f"loaded {len(parsed)} sections from url {url}")
            self._last_failure_at = 0.0
            return self._sections

    # -- the tools ----------------------------------------------------------

    async def list_glidegrail_sections(self) -> str:
        """
        List every section of the GlideGrail ServiceNow coding standards.
        Call this first when you are unsure which section covers a topic;
        then call get_glidegrail_guidance with the section or topic you need.
        """
        sections = await asyncio.to_thread(self._ensure_document)
        if not sections:
            return (
                "GlideGrail standards are currently unavailable (document "
                "could not be loaded from the configured path or URL)."
            )
        titles = [title for title, _ in sections.values()]
        return (
            "GlideGrail sections (%d):\n" % len(titles)
            + "\n".join(f"- {t}" for t in titles)
        )

    async def get_glidegrail_guidance(self, topic: str) -> str:
        """
        Get the GlideGrail ServiceNow coding-standard sections most relevant
        to a topic. Use whenever you write, review, or refactor ServiceNow
        code and need the project's mandatory conventions — e.g. GlideRecord
        queries, Business Rules, ACLs, Script Includes, Flow Designer,
        Service Portal widgets, Scripted REST APIs, logging, or ATF tests.
        Follow the returned standards over your own defaults.

        :param topic: The ServiceNow topic, artifact type, or section title
            to look up (e.g. "business rules", "acl debugging", "atf").
        """
        topic = (topic or "").strip()
        if not topic:
            return "Provide a topic, e.g. get_glidegrail_guidance('business rules')."

        sections = await asyncio.to_thread(self._ensure_document)
        if not sections:
            return (
                "GlideGrail standards are currently unavailable (document "
                "could not be loaded from the configured path or URL)."
            )

        norm_topic = _normalize_title(topic)
        tokens = {
            t
            for t in _TOKEN_RE.findall(norm_topic)
            if t not in _STOPWORDS
        }
        token_patterns = [
            re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)") for t in tokens
        ]

        scored: List[Tuple[int, str]] = []
        for norm_title, (title, text) in sections.items():
            score = 0
            # Direct title relationship dominates everything else.
            if norm_topic == norm_title:
                score += 1000
            elif norm_topic in norm_title or norm_title in norm_topic:
                score += 300
            title_lower = title.casefold()
            body_lower = text.split("\n", 1)[1].casefold() if "\n" in text else ""
            for pattern in token_patterns:
                score += 5 * len(pattern.findall(title_lower))
                score += len(pattern.findall(body_lower))
            if score > 0:
                scored.append((score, norm_title))

        if not scored:
            titles = [title for title, _ in sections.values()]
            return (
                f"No GlideGrail section matched '{topic}'. Available sections:\n"
                + "\n".join(f"- {t}" for t in titles)
            )

        scored.sort(key=lambda item: item[0], reverse=True)
        top_k = max(int(self.valves.top_k), 1)
        budget = max(int(self.valves.char_budget), 500)

        picked: List[str] = []
        used = 0
        for _, norm_title in scored[:top_k]:
            text = sections[norm_title][1]
            if used + len(text) > budget:
                remaining = budget - used
                if not picked and remaining > 500:
                    text = (
                        text[:remaining]
                        + "\n\n[... truncated to fit the lookup budget ...]"
                    )
                else:
                    break
            picked.append(text)
            used += len(text)

        self._log(
            f"guidance('{topic}') -> "
            + ", ".join(sections[t][0] for _, t in scored[: len(picked)])
        )
        return (
            "The following GlideGrail coding standards are MANDATORY for this "
            "project — follow them over your own defaults.\n\n"
            + "\n\n".join(picked)
        )
