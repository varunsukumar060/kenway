#!/usr/bin/env python3
"""
skills/app_skill.py — App Launch and Close
"""

import subprocess
import logging
import yaml
import os
from core.voice import speak

log = logging.getLogger("kenway.app_skill")


def _get_allowlist() -> list:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f).get("apps", {}).get("allowlist", [])
    except Exception:
        return []


# Map of common spoken names → actual binary names
APP_ALIASES = {
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "cursor": "cursor",
    "terminal": "xfce4-terminal",
    "file manager": "thunar",
    "files": "thunar",
    "text editor": "mousepad",
    "notepad": "mousepad",
    "chrome": "google-chrome",
    "browser": "google-chrome",
    "vlc": "vlc",
    "music": "spotify",
    "virtualbox": "virtualbox",
    "arduino": "arduino-ide",
    "gimp": "gimp",
}


def launch_app(app_name: str):
    name = APP_ALIASES.get(app_name.lower(), app_name.lower())
    allowlist = _get_allowlist()

    if name not in allowlist:
        speak(f"{app_name} is not in my allowed applications list.")
        log.warning(f"Launch denied: {name}")
        return

    try:
        subprocess.Popen([name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        speak(f"Opening {app_name}.")
        log.info(f"Launched: {name}")
    except FileNotFoundError:
        speak(f"{app_name} is not installed or not found.")
        log.error(f"App not found: {name}")
    except Exception as e:
        speak(f"Failed to open {app_name}.")
        log.error(f"Launch error for {name}: {e}")


def close_app(app_name: str):
    name = APP_ALIASES.get(app_name.lower(), app_name.lower())
    try:
        subprocess.run(["pkill", "-f", name], check=True)
        speak(f"Closed {app_name}.")
        log.info(f"Closed: {name}")
    except subprocess.CalledProcessError:
        speak(f"No running instance of {app_name} found.")
    except Exception as e:
        speak(f"Failed to close {app_name}.")
        log.error(f"Close error for {name}: {e}")
