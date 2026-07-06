"""Reusable record table widget.

Provides a QTableWidget with common functionality:
- Load data from a list of models
- Row selection signals
- Context menu support
- Column configuration
"""

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction


class RecordTable(QTableWidget):
    """A configurable table for displaying records."""

    row_selected = Signal(int)     # Emits record ID
    row_double_clicked_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)

        self._id_column = 0  # Which column stores the record ID

        self.cellClicked.connect(self._on_cell_clicked)
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def set_columns(self, headers: list, id_column: int = 0):
        """Configure table columns."""
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self._id_column = id_column
        if id_column >= 0:
            self.setColumnHidden(id_column, True)  # Hide ID column

    def load_data(self, rows: list):
        """Load rows into the table. Each row is a list/tuple of values."""
        self.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.setItem(i, j, item)
        self.resizeColumnsToContents()

    def get_selected_id(self) -> int:
        """Get the ID of the selected row."""
        row = self.currentRow()
        if row < 0:
            return -1
        item = self.item(row, self._id_column)
        return int(item.text()) if item else -1

    def _on_cell_clicked(self, row: int, col: int):
        id_val = self._get_row_id(row)
        if id_val >= 0:
            self.row_selected.emit(id_val)

    def _on_cell_double_clicked(self, row: int, col: int):
        id_val = self._get_row_id(row)
        if id_val >= 0:
            self.row_double_clicked_signal.emit(id_val)

    def _get_row_id(self, row: int) -> int:
        if self._id_column < 0:
            return row
        item = self.item(row, self._id_column)
        return int(item.text()) if item else -1
