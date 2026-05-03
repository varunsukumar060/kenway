#!/usr/bin/env python3
"""
core/intent_parser.py — KENWAY Direct Mode Rule Engine
Phase 2 content: regex-based intent matching (no LLM).
Included in Phase 1 as a stub for routing architecture.
"""

import re
import logging

log = logging.getLogger("kenway.intent_parser")

# ── Intent rules ───────────────────────────────────────────────────────────────
# Format: (regex_pattern, action_tag, data_extractor_fn | None)
# Patterns are matched in order — put more specific patterns first.

INTENT_RULES = [
    # Browser / media
    (r"play (.+) on youtube",          "YOUTUBE_PLAY",   lambda m: m.group(1).strip()),
    (r"search (.+) on youtube",        "YOUTUBE_SEARCH", lambda m: m.group(1).strip()),
    (r"search (.+) on google",         "GOOGLE_SEARCH",  lambda m: m.group(1).strip()),
    (r"open (.+\.com|.+\.org|.+\.in)", "OPEN_URL",       lambda m: m.group(1).strip()),
    (r"play (.+) on spotify",          "SPOTIFY_PLAY",   lambda m: m.group(1).strip()),

    # App control
    (r"open (.+)",                     "OPEN_APP",       lambda m: m.group(1).strip()),
    (r"close (.+)",                    "CLOSE_APP",      lambda m: m.group(1).strip()),
    (r"launch (.+)",                   "OPEN_APP",       lambda m: m.group(1).strip()),

    # System
    (r"volume (up|down|\d+)",          "VOLUME_SET",     lambda m: m.group(1).strip()),
    (r"(battery|battery status)",       "BATTERY_STATUS", None),
    (r"(shutdown|shut down|turn off)",  "SHUTDOWN",       None),
    (r"(restart|reboot)",              "REBOOT",         None),
    (r"(sleep|suspend)",               "SLEEP",          None),
    (r"brightness (up|down|\d+)",      "BRIGHTNESS_SET", lambda m: m.group(1).strip()),

    # Screen & files
    (r"read (my )?screen",             "READ_SCREEN",    None),
    (r"read (file|document) (.+)",     "FILE_READ",      lambda m: m.group(2).strip()),
    (r"write (.+) to (.+)",            "FILE_WRITE",     lambda m: {"content": m.group(1), "path": m.group(2)}),
    (r"open file (.+)",                "FILE_OPEN",      lambda m: m.group(1).strip()),

    # Window management
    (r"(minimize|hide) (.+)",          "WINDOW_MINIMIZE",lambda m: m.group(2).strip()),
    (r"(maximize|fullscreen) (.+)",    "WINDOW_MAXIMIZE",lambda m: m.group(2).strip()),
    (r"focus (.+)",                    "WINDOW_FOCUS",   lambda m: m.group(1).strip()),
]


def parse(command: str) -> dict:
    """
    Match a command string against intent rules.
    Returns dict: {action, data, mode}
    """
    cmd = command.strip().lower()

    for pattern, action, extractor in INTENT_RULES:
        match = re.search(pattern, cmd)
        if match:
            data = extractor(match) if extractor else None
            log.info(f"Matched intent: {action} | data={data}")
            return {"action": action, "data": data, "mode": "direct"}

    log.info(f"No intent matched for: '{cmd}'")
    return {"action": "UNKNOWN", "data": cmd, "mode": "direct"}
