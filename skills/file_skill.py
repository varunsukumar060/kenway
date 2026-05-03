#!/usr/bin/env python3
"""
skills/file_skill.py — File Open Skill
Opens files using xdg-open (system default app).
"""

import subprocess
import os
import logging
from core.voice import speak

log = logging.getLogger("kenway.file_skill")


def open_file(path: str):
    """Open a file using its default application."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        speak(f"File not found: {path}")
        log.warning(f"File not found: {expanded}")
        return
    try:
        subprocess.Popen(["xdg-open", expanded])
        speak(f"Opening {os.path.basename(path)}.")
        log.info(f"Opened file: {expanded}")
    except Exception as e:
        speak("Failed to open file.")
        log.error(f"File open error: {e}")
