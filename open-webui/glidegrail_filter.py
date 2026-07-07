"""
title: GlideGrail ServiceNow Coding Standards Enforcement
author: Michael Beardsley
author_url: https://github.com/bikemeardsley
version: 1.0.0
license: CC-BY-4.0
description: ENFORCEMENT (push) — automatically detects ServiceNow development topics in the conversation and injects the relevant GlideGrail coding-standard sections into the system prompt before the model answers. Works with ANY model (no function-calling needed); silent on non-ServiceNow chats. Install this one for guaranteed standards; the separate "GlideGrail ServiceNow Coding Standards Lookup" TOOL is an optional companion that lets capable models pull additional sections on demand.
required_open_webui_version: 0.6.0
"""

# GlideGrail Open WebUI filter
# ----------------------------
# Source document: https://github.com/bikemeardsley/GlideGrail.md
#
# How it works (inlet):
#   1. Load GlideGrail.md from a local path (preferred) or the GitHub raw URL
#      (cached in memory with a TTL; failed URL fetches back off for
#      FETCH_RETRY_BACKOFF_S seconds). Parsed into "## " (h2) sections,
#      code-fence aware. Document acquisition runs off the event loop in a
#      worker thread and never holds the lock across network/file I/O.
#   2. Scan the last N user messages for keyword hits (KEYWORD_MAP below).
#      Keywords are THREE-TIER: "specific" keywords (ServiceNow-unique API
#      tokens such as Glide* classes, gs.* calls, sys_* tables) fire on
#      their own AND establish ServiceNow context; "vocab" keywords
#      (SN-flavored but ecosystem-ambiguous phrases like "business rule"
#      or "acl") arm context only via WITNESS COUNTING: matched vocab
#      occurrences are collected as text SPANS, overlapping spans are
#      merged into one occurrence, occurrences map to CONCEPT GROUPS
#      (VOCAB_GROUPS — near-synonyms count once), and context arms when
#      vocab_arm_threshold (default 2) distinct groups are witnessed AND
#      at least one group is STRONG (STRONG_VOCAB) AND no PLATFORM_VETO
#      competitor token (Salesforce, Power Automate, ...) is present.
#      Once armed, every vocab hit fires its section. "generic" keywords
#      (developer vocabulary like "try catch" or "oauth") only count once
#      ServiceNow context exists (a GENERIC_SN_SIGNALS match, a specific
#      hit, or a vocab witness pair) and never establish it themselves.
#      This keeps the filter silent on non-ServiceNow conversations.
#   3. If no topical keyword hit (matches on always_include sections alone do
#      not count) and the prompt clearly smells like ServiceNow
#      (GENERIC_SN_SIGNALS), fall back to a lightweight token-overlap search
#      over the document sections.
#   4. Inject the selected sections (plus always-include sections) into the
#      system message between marker comments, replacing any block injected
#      on a previous turn (never stacking).
#
# SENTINEL CONTRACT (v0.5.0): pipeline/bridge callers that need GUARANTEED
# (non-heuristic) injection put the exact sentinel_token valve string
# (default "<<<GLIDEGRAIL_ENFORCE>>>") anywhere in ANY message — system,
# user, or assistant. Before any other processing the token is stripped
# from every message (the downstream model never sees it) and ServiceNow
# context is treated as unconditionally armed for the request, like
# assume_servicenow_context. sentinel_inject chooses what goes in:
# "sections" (default) selects sections exactly as the armed heuristic
# path would; "full" injects the entire document verbatim, ignoring
# char_budget. Setting sentinel_token to "" disables the feature; with no
# sentinel present, behavior is identical to the heuristic path.
#
# The filter is global/always-on by design (no per-chat toggle): it runs for
# both the Open WebUI chat UI and direct /api/chat/completions callers such
# as MCP bridges or scripts. The three-tier keyword gating is what keeps it
# quiet on unrelated conversations. Deployments that only ever talk
# ServiceNow can set assume_servicenow_context=True (context always armed)
# or vocab_arm_threshold=1 (single vocab term fires alone).
#
# The filter is designed to NEVER break a chat: every failure path returns
# the body unmodified.

from __future__ import annotations

import asyncio
import inspect
import os
import re
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

# NOTE: `requests` is intentionally NOT imported at module level.
# It is imported lazily inside Filter._fetch_url() so that the filter loads
# even in environments where network fetching is never used or unavailable.


# ---------------------------------------------------------------------------
# Injection markers (used to find/replace our block on multi-turn chats)
# ---------------------------------------------------------------------------

MARKER_START = "<!-- GLIDEGRAIL-STANDARDS v1 -->"
MARKER_END = "<!-- /GLIDEGRAIL-STANDARDS -->"

_MARKER_BLOCK_RE = re.compile(
    re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"[ \t]*\n?",
    re.DOTALL,
)

INJECTION_HEADER = (
    "MANDATORY ServiceNow coding standards (GlideGrail). The sections below are "
    "authoritative for this conversation: when generating, reviewing, or explaining "
    "ServiceNow code or configuration, follow these standards exactly and prefer "
    "them over your default habits or generic best practices. If a user request "
    "conflicts with a standard, point out the conflict instead of silently ignoring it."
)

# After a URL fetch failure, skip re-fetch attempts for this many seconds so
# an outage does not add a network timeout to every message.
FETCH_RETRY_BACKOFF_S = 60


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _normalize_title(title: str) -> str:
    """Normalize a section title for dictionary keying.

    casefold, strip, collapse internal whitespace, and replace em-dash /
    en-dash with "-". Used identically for document headings, KEYWORD_MAP
    keys, and the always_include valve, so the three can never drift apart.
    """
    t = title.replace("—", "-").replace("–", "-")
    t = " ".join(t.split())  # collapse internal whitespace (also strips)
    return t.casefold()


_WORDISH_RE = re.compile(r"[A-Za-z0-9_$]")

# Match-time SQL guard for "update set" (v0.5.0). A regex lookbehind is
# fixed-width, so the old (?<!do\s) missed "DO  UPDATE SET" (double space)
# and "WHEN MATCHED THEN UPDATE SET" entirely. Instead, each candidate
# match inspects up to _GUARD_LOOKBACK preceding characters and is
# DISCARDED when they end in a DO/THEN keyword (arbitrary whitespace,
# newlines included). "move it into an update set" is unaffected.
_SQL_UPSERT_PRECEDER_RE = re.compile(r"(?:\b(?:do|then)\s*)$", re.IGNORECASE)
_GUARD_LOOKBACK = 12


class _PrecederGuardedPattern:
    """Duck-types the re.Pattern subset used by this filter (search /
    finditer), yielding only matches whose preceding text does NOT match
    guard_re — a variable-width, match-time replacement for a lookbehind."""

    def __init__(
        self,
        pattern: "re.Pattern[str]",
        guard_re: "re.Pattern[str]",
        lookback: int,
    ) -> None:
        self._pattern = pattern
        self._guard_re = guard_re
        self._lookback = lookback

    def finditer(self, text: str):
        for m in self._pattern.finditer(text):
            preceding = text[max(0, m.start() - self._lookback): m.start()]
            if not self._guard_re.search(preceding):
                yield m

    def search(self, text: str):
        return next(self.finditer(text), None)


def _compile_keyword(keyword: str) -> "re.Pattern[str]":
    """Compile a keyword into a case-insensitive, whitespace-relaxed regex.

    - re.escape() the keyword, then relax: any run of spaces matches \\s+.
    - Word boundaries are enforced with lookarounds (?<![\\w$]) / (?![\\w$])
      rather than \\b so keywords that start or end with non-word characters
      (e.g. "$sp.", "g:evaluate") still work. A boundary is only applied on
      a side whose edge character is word-like, so trailing punctuation such
      as "." does not block matches like "$sp.getParameter".
    - Keywords ending in "_" are PREFIX keywords: no trailing boundary is
      applied and any [a-z0-9_]* continuation is allowed, so "sn_" matches
      sn_hr_core, sn_customerservice, etc. The short prefixes "u_", "x_"
      and "sn_" are special-cased below with tighter guards.
    - "update set" gets a match-time preceding-text guard (see
      _PrecederGuardedPattern) so SQL upsert syntax ("... DO UPDATE SET",
      "WHEN MATCHED THEN UPDATE SET") can never match.
    - "now platform" carries a negative lookahead so ordinary English
      ("now platform independent/agnostic/specific/neutral") cannot match.
    """
    kw = keyword.strip()
    if kw == "u_":
        # Guarded custom-table prefix: u_ + at least THREE trailing chars.
        # The exclusions only match COMPLETE tokens (v0.5.0 recall fix —
        # the old (?!int|char|...) prefix test also killed real SN fields
        # like u_charge_code / u_shortcut / u_longitude):
        #   - the C fixed-width type family from sys/types.h as WHOLE
        #     tokens: u_int, u_int32, u_int32_t, u_char, u_short, u_long,
        #     u_quad_t (optional digits, optional _t suffix, then a word
        #     boundary). u_charge_code, u_shortcut, u_longitude,
        #     u_int_something all match now;
        #   - CFD/physics velocity fields: u_velocity / u_vel plus any
        #     underscore-separated continuation (u_velocity_field).
        return re.compile(
            r"(?<![\w$])u_(?!(?:int|char|short|long|quad)(?:\d+)?(?:_t)?\b)"
            r"(?!(?:velocity|vel)(?:_|\b))"
            r"[a-z0-9][a-z0-9_]{2,}",
            re.IGNORECASE,
        )
    if kw == "x_":
        # Guarded scoped-app prefix: SN custom scopes are x_<vendor>_<app>,
        # so require TWO underscore-separated segments after "x_" (a lone
        # "x_position" style variable cannot match) AND a first-segment
        # stoplist for common ML / plotting / HTTP variable families:
        # x_train_scaled, x_test_split, x_axis_label, x_forwarded_for,
        # x_tick_labels do not arm; x_acme_app still does.
        return re.compile(
            r"(?<![\w$])x_(?!(?:train|test|val|axis|min|max|pos|offset"
            r"|forwarded|coord|scale|label|data|value|tick)(?:_|\b))"
            r"[a-z0-9]+_[a-z0-9][a-z0-9_]*",
            re.IGNORECASE,
        )
    if kw == "sn_":
        # Prefix signal for SN scope/app names (sn_hr_core,
        # sn_customerservice, ...) with a stoplist for engineering
        # signal-to-noise terms: sn_ratio / sn_curve(s) (Taguchi methods,
        # fatigue analysis) are complete-token exclusions.
        return re.compile(
            r"(?<![\w$])sn_(?!(?:ratio|curve)s?\b)[a-z0-9_]*",
            re.IGNORECASE,
        )
    if kw.casefold() == "now platform":
        # "the Now Platform" is a ServiceNow signal, but "now platform
        # independent/agnostic/specific/neutral" is ordinary English.
        return re.compile(
            r"(?<![\w$])now\s+platform"
            r"(?![\s-]+(?:independent|agnostic|specific|neutral)\b)"
            r"(?![\w$])",
            re.IGNORECASE,
        )
    if kw.casefold() == "update set":
        # SQL upsert guard: "DO UPDATE SET" (any whitespace, incl. the
        # double-spaced form) and "WHEN MATCHED THEN UPDATE SET" must not
        # count as the ServiceNow artifact. Match-time check — see
        # _PrecederGuardedPattern.
        return _PrecederGuardedPattern(
            re.compile(r"(?<![\w$])update\s+set(?![\w$])", re.IGNORECASE),
            _SQL_UPSERT_PRECEDER_RE,
            _GUARD_LOOKBACK,
        )
    escaped = re.escape(kw)
    # Since Python 3.7 re.escape() escapes the space character (special under
    # re.VERBOSE); un-escape it first so the relax step below sees plain spaces.
    escaped = escaped.replace("\\ ", " ")
    relaxed = re.sub(r" +", r"\\s+", escaped)
    prefix = r"(?<![\w$])" if kw and _WORDISH_RE.match(kw[0]) else ""
    if kw.endswith("_"):
        # Prefix keyword: match the literal prefix plus any word-ish tail.
        return re.compile(prefix + relaxed + r"[a-z0-9_]*", re.IGNORECASE)
    suffix = r"(?![\w$])" if kw and _WORDISH_RE.match(kw[-1]) else ""
    return re.compile(prefix + relaxed + suffix, re.IGNORECASE)


