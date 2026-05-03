#!/usr/bin/env python3
"""
core/executor.py — KENWAY Action Dispatcher
Routes parsed intents to the correct skill module.
"""

import logging
from core.voice import speak

log = logging.getLogger("kenway.executor")


def dispatch(intent: dict):
    action = intent.get("action", "UNKNOWN")
    data   = intent.get("data")

    log.info(f"Dispatching action={action} data={data} mode={intent.get('mode')}")

    # ── System skills ────────────────────────────────────────────────
    if action == "VOLUME_SET":
        from skills.system_skill import set_volume
        msg = set_volume(data)
        speak(msg)

    elif action == "BATTERY_STATUS":
        from skills.system_skill import get_battery
        msg = get_battery()
        speak(msg)

    elif action == "BRIGHTNESS_SET":
        from skills.system_skill import set_brightness
        msg = set_brightness(data)
        speak(msg)

    elif action == "SHUTDOWN":
        speak("Shutting down your system in 5 seconds, Varun.")
        import time; time.sleep(5)
        import subprocess; subprocess.run(["shutdown", "-h", "now"])

    elif action == "REBOOT":
        speak("Rebooting your system in 5 seconds, Varun.")
        import time; time.sleep(5)
        import subprocess; subprocess.run(["reboot"])

    # ── App skills ─────────────────────────────────────────────────
    elif action == "OPEN_APP":
        from skills.app_skill import launch_app
        msg = launch_app(data)
        speak(msg)

    elif action == "CLOSE_APP":
        from skills.app_skill import close_app
        msg = close_app(data)
        speak(msg)

    # ── Browser skills ──────────────────────────────────────────────
    elif action == "YOUTUBE_PLAY":
        from skills.browser_skill import play_on_youtube
        msg = play_on_youtube(data)
        speak(msg)

    elif action == "GOOGLE_SEARCH":
        from skills.browser_skill import search_google
        msg = search_google(data)
        speak(msg)

    elif action == "OPEN_URL":
        from skills.browser_skill import open_url_direct
        msg = open_url_direct(data)
        speak(msg)

    # ── File skills ─────────────────────────────────────────────────
    elif action == "FILE_READ":
        from skills.file_skill import read_file
        msg = read_file(data)
        speak(msg)

    elif action == "FILE_WRITE":
        # data is a tuple: (content, filename)
        if isinstance(data, (list, tuple)) and len(data) == 2:
            from skills.file_skill import write_file
            msg = write_file(data[0], data[1])
            speak(msg)
        else:
            speak("I couldn't understand the file write command.")

    elif action == "FILE_LIST":
        from skills.file_skill import list_files
        msg = list_files(data)
        speak(msg)

    # ── Screen skill ───────────────────────────────────────────────
    elif action == "READ_SCREEN":
        from core.screen import read_screen
        msg = read_screen()
        speak(msg)

    # ── Unknown ───────────────────────────────────────────────────
    else:
        log.warning(f"Unknown action: {action} | data: {data}")
        speak("I don't recognise that command in direct mode. Try enabling LLM mode for complex tasks.")
