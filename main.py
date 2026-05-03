#!/usr/bin/env python3
"""
main.py - KENWAY Entry Point

Dual-brain architecture:
  DIRECT MODE (default) : regex rule engine, zero LLM, instant response
  LLM MODE (toggled ON) : qwen2.5:0.5b via Ollama for ambiguous commands

Hotkey: Alt+K (global, works regardless of focused window)
Requires: pip install keyboard  AND  run with sudo OR add user to input group:
  sudo usermod -aG input $USER  (then log out and back in)
"""

import sys
import logging
import os
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG

os.environ.setdefault("OLLAMA_KEEP_ALIVE", "0")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("kenway.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("kenway.main")

LLM_ENABLED = False


def set_llm_enabled(state: bool):
    global LLM_ENABLED
    LLM_ENABLED = state
    status = "ON" if state else "OFF"
    log.info(f"LLM mode: {status}")
    from core.voice import speak
    if state:
        from core.llm_bridge import is_ollama_running
        if not is_ollama_running():
            speak("Warning: Ollama is not running. Run ollama serve in a terminal.")
            return
    speak(f"L L M mode is now {status}.")


def handle_command(command: str):
    command = command.strip()
    if not command:
        return
    log.info(f"Command received: '{command}'")
    from core.voice import speak
    from core.executor import dispatch
    if LLM_ENABLED:
        from core.llm_bridge import parse as llm_parse
        intent = llm_parse(command)
    else:
        from core.intent_parser import parse as direct_parse
        intent = direct_parse(command)
    if intent["action"] == "UNKNOWN" and not LLM_ENABLED:
        speak("I don't recognise that command. Enable LLM mode for smarter parsing.")
        return
    dispatch(intent, speak_fn=speak)


def _start_global_hotkey(bar):
    """
    Run in a daemon thread.
    Listens for Alt+K globally and calls bar.show_bar() thread-safely.
    Requires 'keyboard' lib and /dev/input read access.
    """
    try:
        import keyboard
        def _trigger():
            # Must call Qt UI from main thread — use invokeMethod
            QMetaObject.invokeMethod(bar, "show_bar", Qt.QueuedConnection)
            log.info("Global hotkey Alt+K triggered.")

        keyboard.add_hotkey("alt+k", _trigger)
        log.info("Global hotkey active: Alt+K")
        keyboard.wait()   # blocks this thread forever, listening for hotkeys
    except ImportError:
        log.error("'keyboard' library not installed. Run: pip install keyboard")
    except PermissionError:
        log.error(
            "No permission to read /dev/input. Fix with:\n"
            "  sudo usermod -aG input $USER\n"
            "  then log out and back in, or run KENWAY with sudo."
        )
    except Exception as e:
        log.error(f"Global hotkey error: {e}")


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from core.hooks import on_startup
    on_startup()

    from ui.tray_icon import KenwayTray
    tray = KenwayTray(app, llm_toggle_fn=set_llm_enabled)
    tray.show()

    from ui.input_bar import KenwayInputBar
    bar = KenwayInputBar(on_submit=handle_command)

    # Global hotkey in background daemon thread
    hotkey_thread = threading.Thread(
        target=_start_global_hotkey,
        args=(bar,),
        daemon=True
    )
    hotkey_thread.start()

    log.info("KENWAY online. Press Alt+K anywhere to open command bar.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
