"""StatCard — reusable metric card with hover feedback.

Used by: DashboardView, GpaView.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ...utils.theme import theme


class StatCard(QFrame):
    """A single statistic card with a large number and label.

    Hovering highlights the card border with its accent colour.
    """

    def __init__(
        self,
        title: str,
        value: str,
        color: str = f"{theme.accent}",
        parent=None,
    ):
        super().__init__(parent)
        self.color = color
        self.setObjectName("StatCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(theme.card_stylesheet(color, hovered=False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size: 30px; font-weight: bold; color: {color};"
        )
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"font-size: 13px; color: {theme.fg_muted};")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

    def enterEvent(self, event):
        self.setStyleSheet(theme.card_stylesheet(self.color, hovered=True))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(theme.card_stylesheet(theme.border, hovered=False))
        super().leaveEvent(event)
