#!/usr/bin/env python3
"""
main.py - KENWAY Entry Point

Dual-brain architecture:
  DIRECT MODE (default) : regex rule engine, zero LLM, instant response
  LLM MODE (toggled ON) : qwen2.5:0.5b via Ollama for ambiguous commands

Hotkey strategy:
  KENWAY listens on a Unix socket at /tmp/kenway.sock
  A tiny trigger script (scripts/trigger.sh) sends a signal to that socket.
  That trigger script is bound to Ctrl+F12 in XFCE keyboard settings.
  This works globally with zero terminal conflicts.

  Setup (one-time):
    xfce4-keyboard-settings -> Application Shortcuts
    Command : bash /home/<you>/kenway/scripts/trigger.sh
    Key     : Ctrl+F12  (or any key with no conflicts)
"""

import sys
import logging
import os
import threading
import socket
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QMetaObject, Qt

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

SOCKET_PATH = "/tmp/kenway.sock"
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


def _socket_listener(bar):
    """
    Listens on Unix socket /tmp/kenway.sock.
    Any connection (even empty) triggers the input bar to appear.
    The trigger script just does: echo '' | nc -U /tmp/kenway.sock
    """
    # Clean up stale socket
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    os.chmod(SOCKET_PATH, 0o600)
    log.info(f"Socket listener active: {SOCKET_PATH}")

    while True:
        try:
            conn, _ = server.accept()
            conn.close()
            # Thread-safe call to Qt main thread
            QMetaObject.invokeMethod(bar, "show_bar", Qt.QueuedConnection)
            log.info("Socket trigger received — showing input bar.")
        except Exception as e:
            log.error(f"Socket listener error: {e}")
            break


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

    # Socket listener in background daemon thread
    sock_thread = threading.Thread(
        target=_socket_listener,
        args=(bar,),
        daemon=True
    )
    sock_thread.start()

    log.info("KENWAY online. Waiting for socket trigger on /tmp/kenway.sock")
    log.info("Bind shortcut in XFCE: bash ~/kenway/scripts/trigger.sh")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