# ---------------------------------------------------------------------------
# Keyword map: document section title -> three keyword tiers.
#
#   "specific": ServiceNow-unique API tokens ONLY (Glide* classes, gs.* /
#       g_form / g_scratchpad / $sp APIs, sys_* / sc_* / cmdb_ci tables,
#       AbstractAjaxProcessor, sn_cicd, ...). The bar: NO plausible
#       non-ServiceNow developer sentence contains the token. ONE specific
#       hit selects its section unconditionally AND establishes ServiceNow
#       context for the whole scanned window.
#   "vocab": ServiceNow-flavored but ecosystem-ambiguous phrases (business
#       rule, acl, update set, cmdb, flow designer, ...). A SINGLE vocab hit
#       in isolation does NOTHING. Arming uses WITNESS COUNTING (see
#       _vocab_witnesses): matched occurrences are collected as (start, end)
#       spans over the scanned text, OVERLAPPING spans merge into one
#       occurrence ("service catalog items" is ONE witness even though
#       "service catalog" and "catalog items" both match), and each merged
#       occurrence maps to a CONCEPT GROUP via VOCAB_GROUPS (near-synonyms
#       such as the before/after-insert/update/delete family count once).
#       At vocab_arm_threshold >= 2 (default), context arms when that many
#       DISTINCT groups are witnessed AND at least one witnessed group is
#       STRONG (STRONG_VOCAB — terms a developer usually only says about
#       ServiceNow) AND no PLATFORM_VETO competitor token is present. At
#       vocab_arm_threshold == 1 (documented SN-leaning profile) any single
#       witness arms (still subject to the veto). Once armed, ALL vocab
#       hits fire their sections and generic hits count too.
#   "generic": ordinary developer vocabulary (try catch, oauth, flexbox...).
#       Generic hits only count when ServiceNow context is present: a
#       GENERIC_SN_SIGNALS match, a specific hit, or a vocab pair. They
#       never establish context themselves, so non-ServiceNow chats get
#       nothing injected.
#
# The tier test for every keyword: "does any plausible non-ServiceNow
# developer sentence contain this?" Never -> specific. Yes, but a ServiceNow
# developer would recognize it as platform terminology -> vocab. Plain
# cross-platform vocabulary -> generic.
#
# (Titles contain em-dashes exactly as in GlideGrail.md; _normalize_title
#  makes them match the parsed document keys.)
# ---------------------------------------------------------------------------

