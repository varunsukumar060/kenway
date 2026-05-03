#!/usr/bin/env python3
"""
skills/folder_skill.py — KENWAY Folder Navigation Skill
Opens folders in Thunar using the folder map from config.yaml.
Also supports opening specific paths.
"""

import subprocess
import logging
import os
import yaml

log = logging.getLogger("kenway.folder_skill")


def _cfg():
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def open_folder(name: str) -> str:
    cfg     = _cfg()["folders"]
    name_l  = name.strip().lower() if name else "home"

    # Resolve alias
    folder_path = cfg.get(name_l)

    # If not found in map, try treating it as a literal path
    if not folder_path:
        expanded = os.path.expanduser(name)
        if os.path.isdir(expanded):
            folder_path = expanded

    if not folder_path or not os.path.isdir(folder_path):
        log.warning(f"Folder not found: {name}")
        return f"I couldn't find the {name} folder."

    try:
        subprocess.Popen(
            ["thunar", folder_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        log.info(f"Opened folder: {folder_path}")
        return f"Opening your {name_l} folder."
    except Exception as e:
        log.error(f"Folder open error: {e}")
        return f"Failed to open {name} folder."


def list_folder_contents(name: str) -> str:
    """Speak a short summary of what's in a folder."""
    cfg    = _cfg()["folders"]
    name_l = name.strip().lower() if name else "home"
    folder_path = cfg.get(name_l, os.path.expanduser("~"))

    try:
        items = os.listdir(folder_path)
        count = len(items)
        # Speak first 5 items
        sample = ", ".join(items[:5])
        suffix = f" and {count - 5} more" if count > 5 else ""
        return f"Your {name_l} folder has {count} items: {sample}{suffix}."
    except Exception as e:
        return f"Couldn't read {name} folder: {e}"
