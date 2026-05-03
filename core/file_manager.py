#!/usr/bin/env python3
"""
core/file_manager.py — KENWAY Sandboxed File Manager
Only reads/writes within paths defined in config.yaml.
"""

import os
import logging
import yaml
from core.voice import speak

log = logging.getLogger("kenway.file_manager")


def _load_allowed_paths() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("file_manager", {})
    except Exception:
        return {"allowed_read_paths": [], "allowed_write_paths": []}


def _is_allowed(path: str, allowed_list: list) -> bool:
    abs_path = os.path.abspath(os.path.expanduser(path))
    for allowed in allowed_list:
        if abs_path.startswith(os.path.abspath(os.path.expanduser(allowed))):
            return True
    return False


def read_file(path: str) -> str:
    cfg = _load_allowed_paths()
    if not _is_allowed(path, cfg.get("allowed_read_paths", [])):
        speak("That path is not in my allowed read list.")
        log.warning(f"Read denied: {path}")
        return ""
    try:
        with open(os.path.expanduser(path), "r") as f:
            content = f.read()
        log.info(f"Read file: {path}")
        return content
    except FileNotFoundError:
        speak("File not found.")
        return ""
    except Exception as e:
        log.error(f"File read error: {e}")
        return ""


def write_file(path: str, content: str, mode: str = "w"):
    cfg = _load_allowed_paths()
    if not _is_allowed(path, cfg.get("allowed_write_paths", [])):
        speak("That path is not in my allowed write list.")
        log.warning(f"Write denied: {path}")
        return
    try:
        os.makedirs(os.path.dirname(os.path.expanduser(path)), exist_ok=True)
        with open(os.path.expanduser(path), mode) as f:
            f.write(content)
        speak(f"Written to {os.path.basename(path)} successfully.")
        log.info(f"Wrote file: {path}")
    except Exception as e:
        speak("Failed to write file.")
        log.error(f"File write error: {e}")
