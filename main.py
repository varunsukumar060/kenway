#!/usr/bin/env python3
"""
main.py - KENWAY Entry Point

Dual-brain architecture:
  DIRECT MODE (default) : regex rule engine, zero LLM, instant response
  LLM MODE (toggled ON) : qwen2.5:0.5b via Ollama for ambiguous commands

Ollama note: systemd service already runs at boot (installed via install.sh).
  OLLAMA_KEEP_ALIVE=0 is set in llm_bridge.py per-request, no need to
  restart ollama serve manually.

If pyttsx3 fails: sudo apt install espeak-ng
"""

import sys
import logging
import os
from PyQt5.QtWidgets import QApplication

# Tell Ollama to unload model from RAM immediately after each response
os.environ.setdefault("OLLAMA_KEEP_ALIVE", "0")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("kenway.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("kenway.main")

# ---------------------------------------------------------------------------
# Global LLM toggle state
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Command handler — called by input bar on submit
# ---------------------------------------------------------------------------

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

    # If direct mode couldn't match, suggest enabling LLM
    if intent["action"] == "UNKNOWN" and not LLM_ENABLED:
        speak("I don't recognise that command. Enable LLM mode for smarter parsing.")
        return

    dispatch(intent, speak_fn=speak)


# ---------------------------------------------------------------------------
# Boot
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Boot greeting
    from core.hooks import on_startup
    on_startup()

    # System tray with LLM toggle
    from ui.tray_icon import KenwayTray
    tray = KenwayTray(app, llm_toggle_fn=set_llm_enabled)
    tray.show()

    # Floating input bar
    from ui.input_bar import KenwayInputBar
    bar = KenwayInputBar(on_submit=handle_command)

    # Global hotkey: Alt+K to show input bar
    # (Super+Space conflicts with many DEs; Alt+K is safer on XFCE)
    try:
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        shortcut = QShortcut(QKeySequence("Alt+K"), bar)
        shortcut.activated.connect(bar.show_bar)
        log.info("Hotkey registered: Alt+K")
    except Exception as e:
        log.warning(f"Hotkey registration failed: {e}")

    log.info("KENWAY online. Press Alt+K to open command bar.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
