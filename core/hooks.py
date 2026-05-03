#!/usr/bin/env python3
"""
core/hooks.py — KENWAY Boot & Shutdown Hooks
"""

import logging
import time
from datetime import datetime
from core.voice import speak_blocking

log = logging.getLogger("kenway.hooks")


def _get_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


def on_startup():
    time.sleep(2)
    greeting = _get_greeting()
    # Fixed: removed mention of Super+Space
    message = (
        f"{greeting}, Varun. "
        f"Kenway systems online. "
        f"Press Alt and K to give me a command."
    )
    log.info(f"Startup greeting: {message}")
    speak_blocking(message)


def on_shutdown():
    message = "Shutting down, Varun. Stay sharp."
    log.info(f"Shutdown: {message}")
    speak_blocking(message)
