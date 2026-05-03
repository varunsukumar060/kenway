#!/usr/bin/env python3
"""
skills/app_skill.py — KENWAY App Launcher Skill
Launches and closes apps using the alias map from config.yaml.
"""

import subprocess
import logging
import os
import yaml

log = logging.getLogger("kenway.app_skill")


def _cfg():
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _resolve(name: str) -> str:
    """Resolve friendly name to binary using alias map, then allowlist."""
    cfg     = _cfg()["apps"]
    aliases = cfg.get("aliases", {})
    name_l  = name.strip().lower()

    # 1. Check alias map first
    if name_l in aliases:
        return aliases[name_l]

    # 2. Check if it's directly in allowlist
    for entry in cfg.get("allowlist", []):
        if name_l == entry.lower() or name_l in entry.lower():
            return entry

    # 3. Return as-is and let subprocess try it
    return name_l


def launch_app(name: str) -> str:
    binary = _resolve(name)
    log.info(f"Launching: {binary} (requested: {name})")
    try:
        subprocess.Popen(
            [binary],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        # Use friendly name in speech
        display = name if name else binary
        return f"Opening {display}."
    except FileNotFoundError:
        log.warning(f"Binary not found: {binary}")
        return f"I couldn't find {name} on your system."
    except Exception as e:
        log.error(f"Launch error: {e}")
        return f"Failed to open {name}."


def close_app(name: str) -> str:
    binary = _resolve(name)
    log.info(f"Closing: {binary} (requested: {name})")
    try:
        result = subprocess.run(
            ["pkill", "-f", binary],
            capture_output=True
        )
        if result.returncode == 0:
            return f"Closed {name}."
        else:
            return f"{name} doesn't appear to be running."
    except Exception as e:
        log.error(f"Close error: {e}")
        return f"Failed to close {name}."