KEYWORD_MAP: Dict[str, Dict[str, List[str]]] = {
    "Agent Ground Rules": {
        "specific": [
            "updateMultiple",
            "deleteMultiple",
        ],
        "vocab": [
            "acl",
            "acls",
            "access control",
        ],
        "generic": [
            "ground rules",
            "mass update",
            "mass delete",
            "bulk update",
            "bulk delete",
            "data migration",
            "database index",
            "destructive operation",
        ],
    },
    "Technical Debt": {
        "specific": [],
        "vocab": [
            "baseline record",
        ],
        "generic": [
            "technical debt",
            "tech debt",
            "gold plating",
            "gold-plating",
            "upgrade risk",
        ],
    },
    "Naming Conventions": {
        "specific": [],
        "vocab": [
            "update set",
            "update sets",
        ],
        "generic": [
            "naming convention",
            "naming conventions",
            "snake_case",
            "camelCase",
            "PascalCase",
            "kebab-case",
            "variable naming",
            "widget id",
            "how should I name",
            "what should I name",
        ],
    },
    "General Coding Standards": {
        "specific": [
            "getUniqueValue",
            "dot-walk",
            "dot walk",
            "dot-walking",
            "GlideElement",
            "GlideDateTime",
            "GlideRecordSecure",
            "glide.servlet.uri",
        ],
        "vocab": [],
        "generic": [
            "coding standards",
            "instance url",
            "self-executing function",
            "IIFE",
            "timezone",
            "forEach",
            "scheduled job",
        ],
    },
    "Application Scope": {
        "specific": [],
        "vocab": [
            # "scoped app"/"scoped application" demoted from specific in
            # v0.4.0: "a narrowly scoped app - just an expense tracker in
            # Flask" is a confirmed non-SN sentence. Strong vocab instead.
            "scoped app",
            "scoped application",
            "cross-scope",
            "cross scope",
        ],
        "generic": [
            "application scope",
            "global scope",
            "app scope",
            "custom application",
            "accessible from",
        ],
    },
    "Configurability": {
        "specific": [
            "gs.getProperty",
            "glide.servlet.uri",
            "hardcoded sys_id",
        ],
        "vocab": [],
        "generic": [
            "configurability",
            "hardcoded url",
            "hardcoded value",
            "feature toggle",
            "config table",
            "instance url",
        ],
    },
    "Code Readability": {
        "specific": [
            "getRefRecord",
            "vaVars",
            "g:evaluate",
        ],
        "vocab": [
            "getElement",
        ],
        "generic": [
            "readability",
            "JSDoc",
            "ternary",
            "single responsibility",
            "eval",
            "inline comments",
            "code comments",
            "jelly",
            "JEXL",
        ],
    },
    "Official API Preference": {
        "specific": [
            "gs.nil",
            "gs.getUserID",
            "gs.getUserName",
            "gs.hasRole",
            "GlideAggregate",
            "g_form",
        ],
        "vocab": [
            "journal field",
        ],
        "generic": [
            "official api",
            "setValue",
            "getValue",
            "getDisplayValue",
            "hasRole",
        ],
    },
    "Do Not Use": {
        "specific": [
            "setWorkflow",
            "gs.sleep",
            "gs.log",
            "GlideQuery",
            "GlideAjax",
            "getXMLAnswer",
            "hardcoded sys_id",
        ],
        "vocab": [
            "merging update sets",
        ],
        "generic": [
            "getReference",
            "getRowCount",
            "getXML",
            "dom manipulation",
            "legacy workflow",
            "anti-pattern",
            "anti pattern",
        ],
    },
    "Tables, Fields & Choices": {
        "specific": [
            "TaskStateUtil",
            "close_states",
            "default_close_state",
            "dot-walked",
        ],
        "vocab": [
            "state model",
            "choice list",
        ],
        "generic": [
            "state field",
            "choice field",
            "calculated field",
            "default value",
            "derived field",
            "choice values",
        ],
    },
    "Database Views": {
        "specific": [],
        "vocab": [
            "database view",
            "database views",
            "dv_",
        ],
        "generic": [],
    },
    "System Properties": {
        "specific": [
            "sys_properties",
            "gs.getProperty",
        ],
        "vocab": [],
        "generic": [
            "system property",
            "system properties",
            "getProperty",
            "user preference",
            "user preferences",
            "settings table",
            "application settings",
            "cache flush",
        ],
    },
    "GlideRecord": {
        "specific": [
            "GlideRecord",
            "GlideAggregate",
            "GlideQuery",
            "GlideElement",
            "addEncodedQuery",
            "addJoinQuery",
            "getUniqueValue",
            "dot-walk",
            "dot walking",
        ],
        "vocab": [
            "encoded query",
            "addQuery",
        ],
        "generic": [
            "getRowCount",
            "setLimit",
            "getValue",
            "getDisplayValue",
        ],
    },
    "Performance at Scale": {
        "specific": [
            "updateMultiple",
            "deleteMultiple",
            "gs.getProperty",
        ],
        "vocab": [],
        "generic": [
            "slow query",
            "slow queries",
            "database index",
            "table index",
            "query performance",
            "large table",
            "scheduled job",
            "batch processing",
        ],
    },
    "GlideForm": {
        "specific": [
            "g_form",
            "GlideForm",
            "g_form.setValue",
        ],
        "vocab": [
            "client script",
        ],
        "generic": [
            "setValue",
            "reference field",
            "display value",
        ],
    },
    "GlideAJAX": {
        "specific": [
            "GlideAjax",
            "getXMLAnswer",
            "g_scratchpad",
        ],
        "vocab": [
            "service catalog",
        ],
        "generic": [
            "getXML",
            "getReference",
            "onChange",
            "onLoad",
            "ajax call",
            "synchronous ajax",
        ],
    },
    "Script Includes": {
        "specific": [
            "AbstractAjaxProcessor",
            "hardcoded sys_id",
        ],
        "vocab": [
            "script include",
            "script includes",
            "client callable",
            "client-callable",
        ],
        "generic": [
            "getParameter",
            "scope prefix",
        ],
    },
    "UI Policies": {
        "specific": [],
        "vocab": [
            "ui policy",
            "ui policies",
            "catalog item",
            "record producer",
        ],
        "generic": [
            # "data policy" demoted to generic in v0.4.0: it is core
            # Purview/Collibra data-governance vocabulary (confirmed FP).
            "data policy",
            "mandatory field",
            "mandatory fields",
            "read-only field",
            "read only field",
            "field visibility",
        ],
    },
    "Business Rules": {
        "specific": [
            "setWorkflow",
            "autoSysFields",
            "changesTo",
            "changesFrom",
            # v0.5.0: bare "business rule(s)" was demoted STRONG->WEAK
            # (pervasive DDD/Drools/BPMN English), so the canonical
            # timing+type compound phrases are SPECIFIC — nobody outside
            # ServiceNow says "before insert business rule". The span-merge
            # witness engine folds the shorter constituent matches
            # ("before insert", "business rule") into the compound.
            "before insert business rule",
            "after insert business rule",
            "before update business rule",
            "after update business rule",
            "before delete business rule",
            "after delete business rule",
            "async business rule",
            "display business rule",
            "query business rule",
        ],
        "vocab": [
            "business rule",
            "business rules",
            "current.update",
            "current.operation",
            "before insert",
            "after insert",
            "before update",
            "after update",
            "before delete",
            "after delete",
        ],
        "generic": [],
    },
    "Events": {
        "specific": [
            "gs.eventQueue",
        ],
        "vocab": [
            "parm1",
            "parm2",
        ],
        "generic": [
            "eventQueue",
            "event registry",
            "event queue",
            "script action",
            "fire an event",
            "queue an event",
            "email notification",
        ],
    },
    "Client Scripts": {
        "specific": [
            "g_form",
            "GlideAJAX",
            "getXMLAnswer",
            "g_scratchpad",
            # Promoted back to specific in v0.4.0: the full phrase is
            # ServiceNow-unique in practice (p4-family rescue).
            "catalog client script",
        ],
        "vocab": [
            "client script",
            "onCellEdit",
            "ui policy",
        ],
        "generic": [
            "onLoad",
            "onChange",
            "onSubmit",
            "getReference",
        ],
    },
    "UI Actions": {
        "specific": [
            "gsftSubmit",
            "g_modal",
            "g_aw",
            "GlideModal",
            "workspace client script",
            "workspace form button",
            "ux form action",
        ],
        "vocab": [
            "ui action",
            "setRedirectURL",
            "setReturnURL",
            "agent workspace",
            "configurable workspace",
            "declarative action",
        ],
        "generic": [],
    },
    "Access Control Lists (ACLs)": {
        "specific": [
            "glide.sm.default_mode",
        ],
        "vocab": [
            "security_admin",
            "query business rule",
            "acl",
            "acls",
            "access control",
        ],
        "generic": [
            "access control list",
            "before query",
            "debug security",
            "access analyzer",
            "impersonate",
            "impersonation",
            "high security settings",
            "field-level acl",
        ],
    },
    "Logging": {
        "specific": [
            "gs.info",
            "gs.warn",
            "gs.error",
            "gs.debug",
            "gs.log",
            "GSLog",
        ],
        "vocab": [],
        "generic": [
            "syslog",
            "log level",
            "log source",
            "log prefix",
            "temp debug",
            "logging",
            "log errors",
            "log an error",
            "error log",
        ],
    },
    "Error Handling": {
        "specific": [
            "setAbortAction",
            "gs.addErrorMessage",
        ],
        "vocab": [
            "addErrorMessage",
        ],
        "generic": [
            "error handling",
            "try catch",
            "try/catch",
            "catch block",
            "empty catch",
            "exception handling",
            "uncaught exception",
            "return contract",
            "result object",
        ],
    },
    "Operational Hygiene": {
        "specific": [
            "gs.eventQueue",
            "ecc queue",
        ],
        "vocab": [
            "mid server",
            "update set",
        ],
        "generic": [
            "event log",
            "eventQueue",
            "slow query",
            "slow queries",
            "system logs",
            "node log",
            "stuck email",
            "go-live",
            "go live",
            "event processor",
        ],
    },
    "Messages & i18n": {
        "specific": [
            "sys_ui_message",
            "gs.getMessage",
        ],
        "vocab": [],
        "generic": [
            "getMessage",
            "i18n",
            "localization",
            "localisation",
            "message key",
            "message keys",
            "ui message",
            "translatable",
            "translation key",
            "user-facing message",
        ],
    },
    "Notifications": {
        "specific": [],
        "vocab": [
            # "send to event creator" demoted from specific in v0.4.0:
            # plausible English in any eventing/webhook conversation. Weak.
            "send to event creator",
            "mail script",
            "mail scripts",
            "mail_script",
        ],
        "generic": [
            "email notification",
            "email notifications",
            "email template",
            "email templates",
            "email layout",
            "notification email",
        ],
    },
    "Scheduled Jobs": {
        "specific": [
            "sysauto",
            "sysauto_script",
        ],
        "vocab": [
            "scheduled script execution",
        ],
        "generic": [
            "scheduled job",
            "scheduled jobs",
            "run_as",
            "run as user",
            "scheduled flow",
            "cron",
            "nightly job",
        ],
    },
    "Multi-row Variable Sets (MRVS)": {
        "specific": [
            "multi-row variable set",
            "multi-row variable sets",
            "multi row variable set",
            "multi row variable sets",
            "multirow variable set",
        ],
        "vocab": [
            "mrvs",
        ],
        "generic": [
            "getRowCount",
            "getRow",
        ],
    },
    "Attachments": {
        "specific": [
            "GlideSysAttachment",
            "sys_attachment",
        ],
        "vocab": [],
        "generic": [
            "attach a file",
            "copy attachment",
            "copy attachments",
            "move attachment",
            "move attachments",
            "attachment size",
        ],
    },
    "Service Catalog — Items & Record Producers": {
        "specific": [
            "sc_req_item",
            "sc_request",
            "ritm",
            "catalog ui policy",
            # Promoted back to specific in v0.4.0 (see Client Scripts).
            "catalog client script",
        ],
        "vocab": [
            "service catalog",
            "catalog item",
            "catalog items",
            "record producer",
            "record producers",
            "catalog variable",
            "order guide",
            "catalog task",
            "two-step checkout",
        ],
        "generic": [
            "variable set",
        ],
    },
    "Update Sets": {
        "specific": [
            "sys_update_xml",
        ],
        "vocab": [
            "update set",
            "update sets",
            "add to application file",
            "update set collision",
            "hotfix update set",
            "fix script",
            "fix scripts",
        ],
        "generic": [
            "background script",
            "import xml",
            "xml import",
            "export xml",
            "xml export",
            "promotion list",
            "application repository",
        ],
    },
    "Flow Designer": {
        "specific": [
            "integrationhub",
            "gs.sleep",
        ],
        "vocab": [
            "flow designer",
            "integration hub",
        ],
        "generic": [
            "subflow",
            "subflows",
            "wait for condition",
            "wait for conditions",
            "flow action",
            "flow actions",
            "flow trigger",
            "trigger table",
            "flow reporting",
            "legacy workflow",
        ],
    },
    "CMDB": {
        "specific": [
            "cmdb_ci",
            "cmdb_rel_type",
            "cmdb_rel_type_suggest",
        ],
        "vocab": [
            "cmdb",
            "cmdb health dashboard",
            "ci class manager",
            "ci class",
            "ci classes",
            "identification rule",
        ],
        "generic": [
            "configuration item",
            "configuration items",
            "suggested relationship",
            "suggested relationships",
        ],
    },
    "UI Builder (Next Experience)": {
        "specific": [
            "macroponent",
            "sys_ux_app_route",
            "sys_ux_form_action",
            "sys_ux_applicability",
            "ux page property",
        ],
        "vocab": [
            "next experience",
            "configurable workspace",
            "agent workspace",
            "chrome_header",
            "declarative action",
            "client state parameter",
        ],
        "generic": [
            "ui builder",
            "page variant",
            "page variants",
            "tab set",
        ],
    },
    "Service Portal — Widgets": {
        "specific": [
            "widget client script",
            "widget server script",
            "widget html template",
            # Promoted back to specific in v0.4.0 (p4 rescue): the FULL
            # phrase "service portal widget" and the sp_widget table name
            # are ServiceNow-unique; the fragments "service portal" and
            # "portal widget" stay (strong) vocab so "customer service
            # portal in Next.js" remains silent.
            "service portal widget",
            "sp_widget",
        ],
        "vocab": [
            "service portal",
            "portal widget",
            "sp widget",
        ],
        "generic": [
            "widget development",
            "client controller",
        ],
    },
    "Service Portal — AngularJS Providers": {
        "specific": [
            "appNameModule",
        ],
        "vocab": [],
        "generic": [
            "angularjs",
            "angular provider",
            "angular directive",
            "angular service",
            "angular factory",
            "angular module",
            "custom directive",
            "link function",
            "factory vs service",
            "service vs factory",
            "gulp",
        ],
    },
    "Service Portal — Server Communication": {
        "specific": [
            "c.server.get",
            "c.server.update",
            "GlideRecordSecure",
        ],
        "vocab": [
            "widget round trip",
            "scripted rest",
        ],
        "generic": [
            "server.get",
            "server.update",
            "round trip",
            "table api",
        ],
    },
    "Service Portal — Client-Side State": {
        "specific": [
            "putClientData",
            "gs.getSession",
        ],
        "vocab": [],
        "generic": [
            "sessionStorage",
            "localStorage",
            "web storage",
            "user preference",
            "user preferences",
            "rootScope",
            "client-side state",
            "state between widgets",
            "widget to widget",
        ],
    },
    "Service Portal — SCSS": {
        "specific": [],
        "vocab": [],
        "generic": [
            "scss",
            "sass",
            "widget css",
            "widget scss",
            "portal css",
            "portal theme",
            "theme css",
            "css include",
            "css specificity",
            "bootstrap override",
            "scss variable",
        ],
    },
    "Service Portal — Styling Conventions": {
        "specific": [],
        "vocab": [],
        "generic": [
            "bem",
            "block element modifier",
            "css naming",
            "class naming",
            "oocss",
            "smacss",
            "flexbox",
            "css grid",
            "utility class",
            "styling convention",
            "class prefix",
            "modifier class",
        ],
    },
    "Service Portal — Accessibility (WCAG)": {
        "specific": [],
        "vocab": [],
        "generic": [
            "wcag",
            "accessibility",
            "a11y",
            "aria-label",
            "aria-labelledby",
            "screen reader",
            "keyboard navigation",
            "tabindex",
            "focus indicator",
            "color contrast",
            "colour contrast",
            "semantic html",
        ],
    },
    "Service Portal — Moment.js i18n": {
        "specific": [
            "g_lang",
        ],
        "vocab": [],
        "generic": [
            "moment.js",
            "momentjs",
            "moment.locale",
            "moment locale",
            "widget dependency",
            "js include",
            "js includes",
            "i18n",
            "date translation",
            "locale file",
        ],
    },
    "Automated Test Framework (ATF)": {
        "specific": [
            "impersonate step",
            "sn_cicd",
            # LOW-risk collision: Kotlin coroutines docs say "Flow API"
            # (with a space) or flowOf(); the single token "FlowAPI" is the
            # ServiceNow server-side class. Kept specific deliberately.
            "FlowAPI",
        ],
        "vocab": [
            "atf",
            "record insert step",
            "run server side script",
            "client test runner",
        ],
        "generic": [
            "automated test framework",
            "test suite",
            "impersonate",
            "jasmine",
            "assertEqual",
            "parameterized test",
            "base test",
        ],
    },
    "Import Sets & Transform Maps": {
        "specific": [
            "sys_import_set_row",
            "import set deleter",
        ],
        "vocab": [
            "import set",
            "transform map",
            "choice action",
            "reference value field",
        ],
        "generic": [
            "staging table",
            "coalesce",
            "onBefore",
            "onAfter",
            "onComplete",
            "scheduled import",
            "ldap import",
            "csv import",
        ],
    },
    "Integrations — General": {
        "specific": [
            "sys_import_set_row",
            "Connector4U",
        ],
        "vocab": [
            "import set",
            "transform map",
        ],
        "generic": [
            "non-repudiation",
            "non repudiation",
            "bi-directional integration",
            "bidirectional integration",
            "outbound integration",
            "inbound integration",
            "integration logging",
            "integration error handling",
            "integration loop",
            "integration design",
        ],
    },
    "Integrations — Scripted REST API": {
        "specific": [
            "scripted rest api",
        ],
        "vocab": [
            "scripted rest",
        ],
        "generic": [
            "custom rest api",
            "rest endpoint",
            "rest resource",
            "inbound rest",
            "api versioning",
            "api version",
            "http status code",
            "ServiceError",
            "setStatus",
            "setMessage",
            "setDetail",
        ],
    },
    "Integrations — Integration Hub & Custom Spokes": {
        "specific": [
            "integrationhub",
            "spoke action",
            "RESTMessageV2",
            "connection and credential alias",
        ],
        "vocab": [
            "integration hub",
            "custom spoke",
            "mid server",
            "action designer",
            "flow designer",
            "data stream action",
        ],
        "generic": [
            "credential alias",
            "subflow",
            "jdbc step",
            "rest step",
            "webhook",
        ],
    },
    "Integrations — OAuth 2.0": {
        "specific": [],
        "vocab": [],
        "generic": [
            "oauth",
            "oauth2",
            "oauth 2.0",
            "client credentials",
            "authorization code",
            "resource owner password",
            "access token",
            "refresh token",
            "token refresh",
            "oauth provider",
            "oauth profile",
            "client secret",
        ],
    },
    "Integrations — LDAP User Import": {
        "specific": [
            "sys_user",
            "sys_user_group",
        ],
        "vocab": [
            "ou definition",
        ],
        "generic": [
            "ldap",
            "ldaps",
            "active directory",
            "distinguished name",
            "objectGUID",
            "objectClass",
            "userAccountControl",
            "samAccountName",
            "user import",
            "user provisioning",
            "coalesce",
        ],
    },
    "Integrations — Security": {
        "specific": [
            "GlideRecordSecure",
            "web service access only",
        ],
        "vocab": [
            "password2",
            "acl",
            "access control",
        ],
        "generic": [
            "basic auth",
            "basic authentication",
            "mutual authentication",
            "integration user",
            "ip address access control",
            "ip access control",
            "ip whitelist",
            "itil role",
        ],
    },
}


