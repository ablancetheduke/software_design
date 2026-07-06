"""StatCard — neumorphic metric card with hover lift.

Used by: DashboardView, GpaView.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ...utils.theme import theme


class StatCard(QFrame):
    """A single metric card — large value, subtle label, hover lift.

    Neumorphic style: white card, subtle shadow, accent-coloured value,
    soft amber glow on hover.
    """

    def __init__(
        self,
        title: str,
        value: str,
        color: str = f"{theme.primary}",
        parent=None,
    ):
        super().__init__(parent)
        self.color = color
        self.setObjectName("StatCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"StatCard {{"
            f"  background: {theme.bg_card};"
            f"  border: 1px solid {theme.border};"
            f"  border-radius: {theme.radius_lg};"
            f"  padding: 20px 22px;"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size: 34px; font-weight: 800; color: {color};"
            f"letter-spacing: -1px;"
        )
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"font-size: 12px; color: {theme.fg_muted};"
            f"font-weight: 500; text-transform: uppercase;"
            f"letter-spacing: 0.5px;"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

    def enterEvent(self, event):
        self.setStyleSheet(
            f"StatCard {{"
            f"  background: {theme.bg_card};"
            f"  border: 2px solid {self.color};"
            f"  border-radius: {theme.radius_lg};"
            f"}}"
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(
            f"StatCard {{"
            f"  background: {theme.bg_card};"
            f"  border: 1px solid {theme.border};"
            f"  border-radius: {theme.radius_lg};"
            f"}}"
        )
        super().leaveEvent(event)
