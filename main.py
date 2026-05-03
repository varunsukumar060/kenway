#!/usr/bin/env python3
"""
KENWAY — Main Entry Point
"""

import sys
import logging
import threading

print("[KENWAY] Starting up...")

from PyQt5.QtWidgets import QApplication
from core.voice import speak
from core.hooks import on_startup
from ui.tray_icon import KenwayTray
from ui.input_bar import KenwayInputBar

print("[KENWAY] All modules loaded.")

# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("kenway.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("kenway")


def handle_command(command: str, llm_enabled: bool):
    """
    Central command dispatcher.
    Routes through intent_parser (Direct Mode) or llm_bridge (LLM Mode).
    """
    if not command.strip():
        return

    log.info(f"Command [{('LLM' if llm_enabled else 'DIRECT')}]: {command}")
    print(f"[KENWAY] Executing: {command}")

    # Parse intent
    if llm_enabled:
        from core.llm_bridge import ask
        intent = ask(command)
    else:
        from core.intent_parser import parse
        intent = parse(command)

    print(f"[KENWAY] Intent: {intent}")

    # Dispatch to skill
    from core.executor import dispatch
    threading.Thread(target=dispatch, args=(intent,), daemon=True).start()


def main():
    log.info("KENWAY starting up...")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from PyQt5.QtWidgets import QSystemTrayIcon
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[KENWAY] WARNING: No system tray available!")

    tray = KenwayTray(app)

    input_bar = KenwayInputBar(
        on_submit=lambda cmd: handle_command(cmd, tray.llm_enabled)
    )
    tray.set_input_bar(input_bar)

    # Register hotkey: Alt+K
    try:
        from pynput import keyboard
        hotkey = keyboard.GlobalHotKeys({"<alt>+k": input_bar.show_bar})
        hotkey.start()
        print("[KENWAY] Hotkey Alt+K registered.")
    except Exception as e:
        print(f"[KENWAY] Hotkey failed: {e}. Use tray to open bar.")

    # Boot greeting after Qt is running
    threading.Thread(target=on_startup, daemon=True).start()

    print("[KENWAY] Online. Alt+K = command bar. Right-click tray for menu.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
