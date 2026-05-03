#!/usr/bin/env python3
"""
core/executor.py — KENWAY Action Dispatcher
"""

import logging
from core.voice import speak

log = logging.getLogger("kenway.executor")


def dispatch(intent: dict):
    action = intent.get("action", "UNKNOWN")
    data   = intent.get("data")
    log.info(f"Dispatching action={action} data={data}")

    # ── System ──────────────────────────────────────────────────────────────
    if action == "VOLUME_SET":
        from skills.system_skill import set_volume
        speak(set_volume(data))

    elif action == "BATTERY_STATUS":
        from skills.system_skill import get_battery
        speak(get_battery())

    elif action == "BRIGHTNESS_SET":
        from skills.system_skill import set_brightness
        speak(set_brightness(data))

    elif action == "BRIGHTNESS_GET":
        from skills.system_skill import get_brightness
        speak(get_brightness())

    elif action == "SHUTDOWN":
        speak("Shutting down your system in 5 seconds, Varun.")
        import time; time.sleep(5)
        import subprocess; subprocess.run(["shutdown", "-h", "now"])

    elif action == "REBOOT":
        speak("Rebooting in 5 seconds, Varun.")
        import time; time.sleep(5)
        import subprocess; subprocess.run(["reboot"])

    # ── Apps ──────────────────────────────────────────────────────────────
    elif action == "OPEN_APP":
        from skills.app_skill import launch_app
        speak(launch_app(data))

    elif action == "CLOSE_APP":
        from skills.app_skill import close_app
        speak(close_app(data))

    # ── Browser ────────────────────────────────────────────────────────────
    elif action == "YOUTUBE_PLAY":
        from skills.browser_skill import play_on_youtube
        speak(play_on_youtube(data))

    elif action == "GOOGLE_SEARCH":
        from skills.browser_skill import search_google
        speak(search_google(data))

    elif action == "OPEN_URL":
        from skills.browser_skill import open_url_direct
        speak(open_url_direct(data))

    # ── Folders ────────────────────────────────────────────────────────────
    elif action == "OPEN_FOLDER":
        from skills.folder_skill import open_folder
        speak(open_folder(data))

    elif action == "LIST_FOLDER":
        from skills.folder_skill import list_folder_contents
        speak(list_folder_contents(data))

    # ── Files ──────────────────────────────────────────────────────────────
    elif action == "OPEN_FILE":
        from skills.file_skill import open_file
        speak(open_file(data))

    elif action == "FILE_READ":
        from skills.file_skill import read_file
        speak(read_file(data))

    elif action == "FILE_WRITE":
        if isinstance(data, (list, tuple)) and len(data) == 2:
            from skills.file_skill import write_file
            speak(write_file(data[0], data[1]))
        else:
            speak("I couldn't parse that file write command.")

    elif action == "FILE_LIST":
        from skills.file_skill import list_files
        speak(list_files(data))

    elif action == "READ_SCREEN":
        from core.screen import read_screen
        speak(read_screen())

    # ── Unknown ──────────────────────────────────────────────────────────────
    else:
        log.warning(f"Unknown action: {action}")
        speak("I don't recognise that command. Enable LLM mode for complex requests.")