# ---------------------------------------------------------------------------
# Concept groups for vocab witness counting. Near-synonyms and family
# variants of ONE ServiceNow concept count as ONE witness, so "before insert
# and before update" (Salesforce Apex uses the same timing names) or
# "ACLs for access control" can never self-corroborate into arming. Any
# vocab keyword not listed here forms its own implicit one-keyword group.
# Group membership is by casefolded keyword string; listing strings that are
# not (or no longer) vocab keywords is harmless.
# ---------------------------------------------------------------------------

VOCAB_GROUPS: List[List[str]] = [
    # Business-rule timing family (shared verbatim with Salesforce Apex
    # trigger contexts and generic DB-trigger vocabulary).
    [
        "before insert", "after insert", "before update", "after update",
        "before delete", "after delete",
    ],
    # Access-control family (S3 ACLs, POSIX ACLs, generic security English).
    ["acl", "acls", "access control", "access control list"],
    # Service-catalog family (AWS Service Catalog, data catalogs).
    [
        "service catalog", "catalog item", "catalog items",
        "catalog variable", "catalog variables", "catalog task",
        "order guide", "order guides", "two-step checkout",
    ],
    # CMDB family (iTop, Device42, ITIL-general vocabulary).
    ["cmdb", "cmdb health dashboard", "ci class", "ci classes",
     "ci class manager"],
    # Event parm family (T-SQL @parm1/@parm2 style parameter naming).
    ["parm1", "parm2"],
    # Update-set family (siblings share the concept).
    ["update set", "update sets", "merging update sets",
     "update set collision", "hotfix update set"],
    # Business-rule family.
    ["business rule", "business rules", "display business rule",
     "query business rule"],
    # Singular/plural + close-sibling pairs (span merging already prevents
    # double counting from ONE phrase; grouping also collapses separate
    # mentions, which is the honest reading of "one concept").
    ["record producer", "record producers"],
    ["script include", "script includes"],
    ["ui policy", "ui policies"],
    ["ui action", "ui actions"],
    ["service portal", "portal widget", "sp widget"],
    ["mail script", "mail scripts", "mail_script"],
    ["fix script", "fix scripts"],
    ["scoped app", "scoped application"],
    ["client callable", "client-callable"],
    ["cross-scope", "cross scope"],
    ["current.update", "current.operation"],
    ["setRedirectURL", "setReturnURL"],
    ["agent workspace", "configurable workspace"],
    ["database view", "database views", "dv_"],
]

# ---------------------------------------------------------------------------
# STRONG vocab witnesses: terms a developer saying them usually means
# ServiceNow. Arming at vocab_arm_threshold >= 2 requires at least one
# witnessed group to contain a strong keyword; WEAK-only combinations
# (e.g. Postgres "before insert trigger that checks the acl table") stay
# silent. Everything in the vocab tier but NOT listed here is weak:
# acl/access-control family, BR-timing family, parm1/parm2, cmdb family,
# client script, encoded query, cross-scope, mail scripts, agent workspace,
# atf, import set, send to event creator, and the rest of the
# generic-English-plausible tail.
#
# Demoted STRONG -> WEAK in v0.5.0 (confirmed false-positive sources):
#   - "business rule(s)": pervasive DDD/Drools/BPMN English (the canonical
#     "<timing> business rule" compounds are SPECIFIC-tier instead);
#   - "fix script(s)": ordinary verb+noun English;
#   - "scoped app"/"scoped application": "a narrowly scoped app" is plain
#     English (Flask FP with "access control").
# ---------------------------------------------------------------------------

STRONG_VOCAB: frozenset = frozenset(
    k.casefold()
    for k in [
        "update set", "update sets", "merging update sets",
        "update set collision", "hotfix update set",
        "record producer", "record producers",
        "flow designer",
        "transform map",
        "script include", "script includes",
        "ui policy", "ui policies",
        "ui action", "ui actions",
        "service portal", "portal widget", "sp widget",
        "service catalog", "catalog item", "catalog items",
        "catalog variable", "catalog task", "order guide",
        "two-step checkout",
        "scripted rest",
        "mid server",
        "next experience",
        "mrvs",
    ]
)

