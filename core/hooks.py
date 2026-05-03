#!/usr/bin/env python3
"""
core/hooks.py — KENWAY Boot & Shutdown Hooks
Handles greeting on startup and farewell on shutdown.
"""

import logging
import time
from datetime import datetime
from core.voice import speak_blocking

log = logging.getLogger("kenway.hooks")


def _get_greeting() -> str:
    """Return time-appropriate greeting."""
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


def on_startup():
    """
    Called once when KENWAY starts.
    Waits a moment for the audio system to be ready, then greets.
    """
    time.sleep(2)   # Let PipeWire/ALSA fully initialize
    greeting = _get_greeting()
    message = (
        f"{greeting}, Varun. "
        f"KENWAY systems online. "
        f"Press Super and Space to give me a command."
    )
    log.info(f"Startup greeting: {message}")
    speak_blocking(message)


def on_shutdown():
    """
    Called before KENWAY exits.
    """
    message = "Shutting down, Varun. Stay sharp."
    log.info(f"Shutdown: {message}")
    speak_blocking(message)
