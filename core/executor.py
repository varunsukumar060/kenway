#!/usr/bin/env python3
"""
core/executor.py — KENWAY Action Dispatcher
Routes parsed intents to the correct skill handler.
"""

import logging
from core.voice import speak

log = logging.getLogger("kenway.executor")


def dispatch(intent: dict):
    """
    Takes an intent dict {action, data, mode} and calls the right skill.
    Skills are imported lazily to keep startup fast.
    """
    action = intent.get("action", "UNKNOWN")
    data = intent.get("data")
    mode = intent.get("mode", "direct")

    log.info(f"Dispatching action={action} data={data} mode={mode}")

    try:
        # ── Browser / Media ──────────────────────────────────────────────────
        if action == "YOUTUBE_PLAY":
            from skills.browser_skill import play_on_youtube
            play_on_youtube(data)

        elif action == "YOUTUBE_SEARCH":
            from skills.browser_skill import search_youtube
            search_youtube(data)

        elif action == "GOOGLE_SEARCH":
            from skills.browser_skill import search_google
            search_google(data)

        elif action == "OPEN_URL":
            from skills.browser_skill import open_url
            open_url(data)

        elif action == "SPOTIFY_PLAY":
            from skills.media_skill import play_on_spotify
            play_on_spotify(data)

        # ── App Control ──────────────────────────────────────────────────────
        elif action == "OPEN_APP":
            from skills.app_skill import launch_app
            launch_app(data)

        elif action == "CLOSE_APP":
            from skills.app_skill import close_app
            close_app(data)

        # ── System ───────────────────────────────────────────────────────────
        elif action == "VOLUME_SET":
            from skills.system_skill import set_volume
            set_volume(data)

        elif action == "BATTERY_STATUS":
            from skills.system_skill import get_battery
            get_battery()

        elif action == "SHUTDOWN":
            from skills.system_skill import shutdown
            shutdown()

        elif action == "REBOOT":
            from skills.system_skill import reboot
            reboot()

        elif action == "SLEEP":
            from skills.system_skill import sleep_system
            sleep_system()

        elif action == "BRIGHTNESS_SET":
            from skills.system_skill import set_brightness
            set_brightness(data)

        # ── Screen & Files ───────────────────────────────────────────────────
        elif action == "READ_SCREEN":
            from core.screen import read_screen
            text = read_screen()
            speak(f"Screen reads: {text[:200]}")

        elif action == "FILE_READ":
            from core.file_manager import read_file
            content = read_file(data)
            speak(f"File content: {content[:200]}")

        elif action == "FILE_WRITE":
            from core.file_manager import write_file
            write_file(data["path"], data["content"])

        elif action == "FILE_OPEN":
            from skills.file_skill import open_file
            open_file(data)

        # ── Window Management ────────────────────────────────────────────────
        elif action == "WINDOW_FOCUS":
            from skills.window_skill import focus_window
            focus_window(data)

        elif action == "WINDOW_MINIMIZE":
            from skills.window_skill import minimize_window
            minimize_window(data)

        elif action == "WINDOW_MAXIMIZE":
            from skills.window_skill import maximize_window
            maximize_window(data)

        # ── Unknown ──────────────────────────────────────────────────────────
        elif action == "UNKNOWN":
            speak("I didn't understand that command. Try enabling LLM mode for complex tasks.")
            log.warning(f"Unknown command: {data}")

        else:
            speak(f"Action {action} is not yet implemented.")
            log.warning(f"Unhandled action: {action}")

    except ImportError as e:
        speak("That skill is not yet available.")
        log.error(f"Skill import error for {action}: {e}")
    except Exception as e:
        speak("Something went wrong while executing that command.")
        log.error(f"Executor error for {action}: {e}")