# ---------------------------------------------------------------------------
# NEGATIVE vocab: phrases that CONTAIN a vocab keyword but are evidence of a
# NON-ServiceNow topic. They compile like vocab keywords and participate in
# span merging; when a merged occurrence's LONGEST constituent is a negative
# entry, the whole occurrence is DISCARDED — it contributes no witness, and
# vocab-tier section selection ignores matches inside its span. "customer
# service portal in Next.js; the catalog items page needs pagination"
# therefore has no service-portal witness (and the Service Portal section
# cannot fire off that phrase). Residual: ServiceNow CSM users discussing
# their own customer service portal need one more witness or an SN signal.
# ---------------------------------------------------------------------------

NEGATIVE_VOCAB: List[str] = [
    "customer service portal",
]

# ---------------------------------------------------------------------------
# Platform veto: unambiguous COMPETITOR/other-product tokens. A veto match
# suppresses vocab-witness arming ONLY — "should this be a business rule or
# a Power Automate flow designer flow?" is a Dynamics conversation, not a
# ServiceNow one. Specific-tier hits and GENERIC_SN_SIGNALS still arm
# normally ("In ServiceNow ... migrating from Power Automate" fires), and
# once armed everything fires as usual.
#
# v0.5.0 override: the veto only suppresses arming when FEWER THAN TWO
# witnessed groups are STRONG — two independent strong ServiceNow concepts
# (e.g. "update set" + "transform map") outweigh a product mention, so
# migration prompts that name a competitor still fire.
#
# v0.5.0 narrowing (recall-costing bare English removed): "purview" ("under
# the purview of the security team" suppressed a genuine SN prompt) is now
# "microsoft purview"/"azure purview"; "backstage" (theatre/idiom English)
# is now "backstage.io"/"spotify backstage"/"backstage catalog".
# ---------------------------------------------------------------------------

PLATFORM_VETO: List[str] = [
    "salesforce",
    "apex trigger",
    "apex class",
    "dynamics 365",
    "power automate",
    "power apps",
    "microsoft purview",
    "azure purview",
    "collibra",
    "zendesk",
    "itop",
    "freshservice",
    "freshdesk",
    "backstage.io",
    "spotify backstage",
    "backstage catalog",
    "sharepoint",
    "liferay",
    "jira service management",
    "bmc remedy",
    "cherwell",
    # ITSM competitors sharing ServiceNow vocabulary (v0.5.0):
    "manageengine",
    "servicedesk plus",
    "sysaid",
    "ivanti",
    "topdesk",
    "halo itsm",
    "haloitsm",
    "solarwinds service desk",
    # Commerce/streaming false-positive sources (catalog items, record
    # producers, service portals in the other sense):
    "shopify",
    "magento",
    "kafka",
]


# ---------------------------------------------------------------------------
# Generic ServiceNow signals. These serve two purposes:
#   1. They establish ServiceNow context, which arms the vocab and generic
#      keyword tiers in KEYWORD_MAP (see the three-tier notes above).
#   2. They gate the token-overlap search fallback when no topical keyword
#      matched but the prompt is clearly ServiceNow-related.
# "sn_" is a guarded prefix keyword: it matches any sn_* token (sn_hr_core,
# sn_customerservice, ...) except the engineering S/N terms sn_ratio /
# sn_curve(s). "u_" is the guarded custom-table prefix (u_vault_flip): it
# requires three or more trailing characters and excludes COMPLETE C
# u_int*/u_char/... type tokens and u_velocity/u_vel CFD fields (see
# _compile_keyword). "x_" is the guarded scoped-app prefix: it requires two
# segments (x_vendor_app) and stoplists common ML/plotting first segments
# (x_train_scaled, x_axis_label never match; x_acme_app does). "now
# platform" refuses "now platform independent/agnostic/specific/neutral".
#
# Removed in v0.4.0 (confirmed false positives): bare "glide" (the Android
# Glide image-loading library), bare "snc" (SAP Secure Network
# Communications), and "scoped app"/"scoped application" ("a narrowly
# scoped app in Flask" is ordinary English). Removed in v0.5.0: bare
# "service now" ("is the auth service now returning 401" — plain English;
# "servicenow" and "service-now" stay).
# ---------------------------------------------------------------------------

GENERIC_SN_SIGNALS: List[str] = [
    "servicenow",
    "service-now",
    "now platform",
    "servicenow instance",
    "personal developer instance",
    "glidesystem",
    "glideajax",
    "gliderecord",
    "sys_id",
    "sn_ prefix",
    "sn_",
    "u_",
    "x_",
]


# ---------------------------------------------------------------------------
# Search-fallback tokenizer support
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9_]{3,}")

