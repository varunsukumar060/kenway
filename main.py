#!/usr/bin/env python3
"""
KENWAY — Main Entry Point
Phase 1: Voice engine + Boot hooks + Tray icon + Input loop
"""

import sys
import logging
import threading

print("[KENWAY] Starting up...")
print("[KENWAY] Loading Qt...")

from PyQt5.QtWidgets import QApplication
print("[KENWAY] Qt loaded.")

from core.voice import speak
print("[KENWAY] Voice module loaded.")

from core.hooks import on_startup
print("[KENWAY] Hooks module loaded.")

from ui.tray_icon import KenwayTray
print("[KENWAY] Tray module loaded.")

from ui.input_bar import KenwayInputBar
print("[KENWAY] Input bar module loaded.")

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("kenway.log"),
        logging.StreamHandler(sys.stdout)   # Also print to terminal
    ]
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
    print(f"[KENWAY] Command: {command}")

    # ── Phase 2+ will route through intent_parser / llm_bridge here ──
    speak(f"Got it. You said: {command}")


def main():
    print("[KENWAY] Entering main()...")
    log.info("KENWAY starting up...")

    # Qt application — must be created BEFORE any widgets or tray icons
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    print("[KENWAY] QApplication created.")

    # Check if system tray is available
    from PyQt5.QtWidgets import QSystemTrayIcon
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("[KENWAY] WARNING: System tray not available on this desktop!")
        log.warning("System tray not available.")
    else:
        print("[KENWAY] System tray is available.")

    # System tray
    tray = KenwayTray(app)
    print("[KENWAY] Tray icon created.")

    # Floating input bar
    input_bar = KenwayInputBar(
        on_submit=lambda cmd: handle_command(cmd, tray.llm_enabled)
    )
    tray.set_input_bar(input_bar)
    print("[KENWAY] Input bar created.")

    # Register global hotkey: Alt+K → show input bar
    # (Changed from Super+Space — Super opens the XFCE start menu)
    try:
        from pynput import keyboard

        def on_hotkey():
            print("[KENWAY] Hotkey Alt+K triggered.")
            input_bar.show_bar()

        hotkey = keyboard.GlobalHotKeys({
            "<alt>+k": on_hotkey
        })
        hotkey.start()
        print("[KENWAY] Hotkey Alt+K registered successfully.")
        log.info("Hotkey Alt+K registered.")
    except Exception as e:
        print(f"[KENWAY] Hotkey registration failed: {e}")
        log.warning(f"Hotkey registration failed: {e}")

    # Boot greeting in background thread (after Qt is running)
    threading.Thread(target=on_startup, daemon=True).start()
    print("[KENWAY] Boot greeting thread started.")

    print("[KENWAY] KENWAY is online. Press Alt+K to open command bar.")
    print("[KENWAY] Right-click the teal dot in your system tray for options.")
    log.info("KENWAY is online.")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
