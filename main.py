#!/usr/bin/env python3
"""
KENWAY — Main Entry Point
Phase 1: Voice engine + Boot hooks + Tray icon + Input loop
"""

import sys
import logging
import threading
from PyQt5.QtWidgets import QApplication

from core.voice import speak
from core.hooks import on_startup
from ui.tray_icon import KenwayTray
from ui.input_bar import KenwayInputBar

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="kenway.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("kenway")


def handle_command(command: str, llm_enabled: bool):
    """
    Central command dispatcher.
    Phase 1: echo back with voice (full routing added in Phase 2).
    """
    if not command.strip():
        return

    log.info(f"Command received [LLM={'ON' if llm_enabled else 'OFF'}]: {command}")

    # ── Phase 2+ will route through intent_parser / llm_bridge here ──
    # For now, acknowledge the command
    speak(f"Got it. You said: {command}")


def main():
    log.info("KENWAY starting up...")

    # Boot greeting (runs in thread so Qt doesn't block)
    threading.Thread(target=on_startup, daemon=True).start()

    # Qt application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)   # Keep running when input bar closes

    # System tray
    tray = KenwayTray(app)

    # Floating input bar (hidden by default, shown via hotkey)
    input_bar = KenwayInputBar(
        on_submit=lambda cmd: handle_command(cmd, tray.llm_enabled)
    )

    # Register global hotkey: Super+Space → show input bar
    try:
        from pynput import keyboard

        def on_hotkey():
            input_bar.show_bar()

        hotkey = keyboard.GlobalHotKeys({
            "<super>+<space>": on_hotkey
        })
        hotkey.start()
        log.info("Hotkey Super+Space registered.")
    except Exception as e:
        log.warning(f"Hotkey registration failed: {e}. Use tray menu to open input bar.")

    log.info("KENWAY is online.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
