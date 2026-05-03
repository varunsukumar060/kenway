#!/usr/bin/env python3
"""
core/intent_parser.py — KENWAY Direct Mode Rule Engine
Pure regex/keyword matching. Zero LLM. Fast and deterministic.
"""

import re
import logging

log = logging.getLogger("kenway.intent_parser")

# ── Intent Rules ───────────────────────────────────────────────────────────────
# Format: (regex_pattern, action_tag, extractor_lambda)
# Patterns are tried in order — more specific first.
INTENT_RULES = [
    # ── Browser ─────────────────────────────────────────────────────────────
    (r"play (.+?) on youtube",           "YOUTUBE_PLAY",   lambda m: m.group(1).strip()),
    (r"youtube (.+)",                    "YOUTUBE_PLAY",   lambda m: m.group(1).strip()),
    (r"search (.+?) on google",          "GOOGLE_SEARCH",  lambda m: m.group(1).strip()),
    (r"google (.+)",                     "GOOGLE_SEARCH",  lambda m: m.group(1).strip()),
    (r"search for (.+)",                 "GOOGLE_SEARCH",  lambda m: m.group(1).strip()),
    (r"open (https?://\S+)",             "OPEN_URL",       lambda m: m.group(1).strip()),
    (r"go to (https?://\S+)",            "OPEN_URL",       lambda m: m.group(1).strip()),
    (r"open (\S+\.com\S*)",              "OPEN_URL",       lambda m: m.group(1).strip()),

    # ── System ──────────────────────────────────────────────────────────────
    (r"volume (up|down|\d+)",            "VOLUME_SET",     lambda m: m.group(1).strip()),
    (r"(increase|raise) volume",         "VOLUME_SET",     lambda m: "up"),
    (r"(decrease|lower|reduce) volume",  "VOLUME_SET",     lambda m: "down"),
    (r"mute",                            "VOLUME_SET",     lambda m: "mute"),
    (r"unmute",                          "VOLUME_SET",     lambda m: "unmute"),
    (r"brightness (up|down|\d+)",        "BRIGHTNESS_SET", lambda m: m.group(1).strip()),
    (r"battery( status)?",               "BATTERY_STATUS", None),
    (r"shut ?down",                      "SHUTDOWN",       None),
    (r"reboot|restart",                  "REBOOT",         None),

    # ── Apps ───────────────────────────────────────────────────────────────
    # IMPORTANT: "open <app>" must come AFTER "open <url>" rules above
    (r"open (.+)",                       "OPEN_APP",       lambda m: m.group(1).strip()),
    (r"launch (.+)",                     "OPEN_APP",       lambda m: m.group(1).strip()),
    (r"start (.+)",                      "OPEN_APP",       lambda m: m.group(1).strip()),
    (r"close (.+)",                      "CLOSE_APP",      lambda m: m.group(1).strip()),
    (r"kill (.+)",                       "CLOSE_APP",      lambda m: m.group(1).strip()),

    # ── Files ───────────────────────────────────────────────────────────────
    (r"read (?:file )?(.+)",             "FILE_READ",      lambda m: m.group(1).strip()),
    (r"(?:write|save) (.+?) to (.+)",    "FILE_WRITE",     lambda m: (m.group(1).strip(), m.group(2).strip())),
    (r"list files(?: in (.+))?",         "FILE_LIST",      lambda m: m.group(1).strip() if m.group(1) else None),
    (r"read (?:my )?screen",             "READ_SCREEN",    None),
]


def parse(command: str) -> dict:
    """Match command against intent rules. Returns dict with action, data, mode."""
    cmd = command.strip().lower()

    for pattern, action, extractor in INTENT_RULES:
        match = re.search(pattern, cmd)
        if match:
            data = extractor(match) if extractor else None
            log.info(f"Matched intent: {action} | data={data}")
            return {"action": action, "data": data, "mode": "direct"}

    log.info(f"No match found for: {cmd}")
    return {"action": "UNKNOWN", "data": cmd, "mode": "direct"}
