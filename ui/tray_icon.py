#!/usr/bin/env python3
"""
ui/tray_icon.py — KENWAY System Tray Icon
Provides LLM toggle button and quick access menu.
"""

import logging
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize

log = logging.getLogger("kenway.tray")


def _make_icon(color: str) -> QIcon:
    """Generate a simple colored circle icon for the tray."""
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.transparent)
    from PyQt5.QtGui import QPainter
    from PyQt5.QtCore import QRectF
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
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_make_icon("#01696f"))   # Teal = online
        self.tray.setToolTip("KENWAY — Online | LLM: OFF")

        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu { background: #1c1b19; color: #cdccca; border: 1px solid #393836;
                    font-family: sans-serif; font-size: 13px; padding: 4px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #313b3b; }
        """)

        # LLM toggle action
        self.llm_action = QAction("🔴  LLM Mode: OFF")
        self.llm_action.triggered.connect(self.toggle_llm)
        self.menu.addAction(self.llm_action)

        self.menu.addSeparator()

        # Open input bar
        open_bar_action = QAction("⌨️  Open Input Bar")
        open_bar_action.triggered.connect(self._open_input_bar)
        self.menu.addAction(open_bar_action)

        self.menu.addSeparator()

        # Quit
        quit_action = QAction("✖  Quit KENWAY")
        quit_action.triggered.connect(self._quit)
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self._input_bar_ref = None
        log.info("Tray icon initialized.")

    def toggle_llm(self):
        self.llm_enabled = not self.llm_enabled
        status = "ON" if self.llm_enabled else "OFF"
        icon_color = "#4f98a3" if self.llm_enabled else "#01696f"
        emoji = "🟢" if self.llm_enabled else "🔴"

        self.llm_action.setText(f"{emoji}  LLM Mode: {status}")
        self.tray.setIcon(_make_icon(icon_color))
        self.tray.setToolTip(f"KENWAY — Online | LLM: {status}")

        from core.voice import speak
        speak(f"LLM mode is now {status}.")
        log.info(f"LLM mode toggled: {status}")

    def set_input_bar(self, bar):
        """Register the input bar reference for tray menu access."""
        self._input_bar_ref = bar

    def _open_input_bar(self):
        if self._input_bar_ref:
            self._input_bar_ref.show_bar()

    def _quit(self):
        from core.hooks import on_shutdown
        on_shutdown()
        QApplication.quit()
