#!/usr/bin/env python3
"""
core/executor.py - KENWAY Action Dispatcher

Routes parsed intent dicts to the correct skill function.
Works identically for both direct mode and LLM mode intents
since both produce the same {action, data} structure.
"""

import logging

log = logging.getLogger("kenway.executor")


def dispatch(intent: dict, speak_fn=None) -> str:
    """
    Execute the action described in intent.
    Returns a response string (also spoken if speak_fn provided).

    intent = {
        "action": "YOUTUBE_PLAY",
        "data":   "gangnam style",
        "mode":   "direct" | "llm"
    }
    """
    action = intent.get("action", "UNKNOWN")
    data   = intent.get("data", "")
    mode   = intent.get("mode", "direct")

    log.info(f"Dispatching [{mode}]: {action} | data={data}")

    response = _route(action, data)

    if speak_fn and response:
        speak_fn(response)

    return response


def _route(action: str, data) -> str:
    # ----------------------------------------------------------------
    # Browser skills
    # ----------------------------------------------------------------
    if action == "YOUTUBE_PLAY":
        from skills.browser_skill import play_on_youtube
        return play_on_youtube(str(data))

    if action == "SPOTIFY_PLAY":
        from skills.browser_skill import play_on_spotify
        return play_on_spotify(str(data))

    if action == "GOOGLE_SEARCH":
        from skills.browser_skill import search_google
        return search_google(str(data))

    if action == "OPEN_URL":
        from skills.browser_skill import open_url_direct
        return open_url_direct(str(data))

    # ----------------------------------------------------------------
    # App skills (stub — skills/app_skill.py built in Phase 3)
    # ----------------------------------------------------------------
    if action == "OPEN_APP":
        import subprocess
        app = str(data).lower().strip()
        try:
            subprocess.Popen([app],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return f"Opening {app}."
        except FileNotFoundError:
            return f"Could not find application: {app}"

    if action == "CLOSE_APP":
        import subprocess
        app = str(data).lower().strip()
        subprocess.run(["pkill", "-x", app], capture_output=True)
        return f"Closed {app}."

    # ----------------------------------------------------------------
    # System skills (stub — skills/system_skill.py built in Phase 3)
    # ----------------------------------------------------------------
    if action == "VOLUME_SET":
        import subprocess
        d = str(data).strip().lower()
        if d == "up":
            subprocess.run(["amixer", "-q", "sset", "Master", "5%+"])
            return "Volume up."
        elif d == "down":
            subprocess.run(["amixer", "-q", "sset", "Master", "5%-"])
            return "Volume down."
        elif d.isdigit():
            subprocess.run(["amixer", "-q", "sset", "Master", f"{d}%"])
            return f"Volume set to {d}%."
        return "Volume command not understood."

    if action == "BATTERY_STATUS":
        try:
            with open("/sys/class/power_supply/BAT0/capacity") as f:
                pct = f.read().strip()
            with open("/sys/class/power_supply/BAT0/status") as f:
                status = f.read().strip()
            return f"Battery is at {pct}%, currently {status}."
        except FileNotFoundError:
            return "Could not read battery status."

    if action == "SHUTDOWN":
        import subprocess
        from core.voice import speak
        speak("Shutting down. Goodbye, Varun.")
        subprocess.run(["shutdown", "-h", "now"])
        return ""

    # ----------------------------------------------------------------
    # Unknown
    # ----------------------------------------------------------------
    if action == "UNKNOWN":
        error = intent.get("error", "")
        if "Ollama not running" in error:
            return "LLM mode is on but Ollama is not running. Start it with: ollama serve"
        if "timeout" in error.lower():
            return "LLM took too long to respond. Try a simpler command or switch to direct mode."
        return f"I didn't understand that command: {data}"

    return f"Unknown action: {action}"
