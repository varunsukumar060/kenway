#!/usr/bin/env python3
"""
skills/file_skill.py — KENWAY File Skill
Sandboxed read / write / list operations.
"""

import os
import logging
import yaml
import subprocess

log = logging.getLogger("kenway.file_skill")


def _cfg():
    path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _allowed(path: str, mode: str) -> bool:
    cfg   = _cfg()["file_manager"]
    paths = cfg.get(f"allowed_{mode}_paths", [])
    abs_p = os.path.abspath(os.path.expanduser(path))
    return any(abs_p.startswith(p) for p in paths)


def read_file(name: str) -> str:
    """Read first 300 chars of a file and speak them."""
    # Try Documents first
    search_dirs = [
        "/home/varun_sukumar/Documents",
        "/home/varun_sukumar/Desktop",
        "/home/varun_sukumar/Downloads",
    ]
    target = None

    if os.path.isabs(name) and os.path.isfile(name):
        target = name
    else:
        for d in search_dirs:
            candidate = os.path.join(d, name)
            if os.path.isfile(candidate):
                target = candidate
                break

    if not target:
        return f"I couldn't find a file named {name}."

    if not _allowed(target, "read"):
        return "That file is outside my allowed read paths."

    try:
        content = open(target, encoding="utf-8", errors="ignore").read(300)
        return f"Contents of {os.path.basename(target)}: {content}"
    except Exception as e:
        return f"Couldn't read file: {e}"


def write_file(content: str, name: str) -> str:
    """Write content to a file in Documents."""
    target = os.path.join("/home/varun_sukumar/Documents", name)
    if not _allowed(target, "write"):
        return "That path is outside my allowed write paths."
    try:
        with open(target, "w") as f:
            f.write(content)
        return f"Saved {name} to your Documents."
    except Exception as e:
        return f"Couldn't write file: {e}"


def list_files(folder: str = None) -> str:
    """List files in a folder."""
    target = folder or "/home/varun_sukumar/Documents"
    target = os.path.expanduser(target)
    if not os.path.isdir(target):
        return f"Folder not found: {target}"
    try:
        items = [f for f in os.listdir(target) if os.path.isfile(os.path.join(target, f))]
        if not items:
            return "That folder is empty."
        count = len(items)
        sample = ", ".join(items[:6])
        suffix = f" and {count-6} more" if count > 6 else ""
        return f"{count} files: {sample}{suffix}."
    except Exception as e:
        return f"Couldn't list files: {e}"


def open_file(name: str) -> str:
    """Open a file with its default application via xdg-open."""
    search_dirs = [
        "/home/varun_sukumar/Documents",
        "/home/varun_sukumar/Desktop",
        "/home/varun_sukumar/Downloads",
        "/home/varun_sukumar/Pictures",
        "/home/varun_sukumar/Music",
        "/home/varun_sukumar/Videos",
    ]
    target = None
    if os.path.isabs(name) and os.path.isfile(name):
        target = name
    else:
        for d in search_dirs:
            candidate = os.path.join(d, name)
            if os.path.isfile(candidate):
                target = candidate
                break

    if not target:
        return f"I couldn't find {name}."

    try:
        subprocess.Popen(["xdg-open", target],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        return f"Opening {os.path.basename(target)}."
    except Exception as e:
        return f"Couldn't open file: {e}"
