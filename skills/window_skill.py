#!/usr/bin/env python3
"""
skills/window_skill.py — Window Management via wmctrl + xdotool
"""

import subprocess
import logging
from core.voice import speak

log = logging.getLogger("kenway.window_skill")


def focus_window(app_name: str):
    try:
        subprocess.run(["wmctrl", "-a", app_name], check=True)
        speak(f"Focused {app_name}.")
        log.info(f"Focused window: {app_name}")
    except subprocess.CalledProcessError:
        speak(f"Could not find a window named {app_name}.")
    except Exception as e:
        log.error(f"Focus error: {e}")


def minimize_window(app_name: str):
    try:
        result = subprocess.run(
            ["wmctrl", "-l"], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if app_name.lower() in line.lower():
                win_id = line.split()[0]
                subprocess.run(["xdotool", "windowminimize", win_id])
                speak(f"Minimized {app_name}.")
                log.info(f"Minimized window: {app_name}")
                return
        speak(f"No window found for {app_name}.")
    except Exception as e:
        speak("Failed to minimize window.")
        log.error(f"Minimize error: {e}")


def maximize_window(app_name: str):
    try:
        subprocess.run(["wmctrl", "-a", app_name], check=True)
        subprocess.run(["wmctrl", "-r", app_name, "-b", "add,maximized_vert,maximized_horz"])
        speak(f"Maximized {app_name}.")
        log.info(f"Maximized window: {app_name}")
    except Exception as e:
        speak("Failed to maximize window.")
        log.error(f"Maximize error: {e}")


def type_text(text: str):
    """Type text into the currently focused window."""
    try:
        subprocess.run(["xdotool", "type", "--clearmodifiers", text])
        log.info(f"Typed: {text}")
    except Exception as e:
        log.error(f"Type error: {e}")


def press_key(key: str):
    """Press a key combo. Examples: 'ctrl+s', 'Return', 'alt+F4'"""
    try:
        subprocess.run(["xdotool", "key", key])
        log.info(f"Key pressed: {key}")
    except Exception as e:
        log.error(f"Key press error: {e}")


def click_at(x: int, y: int):
    """Move mouse to (x, y) and click."""
    try:
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])
        log.info(f"Clicked at ({x}, {y})")
    except Exception as e:
        log.error(f"Click error: {e}")
