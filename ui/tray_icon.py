#!/usr/bin/env python3
"""
ui/tray_icon.py - KENWAY System Tray

Shows LLM toggle status in system tray.
Green = LLM ON, Red = LLM OFF.
Left-click toggles. Right-click shows menu.
"""

import logging
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt

log = logging.getLogger("kenway.tray")


def _make_icon(color: str) -> QIcon:
    """Generate a simple colored circle icon for the tray."""
    px = QPixmap(22, 22)
    px.fill(Qt.transparent)
    from PyQt5.QtGui import QPainter, QBrush
    from PyQt5.QtCore import QRect
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(color)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QRect(2, 2, 18, 18))
    painter.end()
    return QIcon(px)


class KenwayTray:
    def __init__(self, app, llm_toggle_fn=None):
        self.app            = app
        self.llm_toggle_fn  = llm_toggle_fn
        self.llm_enabled    = False

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_make_icon("#cc3333"))   # red = LLM OFF
        self.tray.setToolTip("KENWAY — LLM: OFF")

        # Left click toggles LLM
        self.tray.activated.connect(self._on_activate)

        # Right-click menu
        self.menu = QMenu()

        self.llm_action = QAction("🔴  LLM Mode: OFF  (click to enable)")
        self.llm_action.triggered.connect(self._toggle_llm)
        self.menu.addAction(self.llm_action)

        self.menu.addSeparator()

        quit_action = QAction("Quit KENWAY")
        quit_action.triggered.connect(self._quit)
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)

    def show(self):
        self.tray.show()

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.Trigger:   # left click
            self._toggle_llm()

    def _toggle_llm(self):
        self.llm_enabled = not self.llm_enabled

        if self.llm_enabled:
            self.tray.setIcon(_make_icon("#33aa33"))   # green = ON
            self.tray.setToolTip("KENWAY — LLM: ON")
            self.llm_action.setText("🟢  LLM Mode: ON  (click to disable)")
        else:
            self.tray.setIcon(_make_icon("#cc3333"))   # red = OFF
            self.tray.setToolTip("KENWAY — LLM: OFF")
            self.llm_action.setText("🔴  LLM Mode: OFF  (click to enable)")

        if self.llm_toggle_fn:
            self.llm_toggle_fn(self.llm_enabled)

        log.info(f"Tray LLM toggle: {self.llm_enabled}")

    def _quit(self):
        from core.hooks import on_shutdown
        on_shutdown()