_STOPWORDS = frozenset(
    {
        "the", "and", "for", "with", "that", "this", "from", "are", "was",
        "were", "will", "would", "should", "could", "can", "cannot", "not",
        "but", "have", "has", "had", "you", "your", "our", "their", "they",
        "them", "its", "how", "what", "when", "where", "which", "why", "who",
        "all", "any", "some", "one", "two", "get", "got", "use", "used",
        "using", "need", "needs", "want", "wants", "does", "did", "doing",
        "please", "help", "about", "into", "onto", "out", "over", "under",
        "just", "like", "make", "made", "also", "than", "then", "there",
        "here", "been", "being", "because", "way", "best", "good", "write",
        "writing", "code", "new", "let", "know", "tell", "give", "show",
    }
)


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Filter execution priority (lower runs earlier).",
        )
        source_path: str = Field(
            default="/app/backend/data/glidegrail/GlideGrail.md",
            description=(
                "Local path to GlideGrail.md inside the Open WebUI container. "
                "Preferred over source_url when the file exists; re-read when "
                "its mtime changes."
            ),
        )
        source_url: str = Field(
            default="https://raw.githubusercontent.com/bikemeardsley/GlideGrail.md/main/skills/glidegrail/GlideGrail.md",
            description=(
                "Fallback raw URL for GlideGrail.md, used when source_path does "
                "not exist. Fetched text is cached in memory for cache_ttl_minutes."
            ),
        )
        cache_ttl_minutes: int = Field(
            default=1440,
            description="How long (minutes) to cache the document fetched from source_url.",
        )
        char_budget: int = Field(
            default=24000,
            description=(
                "Maximum characters of injected standards. Sections are dropped "
                "(lowest priority first) to fit; a lone oversized section is truncated."
            ),
        )
        scan_last_n_user_messages: int = Field(
            default=3,
            description="How many of the most recent user messages to scan for triggers.",
        )
        vocab_arm_threshold: int = Field(
            default=2,
            ge=1,
            description=(
                "How many DISTINCT vocab concept-group witnesses (overlapping "
                "matches span-merged, near-synonyms grouped) are needed to "
                "establish ServiceNow context. At 2+ (default, for general/"
                "shared instances) at least one witness must also be a STRONG "
                "term and no competitor-platform veto token may be present. "
                "1 suits ServiceNow-leaning instances where a single term "
                "like 'acl' should fire alone."
            ),
        )
        assume_servicenow_context: bool = Field(
            default=False,
            description=(
                "Treat ServiceNow context as ALWAYS established: vocab and "
                "generic keywords fire like specific ones, and the search "
                "fallback's ServiceNow-signal gate is considered satisfied. "
                "For dedicated ServiceNow instances, custom models, or "
                "MCP/API pipelines that only ever discuss ServiceNow."
            ),
        )
        sentinel_token: str = Field(
            default="<<<GLIDEGRAIL_ENFORCE>>>",
            description=(
                "Deterministic trigger for pipeline/bridge callers: when "
                "this exact string appears in ANY message (system, user, "
                "or assistant), injection is guaranteed — the token is "
                "stripped from every message (the model never sees it) and "
                "ServiceNow context is treated as unconditionally armed. "
                "Empty string disables the feature."
            ),
        )
        sentinel_inject: str = Field(
            default="sections",
            description=(
                "What a sentinel trigger injects: 'sections' selects "
                "sections exactly like the armed heuristic path "
                "(char_budget enforced); 'full' injects the ENTIRE "
                "document verbatim, IGNORING char_budget — only for "
                "big-context cloud models (the document is roughly 40-50k "
                "tokens; small local models will silently truncate)."
            ),
        )
        search_fallback: bool = Field(
            default=True,
            description=(
                "When no topical keyword matches but the prompt looks "
                "ServiceNow-related, run a token-overlap search over the "
                "document sections."
            ),
        )
        search_top_k: int = Field(
            default=2,
            description="Maximum number of sections the search fallback may select.",
        )
        min_search_score: int = Field(
            default=3,
            description="Minimum token-overlap score a section needs to be selected by the search fallback.",
        )
        always_include: str = Field(
            default="Agent Ground Rules, Do Not Use",
            description=(
                "Comma-separated section titles injected whenever any other "
                "section fires (never on their own)."
            ),
        )
        show_status: bool = Field(
            default=True,
            description="Emit a status event in the UI describing what was injected.",
        )
        debug: bool = Field(
            default=False,
            description="Print diagnostic messages (prefixed [glidegrail]) to the server log.",
        )

    def __init__(self) -> None:
        self.valves = self.Valves()

        self._lock = threading.Lock()
        # norm_title -> (original_title, full_section_text) in DOCUMENT order
        self._sections: "OrderedDict[str, Tuple[str, str]]" = OrderedDict()
        # Raw document text of the current parse (sentinel_inject="full"
        # injects it verbatim).
        self._raw_text: str = ""
        self._source_sig: Optional[str] = None  # fingerprint of current parse
        self._url_fetched_at: float = 0.0
        self._last_failure_at: float = 0.0  # negative cache for URL fetches
        # (path, mtime) of the file parse currently cached; used to refuse
        # swapping in a parse of an OLDER file version after a read race.
        self._file_state: Tuple[str, float] = ("", -1.0)

        # Compile keyword regexes once, per tier. KEYWORD_MAP keys are
        # normalized with the same helper used for document headings, so
        # they cannot drift.
        self._keyword_patterns: Dict[str, Dict[str, Any]] = {
            _normalize_title(title): {
                "specific": [_compile_keyword(k) for k in tiers.get("specific", [])],
                "vocab": [_compile_keyword(k) for k in tiers.get("vocab", [])],
                "generic": [_compile_keyword(k) for k in tiers.get("generic", [])],
            }
            for title, tiers in KEYWORD_MAP.items()
        }
        # Keep a normalized-title -> map-title lookup for debug messages.
        self._map_titles: Dict[str, str] = {
            _normalize_title(t): t for t in KEYWORD_MAP
        }
        self._generic_patterns: List["re.Pattern[str]"] = [
            _compile_keyword(k) for k in GENERIC_SN_SIGNALS
        ]

        # Witness-counting structures (see _vocab_witnesses): one compiled
        # pattern per DISTINCT vocab keyword across all sections (a keyword
        # like "acl" appears under several sections; scanning it once is
        # enough for arming purposes).
        witness_seen: Dict[str, "re.Pattern[str]"] = {}
        for tiers in KEYWORD_MAP.values():
            for k in tiers.get("vocab", []):
                cf = k.casefold().strip()
                if cf not in witness_seen:
                    witness_seen[cf] = _compile_keyword(k)
        self._witness_patterns: List[Tuple[str, "re.Pattern[str]"]] = list(
            witness_seen.items()
        )
        # casefolded vocab keyword -> concept-group id. Listed groups get a
        # positional id; any unlisted keyword is its own implicit group
        # (id = the keyword itself).
        self._group_of: Dict[str, str] = {}
        for i, group in enumerate(VOCAB_GROUPS):
            for k in group:
                self._group_of[k.casefold().strip()] = f"group:{i}"
        # Group ids that contain at least one STRONG keyword.
        self._strong_groups: set = {
            self._group_of.get(cf, cf) for cf in STRONG_VOCAB
        }
        self._veto_patterns: List["re.Pattern[str]"] = [
            _compile_keyword(k) for k in PLATFORM_VETO
        ]
        # NEGATIVE_VOCAB: compiled like vocab keywords; they join the span
        # merge, and a merged occurrence whose longest constituent is
        # negative is discarded (no witness, no vocab section selection).
        self._negative_patterns: List[Tuple[str, "re.Pattern[str]"]] = [
            (k.casefold().strip(), _compile_keyword(k)) for k in NEGATIVE_VOCAB
        ]
        self._negative_keywords: frozenset = frozenset(
            k for k, _ in self._negative_patterns
        )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        if self.valves.debug:
            print(f"[glidegrail] {message}")

    # ------------------------------------------------------------------
    # Document loading / parsing
    # ------------------------------------------------------------------

    def _fetch_url(self, url: str) -> str:
        """Fetch the document over HTTP. `requests` is imported lazily here
        (and only here) so the module never requires it at import time."""
        import requests  # lazy import by design — do not move to module top

        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "glidegrail-openwebui-filter/1.0.0"},
        )
        response.raise_for_status()
        return response.text

    @staticmethod
    def _parse_sections(text: str) -> "OrderedDict[str, Tuple[str, str]]":
        """Split the document into ordered h2 sections.

        A section starts at a line beginning with "## " and runs until the
        next such line. "### " subheadings stay inside their parent section.
        Lines inside fenced code blocks (```) are never treated as headings,
        so example code containing "## " cannot split a section. The
        "Table of Contents" section is skipped. Keys are normalized titles;
        values are (original_title, full_text_including_heading).
        """
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

    def _ensure_document(self) -> "OrderedDict[str, Tuple[str, str]]":
        """Return parsed sections, (re)loading the document as needed.

        Preference order: local file (re-read on mtime change), then URL
        (memory-cached with TTL; failures back off FETCH_RETRY_BACKOFF_S
        seconds before the next attempt). Any failure returns whatever cache
        exists, possibly empty — never raises.

        This method performs blocking file/network I/O, so callers on an
        event loop must run it in a worker thread (inlet uses
        asyncio.to_thread). The lock is only held for cache checks and
        swaps, NEVER across the I/O itself (double-checked locking).
        """
        # --- 1. Local file, if present ---------------------------------
        path = (self.valves.source_path or "").strip()
        if path and os.path.isfile(path):
            try:
                mtime = os.path.getmtime(path)
                sig = f"file:{path}:{mtime}"
                with self._lock:
                    # A matching signature means THIS file version is already
                    # parsed — treat it as fresh even if it yielded zero
                    # sections, so a heading-less file is not re-read and
                    # re-parsed on every message.
                    if sig == self._source_sig:
                        return self._sections
                # Read + parse outside the lock.
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                parsed = self._parse_sections(text)
                with self._lock:
                    cached_path, cached_mtime = self._file_state
                    # Swap only if (a) still stale and (b) not OLDER than the
                    # parse already cached for this same file — a slow reader
                    # racing a fast one must never clobber a newer parse.
                    if self._source_sig != sig and not (
                        cached_path == path and mtime < cached_mtime
                    ):
                        self._sections = parsed
                        self._raw_text = text
                        self._source_sig = sig
                        self._file_state = (path, mtime)
                        self._log(
                            f"loaded {len(parsed)} sections from file {path}"
                        )
                    return self._sections
            except OSError as exc:
                self._log(f"file read failed ({path}): {exc}")
                # fall through to URL

        # --- 2. URL with in-memory TTL cache + failure backoff ----------
        url = (self.valves.source_url or "").strip()
        if not url:
            with self._lock:
                return self._sections

        ttl_seconds = max(int(self.valves.cache_ttl_minutes), 1) * 60
        url_sig = f"url:{url}"
        now = time.time()
        with self._lock:
            # A matching signature within TTL is fresh even if the parse
            # yielded zero sections (same rationale as the file branch).
            cache_is_fresh = (
                self._source_sig == url_sig
                and (now - self._url_fetched_at) < ttl_seconds
            )
            if cache_is_fresh:
                return self._sections
            if (
                self._last_failure_at
                and (now - self._last_failure_at) < FETCH_RETRY_BACKOFF_S
            ):
                # Negative cache: a fetch failed recently; don't hammer the
                # network on every message during an outage.
                return self._sections

        # Fetch + parse outside the lock.
        try:
            text = self._fetch_url(url)
            parsed = self._parse_sections(text)
        except Exception as exc:
            # Keep any stale cache; a stale document beats no document.
            self._log(f"url fetch failed ({url}): {exc}")
            with self._lock:
                self._last_failure_at = time.time()
                return self._sections

        with self._lock:
            fetched_at = time.time()
            still_stale = not (
                self._source_sig == url_sig
                and (fetched_at - self._url_fetched_at) < ttl_seconds
            )
            if still_stale:
                self._sections = parsed
                self._raw_text = text
                self._source_sig = url_sig
                self._url_fetched_at = fetched_at
                # Forget the file fingerprint: if the file later reappears
                # (any mtime), it must be allowed to take over again.
                self._file_state = ("", -1.0)
                self._log(f"loaded {len(parsed)} sections from url {url}")
            self._last_failure_at = 0.0
            return self._sections

    # ------------------------------------------------------------------
    # Message text extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Get plain text from either str content or Open WebUI's
        list-of-parts content ([{ "type": "text", "text": ... }, ...])."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(str(part.get("text") or ""))
            return "\n".join(parts)
        return ""

    def _recent_user_text(self, messages: List[dict]) -> str:
        n = int(self.valves.scan_last_n_user_messages)
        if n <= 0:
            return ""
        user_texts = [
            self._extract_text(m.get("content"))
            for m in messages
            if isinstance(m, dict) and m.get("role") == "user"
        ]
        return "\n".join(t for t in user_texts[-n:] if t)

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def _merged_vocab_occurrences(
        self, prompt_text: str
    ) -> List[Tuple[int, int, str]]:
        """Collect every vocab AND NEGATIVE_VOCAB match as (start, end,
        keyword) spans via finditer, sort by position, and MERGE
        OVERLAPPING SPANS into one occurrence (so ONE phrase like "service
        catalog items" — where "service catalog" and "catalog items"
        overlap without either string containing the other — is ONE
        occurrence, while "service portal widget with a server script"
        cannot be diluted the other way by string subsumption). Each merged
        occurrence is labeled with its LONGEST constituent match. Returns
        [(merged_start, merged_end, longest_keyword)] in text order.
        """
        occurrences: List[Tuple[int, int, str]] = []
        for kw_cf, pattern in self._witness_patterns:
            for m in pattern.finditer(prompt_text):
                occurrences.append((m.start(), m.end(), kw_cf))
        for kw_cf, pattern in self._negative_patterns:
            for m in pattern.finditer(prompt_text):
                occurrences.append((m.start(), m.end(), kw_cf))
        if not occurrences:
            return []

        occurrences.sort(key=lambda o: (o[0], -(o[1] - o[0])))
        merged: List[Tuple[int, int, str]] = []

        cur_start = -1
        cur_end = -1
        best_len = -1
        best_kw = ""
        for start, end, kw in occurrences:
            if start < cur_end:  # overlaps the occurrence being built
                cur_end = max(cur_end, end)
                if end - start > best_len:
                    best_len, best_kw = end - start, kw
            else:
                if best_len >= 0:
                    merged.append((cur_start, cur_end, best_kw))
                cur_start, cur_end = start, end
                best_len, best_kw = end - start, kw
        merged.append((cur_start, cur_end, best_kw))
        return merged

    def _vocab_witnesses(self, prompt_text: str) -> Tuple[set, int]:
        """Span-based vocab witness counting.

        Maps each merged occurrence (_merged_vocab_occurrences) to a
        concept group (VOCAB_GROUPS; keyed by the occurrence's LONGEST
        constituent match). Occurrences dominated by a NEGATIVE_VOCAB
        entry are DISCARDED. Returns (set_of_witnessed_group_ids,
        count_of_strong_groups_witnessed).
        """
        groups: set = set()
        for _start, _end, kw in self._merged_vocab_occurrences(prompt_text):
            if kw in self._negative_keywords:
                continue  # negative-dominated occurrence: no witness
            groups.add(self._group_of.get(kw, kw))
        strong_count = sum(1 for g in groups if g in self._strong_groups)
        return groups, strong_count

    def _negative_spans(self, prompt_text: str) -> List[Tuple[int, int]]:
        """Merged-occurrence spans dominated by a NEGATIVE_VOCAB entry.
        Vocab-tier section selection ignores matches inside these spans.
        Cheap pre-check: the full merge scan only runs when a negative
        pattern matches at all (almost never on ordinary prompts)."""
        if not any(
            p.search(prompt_text) for _kw, p in self._negative_patterns
        ):
            return []
        return [
            (start, end)
            for start, end, kw in self._merged_vocab_occurrences(prompt_text)
            if kw in self._negative_keywords
        ]

    def _keyword_matches(
        self,
        prompt_text: str,
        sections: "OrderedDict[str, Tuple[str, str]]",
        looks_sn: bool,
    ) -> List[str]:
        """Return normalized titles of sections whose keywords hit.

        Three-tier logic (looks_sn is _looks_like_servicenow computed ONCE
        by the caller):
          - specific: selects its section outright and establishes
            ServiceNow context.
          - vocab: hits select their sections only once context is armed.
            Vocab-only arming uses span-merged concept-group witnesses
            (_vocab_witnesses): at vocab_arm_threshold >= 2, that many
            distinct groups with at least one STRONG group; at threshold
            1, any single witness. A PLATFORM_VETO token (Salesforce,
            Power Automate, ...) suppresses vocab-only arming — but NOT
            arming via a specific hit or a ServiceNow signal, NOT when two
            or more witnessed groups are STRONG (two independent strong
            ServiceNow concepts outweigh a product mention), and once
            armed all vocab hits fire normally. Vocab matches lying inside
            a NEGATIVE_VOCAB-dominated span select nothing.
          - generic: selects its section only when ServiceNow context is
            armed; never arms context itself.

        A specific or vocab hit whose section title is missing from the
        parsed document still ARMS context (only the section selection is
        skipped), so a trimmed document cannot silently disable arming.
        """
        specific_hits: List[str] = []
        vocab_hits: List[str] = []
        generic_hits: List[str] = []
        any_specific = False

        neg_spans = self._negative_spans(prompt_text)

        def vocab_tier_hit(patterns: List[Any]) -> bool:
            if not neg_spans:  # fast path: identical to plain search
                return any(p.search(prompt_text) for p in patterns)
            for p in patterns:
                for m in p.finditer(prompt_text):
                    if not any(
                        s <= m.start() and m.end() <= e
                        for s, e in neg_spans
                    ):
                        return True
            return False

        for norm_title, tiers in self._keyword_patterns.items():
            in_doc = norm_title in sections
            if any(p.search(prompt_text) for p in tiers["specific"]):
                any_specific = True
                if in_doc:
                    specific_hits.append(norm_title)
                continue
            if vocab_tier_hit(tiers["vocab"]):
                if in_doc:
                    vocab_hits.append(norm_title)
                continue
            if in_doc and any(p.search(prompt_text) for p in tiers["generic"]):
                generic_hits.append(norm_title)

        threshold = max(int(self.valves.vocab_arm_threshold), 1)
        witness_groups: set = set()
        strong_count = 0
        vocab_armed = False
        if not (any_specific or looks_sn):
            # Witness counting only decides arming, so skip the scan when
            # context is already established some other way.
            witness_groups, strong_count = self._vocab_witnesses(prompt_text)
            if threshold <= 1:
                vocab_armed = bool(witness_groups)
            else:
                vocab_armed = (
                    len(witness_groups) >= threshold and strong_count >= 1
                )
            if (
                vocab_armed
                and strong_count < 2  # 2+ strong groups override the veto
                and any(p.search(prompt_text) for p in self._veto_patterns)
            ):
                self._log(
                    "vocab arming vetoed by competitor-platform token"
                )
                vocab_armed = False

        sn_context = any_specific or vocab_armed or looks_sn
        if sn_context:
            return specific_hits + vocab_hits + generic_hits

        if vocab_hits or generic_hits:
            self._log(
                "vocab/generic keyword hits discarded (no ServiceNow "
                f"context; {len(witness_groups)} witness group(s), "
                f"strong={strong_count}, threshold={threshold}): "
                + ", ".join(vocab_hits + generic_hits)
            )
        return specific_hits

    def _looks_like_servicenow(self, prompt_text: str) -> bool:
        """True when ServiceNow context is externally established: either
        the assume_servicenow_context valve (dedicated SN deployments) or a
        GENERIC_SN_SIGNALS match. Also gates the search fallback."""
        if bool(self.valves.assume_servicenow_context):
            return True
        return any(p.search(prompt_text) for p in self._generic_patterns)

    def _search_sections(
        self,
        prompt_text: str,
        sections: "OrderedDict[str, Tuple[str, str]]",
    ) -> List[str]:
        """Token-overlap fallback: score each section by occurrences of
        prompt tokens (title hits weighted 5x); return top_k >= min score."""
        tokens = {
            t
            for t in _TOKEN_RE.findall(prompt_text.casefold())
            if t not in _STOPWORDS
        }
        if not tokens:
            return []

        token_patterns = [
            re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)") for t in tokens
        ]

        scored: List[Tuple[int, str]] = []
        for norm_title, (title, text) in sections.items():
            title_lower = title.casefold()
            # Body excludes the heading line so title hits are not counted twice.
            body_lower = text.split("\n", 1)[1].casefold() if "\n" in text else ""
            score = 0
            for pattern in token_patterns:
                score += 5 * len(pattern.findall(title_lower))
                score += len(pattern.findall(body_lower))
            if score >= int(self.valves.min_search_score):
                scored.append((score, norm_title))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_k = max(int(self.valves.search_top_k), 0)
        picked = [norm_title for _, norm_title in scored[:top_k]]
        if picked:
            self._log(
                "search fallback picked: "
                + ", ".join(f"{t} ({s})" for s, t in scored[:top_k])
            )
        return picked

    def _always_include_titles(
        self, sections: "OrderedDict[str, Tuple[str, str]]"
    ) -> List[str]:
        titles: List[str] = []
        for raw in (self.valves.always_include or "").split(","):
            norm = _normalize_title(raw)
            if norm and norm in sections and norm not in titles:
                titles.append(norm)
        return titles

    # ------------------------------------------------------------------
    # Injection assembly
    # ------------------------------------------------------------------

    @staticmethod
    def _render_block(section_texts: List[str]) -> str:
        body = "\n\n".join(section_texts)
        return f"{MARKER_START}\n{INJECTION_HEADER}\n\n{body}\n{MARKER_END}"

    def _build_injection(
        self,
        sections: "OrderedDict[str, Tuple[str, str]]",
        always_norm: List[str],
        keyword_norm: List[str],
        search_norm: List[str],
    ) -> Tuple[str, List[str]]:
        """Assemble the marker-wrapped injection block within char_budget.

        Ordering: always_include sections first, then the other selected
        sections — each group in document order, deduplicated.
        Drop priority when over budget: search results first, then keyword
        matches, then always_include. A lone over-budget section is truncated.
        If even a truncated block cannot fit (char_budget smaller than the
        fixed markers+header overhead), returns ("", []) — the caller skips
        injection rather than emitting header-only noise over budget.
        Returns (block_text, list_of_original_titles_injected).
        """
        doc_order = {norm: i for i, norm in enumerate(sections.keys())}

        # priority: 0 = always_include (keep longest), 1 = keyword, 2 = search
        chosen: "OrderedDict[str, int]" = OrderedDict()
        for norm in sorted(always_norm, key=lambda n: doc_order[n]):
            chosen[norm] = 0
        for norm in sorted(keyword_norm, key=lambda n: doc_order[n]):
            chosen.setdefault(norm, 1)
        for norm in sorted(search_norm, key=lambda n: doc_order[n]):
            chosen.setdefault(norm, 2)

        # entries: (priority, original_title, section_text)
        entries: List[Tuple[int, str, str]] = [
            (prio, sections[norm][0], sections[norm][1])
            for norm, prio in chosen.items()
        ]

        budget = max(int(self.valves.char_budget), 0)
        rendered = self._render_block([e[2] for e in entries])

        # Drop lowest-priority sections (ties: the later entry) until we fit.
        while len(rendered) > budget and len(entries) > 1:
            drop_index = max(
                range(len(entries)), key=lambda i: (entries[i][0], i)
            )
            dropped = entries.pop(drop_index)
            self._log(f"char_budget: dropped section '{dropped[1]}'")
            rendered = self._render_block([e[2] for e in entries])

        # A single remaining section that still exceeds the budget: truncate.
        if len(rendered) > budget and entries:
            prio, title, text = entries[0]
            note = "\n\n[GlideGrail: section truncated to fit char_budget]"
            overhead = len(self._render_block([""])) + len(note)
            allowed = max(budget - overhead, 0)
            entries[0] = (prio, title, text[:allowed].rstrip() + note)
            self._log(f"char_budget: truncated section '{title}'")
            rendered = self._render_block([e[2] for e in entries])

        # Still over budget: char_budget is smaller than the fixed overhead
        # of the markers + header. Never inject header-only noise over budget.
        if len(rendered) > budget:
            self._log(
                "char_budget too small for any injection; skipping entirely"
            )
            return "", []

        return rendered, [e[1] for e in entries]

    # ------------------------------------------------------------------
    # System-message manipulation
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_marker_text(text: str) -> str:
        """Remove complete marker blocks; if an orphaned MARKER_START remains
        (MARKER_END lost to context trimming), strip from it to the end."""
        cleaned = _MARKER_BLOCK_RE.sub("", text)
        orphan = cleaned.find(MARKER_START)
        if orphan != -1:
            cleaned = cleaned[:orphan]
        return cleaned

    @classmethod
    def _strip_previous_block(cls, content: Any) -> Any:
        """Remove any previously injected marker block (multi-turn: we
        replace our block, never stack a second copy)."""
        if isinstance(content, str):
            return cls._strip_marker_text(content).rstrip()
        if isinstance(content, list):
            cleaned: List[Any] = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    new_text = cls._strip_marker_text(
                        str(part.get("text") or "")
                    ).rstrip()
                    if new_text:
                        part = dict(part)
                        part["text"] = new_text
                        cleaned.append(part)
                    # drop text parts that were only our block
                else:
                    cleaned.append(part)
            return cleaned
        return content

    @staticmethod
    def _is_empty_content(content: Any) -> bool:
        if content is None:
            return True
        if isinstance(content, str):
            return not content.strip()
        if isinstance(content, list):
            return len(content) == 0
        return False

    # ------------------------------------------------------------------
    # Sentinel contract (deterministic trigger for pipelines/bridges)
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_sentinel_text(text: str, token: str) -> str:
        """Remove every occurrence of the sentinel token from text. A line
        left empty (whitespace-only) purely by the removal is collapsed
        away entirely, so a first-line sentinel leaves no blank line."""
        if token not in text:
            return text
        out_lines: List[str] = []
        for line in text.split("\n"):
            if token in line:
                cleaned = line.replace(token, "")
                if not cleaned.strip():
                    continue  # line existed only for the token: collapse
                line = cleaned
            out_lines.append(line)
        return "\n".join(out_lines)

    def _strip_sentinel(self, messages: List[dict], token: str) -> bool:
        """Detect and strip the sentinel token from EVERY message — any
        role (system, user, assistant), both str and list-of-parts
        content. The scan is cheap by design: a plain substring test per
        message text before any other work. A message (or text part) that
        becomes empty solely from stripping is removed, same hygiene as
        marker stripping. Returns True when the token was found anywhere.
        """
        found = False
        kept: List[Any] = []
        for m in messages:
            if not isinstance(m, dict):
                kept.append(m)
                continue
            content = m.get("content")
            if isinstance(content, str):
                if token in content:  # cheap substring gate
                    found = True
                    was_empty = not content.strip()
                    new_text = self._strip_sentinel_text(content, token)
                    m["content"] = new_text
                    if not was_empty and not new_text.strip():
                        continue  # emptied solely by the strip: drop it
            elif isinstance(content, list):
                has_token = any(
                    isinstance(p, dict)
                    and p.get("type") == "text"
                    and token in str(p.get("text") or "")
                    for p in content
                )
                if has_token:
                    found = True
                    was_empty = self._is_empty_content(content)
                    new_parts: List[Any] = []
                    for p in content:
                        if isinstance(p, dict) and p.get("type") == "text":
                            t = str(p.get("text") or "")
                            if token in t:
                                t = self._strip_sentinel_text(t, token)
                                if not t.strip():
                                    continue  # part was only the token
                                p = dict(p)
                                p["text"] = t
                        new_parts.append(p)
                    m["content"] = new_parts
                    if not was_empty and self._is_empty_content(new_parts):
                        continue  # emptied solely by the strip: drop it
            kept.append(m)
        if found and len(kept) != len(messages):
            messages[:] = kept
        return found

    def _inject_block(self, messages: List[dict], block: str) -> None:
        # Strip any earlier injection from every system message. If a system
        # message becomes empty BECAUSE of the strip (it contained only our
        # marker block), remove the message entirely — some upstream
        # providers reject empty content parts with a 400. Messages that
        # were already empty before the strip are left untouched.
        kept: List[dict] = []
        for m in messages:
            if isinstance(m, dict) and m.get("role") == "system":
                before = m.get("content")
                was_empty = self._is_empty_content(before)
                m["content"] = self._strip_previous_block(before)
                if not was_empty and self._is_empty_content(m["content"]):
                    continue  # emptied by our strip -> drop it
            kept.append(m)
        if len(kept) != len(messages):
            messages[:] = kept

        system_indices = [
            i
            for i, m in enumerate(messages)
            if isinstance(m, dict) and m.get("role") == "system"
        ]

        if system_indices:
            index = system_indices[0]
            content = messages[index].get("content")
            if isinstance(content, str):
                messages[index]["content"] = (
                    f"{content.rstrip()}\n\n{block}" if content.strip() else block
                )
                return
            if isinstance(content, list):
                content.append({"type": "text", "text": block})
                messages[index]["content"] = content
                return
            # Unknown content shape: never overwrite it — fall through and
            # insert our own system message at the top instead.
        messages.insert(0, {"role": "system", "content": block})

    # ------------------------------------------------------------------
    # Status events
    # ------------------------------------------------------------------

    async def _emit_status(
        self, emitter: Optional[Callable[..., Any]], description: str
    ) -> None:
        """Emit a status event; supports both async and sync emitters.
        Never lets an emitter error escape."""
        if emitter is None:
            return
        try:
            result = emitter(
                {
                    "type": "status",
                    "data": {"description": description, "done": True},
                }
            )
            if inspect.isawaitable(result):
                await result
        except Exception as exc:
            self._log(f"status emit failed: {exc}")

    # ------------------------------------------------------------------
    # Open WebUI entry point
    # ------------------------------------------------------------------

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Optional[Callable[..., Any]] = None,
        __user__: Optional[dict] = None,
    ) -> dict:
        """Inspect the conversation and inject relevant GlideGrail sections
        into the system prompt. On ANY failure, return the body unmodified —
        this filter must never break a chat."""
        try:
            messages = body.get("messages") if isinstance(body, dict) else None
            if not isinstance(messages, list) or not messages:
                return body

            # 0. Sentinel contract — checked FIRST, on ALL messages
            #    (system/user/assistant; the keyword scanner only ever
            #    reads user messages, but bridges put the token in the
            #    SYSTEM message). The token is stripped immediately so it
            #    can never reach the downstream model, even via the
            #    early-return paths below.
            sentinel_fired = False
            token = (self.valves.sentinel_token or "").strip()
            if token:
                sentinel_fired = self._strip_sentinel(messages, token)
                if sentinel_fired:
                    body["messages"] = messages
                    self._log("sentinel token detected and stripped")

            prompt_text = self._recent_user_text(messages)
            if not prompt_text.strip() and not sentinel_fired:
                return body

            # Blocking file/network I/O — keep it off the event loop.
            sections = await asyncio.to_thread(self._ensure_document)
            if not sections:
                # Document unavailable (and no cache): do nothing.
                return body

            # Compute the ServiceNow-signal sweep ONCE per inlet; both the
            # keyword tiers and the search-fallback gate consume it. A
            # sentinel arms context unconditionally (like
            # assume_servicenow_context, search-fallback gate included).
            looks_sn = sentinel_fired or self._looks_like_servicenow(
                prompt_text
            )

            # 1. Keyword matching (three-tier; see _keyword_matches)
            keyword_norm: List[str] = []
            if prompt_text.strip():
                keyword_norm = self._keyword_matches(
                    prompt_text, sections, looks_sn
                )

            # 2. Search fallback, gated on generic ServiceNow signals.
            #    Keyword hits on always_include sections alone must NOT
            #    suppress the fallback — only topical section hits do.
            always_norm = self._always_include_titles(sections)
            topical_norm = [n for n in keyword_norm if n not in always_norm]
            search_norm: List[str] = []
            if (
                not topical_norm
                and self.valves.search_fallback
                and looks_sn
            ):
                search_norm = self._search_sections(prompt_text, sections)

            # Sentinel "full" mode: the ENTIRE document verbatim between
            # the markers, IGNORING char_budget (big-context cloud models
            # only — see README).
            if (
                sentinel_fired
                and (self.valves.sentinel_inject or "").strip().lower()
                == "full"
            ):
                with self._lock:
                    doc_text = self._raw_text
                if not doc_text:
                    doc_text = "\n\n".join(
                        text for _title, text in sections.values()
                    )
                self._inject_block(messages, self._render_block([doc_text]))
                body["messages"] = messages
                self._log("sentinel trigger: injected full document")
                if self.valves.show_status:
                    await self._emit_status(
                        __event_emitter__,
                        "GlideGrail: sentinel trigger — injected full document",
                    )
                return body

            if not keyword_norm and not search_norm and not sentinel_fired:
                # Nothing fired this turn. Leave the body alone (including
                # any block injected on a previous turn).
                return body
            # A sentinel with no topical hits still injects the
            # always_include sections — the trigger is a guarantee.

            block, injected_titles = self._build_injection(
                sections, always_norm, keyword_norm, search_norm
            )
            if not block or not injected_titles:
                return body

            self._inject_block(messages, block)
            body["messages"] = messages

            if sentinel_fired:
                self._log(
                    "sentinel trigger: injected "
                    f"{len(injected_titles)} section(s)"
                )
            self._log(
                f"injected {len(injected_titles)} section(s): "
                + ", ".join(injected_titles)
            )
            if self.valves.show_status:
                description = (
                    f"GlideGrail: injected {len(injected_titles)} section(s): "
                    + ", ".join(injected_titles)
                )
                if len(description) > 240:
                    description = description[:237] + "..."
                await self._emit_status(__event_emitter__, description)

            return body
        except Exception as exc:
            # Absolute safety net: never break the chat.
            self._log(f"inlet error (returning body unmodified): {exc}")
            return body
