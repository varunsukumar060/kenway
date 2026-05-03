#!/usr/bin/env python3
"""
core/intent_parser.py — KENWAY Direct Mode Rule Engine
Pure regex/keyword matching. Zero LLM.
"""

import re
import logging

log = logging.getLogger("kenway.intent_parser")

INTENT_RULES = [
    # ── Browser ─────────────────────────────────────────────────────────────
    (r"play (.+?) on youtube",            "YOUTUBE_PLAY",    lambda m: m.group(1).strip()),
    (r"youtube (.+)",                     "YOUTUBE_PLAY",    lambda m: m.group(1).strip()),
    (r"search (.+?) on google",           "GOOGLE_SEARCH",   lambda m: m.group(1).strip()),
    (r"google (.+)",                      "GOOGLE_SEARCH",   lambda m: m.group(1).strip()),
    (r"search for (.+)",                  "GOOGLE_SEARCH",   lambda m: m.group(1).strip()),
    (r"open (https?://\S+)",              "OPEN_URL",        lambda m: m.group(1).strip()),
    (r"go to (https?://\S+)",             "OPEN_URL",        lambda m: m.group(1).strip()),
    (r"open (\S+\.(?:com|org|net|io|dev|in)\S*)", "OPEN_URL", lambda m: m.group(1).strip()),

    # ── Brightness ───────────────────────────────────────────────────────────
    (r"brightness (up|down|\d+)",         "BRIGHTNESS_SET",  lambda m: m.group(1).strip()),
    (r"(increase|raise) brightness",      "BRIGHTNESS_SET",  lambda m: "up"),
    (r"(decrease|lower|dim) (?:the )?(?:screen|brightness)", "BRIGHTNESS_SET", lambda m: "down"),
    (r"dim(mer)?",                        "BRIGHTNESS_SET",  lambda m: "down"),
    (r"brighter",                         "BRIGHTNESS_SET",  lambda m: "up"),
    (r"(?:screen|brightness) status",     "BRIGHTNESS_GET",  None),

    # ── Volume ─────────────────────────────────────────────────────────────
    (r"volume (up|down|\d+)",             "VOLUME_SET",      lambda m: m.group(1).strip()),
    (r"(increase|raise|louder) (?:the )?volume", "VOLUME_SET", lambda m: "up"),
    (r"(decrease|lower|quieter|softer) (?:the )?volume", "VOLUME_SET", lambda m: "down"),
    (r"^mute$",                           "VOLUME_SET",      lambda m: "mute"),
    (r"^unmute$",                         "VOLUME_SET",      lambda m: "unmute"),
    (r"mute (?:the )?(?:sound|audio|volume)", "VOLUME_SET",  lambda m: "mute"),
    (r"unmute (?:the )?(?:sound|audio|volume)","VOLUME_SET", lambda m: "unmute"),

    # ── Battery & Power ───────────────────────────────────────────────
    (r"battery(?: status| level)?",       "BATTERY_STATUS",  None),
    (r"how(?:'s| is) (?:the )?battery",   "BATTERY_STATUS",  None),
    (r"shut ?down",                       "SHUTDOWN",        None),
    (r"power off",                        "SHUTDOWN",        None),
    (r"reboot|restart",                   "REBOOT",          None),

    # ── Folders ─────────────────────────────────────────────────────────────
    (r"open (?:my )?(?:the )?(desktop|documents|downloads|music|pictures|videos|kenway|arduino|home)(?: folder)?",
                                          "OPEN_FOLDER",     lambda m: m.group(1).strip()),
    (r"go to (?:my )?(?:the )?(desktop|documents|downloads|music|pictures|videos|kenway|arduino|home)(?: folder)?",
                                          "OPEN_FOLDER",     lambda m: m.group(1).strip()),
    (r"show (?:my )?(?:the )?(desktop|documents|downloads|music|pictures|videos|kenway|arduino|home)(?: folder)?",
                                          "OPEN_FOLDER",     lambda m: m.group(1).strip()),
    (r"what(?:'s| is) in (?:my )?(?:the )?(\w+)(?: folder)?",
                                          "LIST_FOLDER",     lambda m: m.group(1).strip()),

    # ── Files ──────────────────────────────────────────────────────────────
    (r"open (?:file )?(.+\.\w{2,5})",    "OPEN_FILE",       lambda m: m.group(1).strip()),
    (r"read (?:file )?(.+\.\w{2,5})",    "FILE_READ",       lambda m: m.group(1).strip()),
    (r"(?:write|save) (.+?) to (.+)",     "FILE_WRITE",      lambda m: (m.group(1).strip(), m.group(2).strip())),
    (r"list files(?: in (.+))?",          "FILE_LIST",       lambda m: m.group(1).strip() if m.group(1) else None),
    (r"read (?:my )?screen",              "READ_SCREEN",     None),

    # ── Apps (LAST — most generic, must be after folder/file/url rules) ─────────
    (r"open (.+)",                        "OPEN_APP",        lambda m: m.group(1).strip()),
    (r"launch (.+)",                      "OPEN_APP",        lambda m: m.group(1).strip()),
    (r"start (.+)",                       "OPEN_APP",        lambda m: m.group(1).strip()),
    (r"close (.+)",                       "CLOSE_APP",       lambda m: m.group(1).strip()),
    (r"kill (.+)",                        "CLOSE_APP",       lambda m: m.group(1).strip()),
    (r"quit (.+)",                        "CLOSE_APP",       lambda m: m.group(1).strip()),
]


def parse(command: str) -> dict:
    cmd = command.strip().lower()
    for pattern, action, extractor in INTENT_RULES:
        match = re.search(pattern, cmd)
        if match:
            data = extractor(match) if extractor else None
            log.info(f"Matched intent: {action} | data={data}")
            return {"action": action, "data": data, "mode": "direct"}
    log.info(f"No match: {cmd}")
    return {"action": "UNKNOWN", "data": cmd, "mode": "direct"}
