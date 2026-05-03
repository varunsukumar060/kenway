#!/usr/bin/env python3
"""
ui/tray_icon.py — KENWAY System Tray
Phase 3: Added memory clear option and Ollama status indicator.
"""

import logging
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF

log = logging.getLogger("kenway.tray")


def _make_icon(color: str) -> QIcon:
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QRectF(2, 2, 18, 18))
    painter.end()
    return QIcon(pixmap)


class KenwayTray:
    def __init__(self, app: QApplication):
        self.llm_enabled = False
        self._input_bar_ref = None

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_make_icon("#01696f"))  # Teal = direct mode
        self.tray.setToolTip("KENWAY — Online | Direct Mode | Alt+K")
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background: #1c1b19; color: #cdccca;
                border: 1px solid #393836;
                font-size: 13px; padding: 4px;
            }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #313b3b; }
            QMenu::separator { height: 1px; background: #393836; margin: 4px 8px; }
        """)

        # Status label
        self._status_action = QAction("⚡ KENWAY — Direct Mode")
        self._status_action.setEnabled(False)
        self.menu.addAction(self._status_action)
        self.menu.addSeparator()

        # LLM toggle
        self.llm_action = QAction("🔴  LLM Mode: OFF")
        self.llm_action.triggered.connect(self.toggle_llm)
        self.menu.addAction(self.llm_action)

        # Ollama status check
        ollama_action = QAction("🧠  Check Ollama Status")
        ollama_action.triggered.connect(self._check_ollama)
        self.menu.addAction(ollama_action)
        self.menu.addSeparator()

        # Open bar
        open_action = QAction("⌨️  Command Bar  (Alt+K)")
        open_action.triggered.connect(self._open_input_bar)
        self.menu.addAction(open_action)

        # Clear LLM memory
        mem_action = QAction("🧹  Clear LLM Memory")
        mem_action.triggered.connect(self._clear_memory)
        self.menu.addAction(mem_action)
        self.menu.addSeparator()

        # Quit
        quit_action = QAction("✖  Quit KENWAY")
        quit_action.triggered.connect(self._quit)
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

        log.info("Tray icon initialized (Phase 3).")
        print("[KENWAY] Tray icon visible:", self.tray.isVisible())

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._open_input_bar()

    def toggle_llm(self):
        self.llm_enabled = not self.llm_enabled
        status = "ON" if self.llm_enabled else "OFF"
        color  = "#4f98a3" if self.llm_enabled else "#01696f"
        emoji  = "🟢" if self.llm_enabled else "🔴"
        mode_label = "LLM Mode" if self.llm_enabled else "Direct Mode"

        self.llm_action.setText(f"{emoji}  LLM Mode: {status}")
        self._status_action.setText(f"⚡ KENWAY — {mode_label}")
        self.tray.setIcon(_make_icon(color))
        self.tray.setToolTip(f"KENWAY — {mode_label} | Alt+K")

        from core.voice import speak
        speak(f"LLM mode {'enabled' if self.llm_enabled else 'disabled'}.")
        log.info(f"LLM toggled: {status}")

    def _check_ollama(self):
        from core.llm_bridge import _is_ollama_running
        from core.voice import speak
        if _is_ollama_running():
            speak("Ollama is running and ready.")
        else:
            speak("Ollama is not running. Start it with: ollama serve")

    def _clear_memory(self):
        from core.llm_bridge import clear_memory
        from core.voice import speak
        clear_memory()
        speak("LLM memory cleared.")

    def set_input_bar(self, bar):
        self._input_bar_ref = bar

    def _open_input_bar(self):
        if self._input_bar_ref:
            self._input_bar_ref.show_bar()

    def _quit(self):
        from core.hooks import on_shutdown
        on_shutdown()
        QApplication.quit()
