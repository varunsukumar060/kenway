#!/usr/bin/env python3
"""
ui/input_bar.py — KENWAY Floating Input Bar
A minimal always-on-top text box that accepts commands.
Triggered by Super+Space hotkey.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QVBoxLayout, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence

log = logging.getLogger("kenway.input_bar")


class KenwayInputBar(QWidget):
    def __init__(self, on_submit):
        super().__init__()
        self.on_submit = on_submit
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(560)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: #1c1b19;
                border: 1px solid #393836;
                border-radius: 12px;
            }
        """)
        inner = QVBoxLayout(container)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(6)

        # Header label
        header = QHBoxLayout()
        kenway_label = QLabel("⚡ KENWAY")
        kenway_label.setStyleSheet("""
            color: #4f98a3;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            background: transparent;
            border: none;
        """)
        header.addWidget(kenway_label)
        header.addStretch()
        hint_label = QLabel("ESC to dismiss")
        hint_label.setStyleSheet(
            "color: #5a5957; font-size: 10px; background: transparent; border: none;"
        )
        header.addWidget(hint_label)
        inner.addLayout(header)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Give me a command...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #cdccca;
                font-size: 16px;
                padding: 4px 0;
                selection-background-color: #313b3b;
            }
        """)
        self.input_field.returnPressed.connect(self._submit)
        inner.addWidget(self.input_field)

        layout.addWidget(container)
        self.setLayout(layout)

    def _submit(self):
        command = self.input_field.text().strip()
        if command:
            self.input_field.clear()
            self.hide()
            log.info(f"Input submitted: {command}")
            self.on_submit(command)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def show_bar(self):
        """Center on screen and show the input bar."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = int(screen.height() * 0.35)   # ~35% from top = comfortable position
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()
        log.info("Input bar shown.")
