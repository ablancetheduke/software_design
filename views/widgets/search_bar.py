"""Reusable search bar widget.

A QLineEdit with a clear button and search icon.
Emits: search_requested(str) when user types (debounced).
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QIcon


class SearchBar(QWidget):
    """Search input with clear button and delayed search signal."""

    search_requested = Signal(str)

    def __init__(self, placeholder: str = "搜索...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setClearButtonEnabled(True)
        layout.addWidget(self.input)

        # Debounce timer: emit search after 300ms pause in typing
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._emit_search)

        self.input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        self._timer.start()

    def _emit_search(self):
        self.search_requested.emit(self.input.text())
