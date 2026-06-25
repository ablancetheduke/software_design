"""CategoryCard — clickable curriculum category card with progress bar.

Used by: DashboardView.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout

from ...utils.theme import theme


class CategoryCard(QFrame):
    """Clickable curriculum category card showing completion progress."""

    def __init__(self, result, color: str, on_click, parent=None):
        super().__init__(parent)
        self.color = color
        self.result = result
        self.on_click = on_click
        self.setObjectName("CategoryCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(theme.card_stylesheet(theme.border, hovered=False))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        required_text = (
            "-"
            if result.required_credits <= 0
            else f"{result.required_credits:g}"
        )
        header = QLabel(f"<b>{result.name}</b>　目标 {required_text}")
        header.setTextFormat(Qt.TextFormat.RichText)
        header.setStyleSheet(f"color: {theme.fg}; font-size: 14px;")
        layout.addWidget(header)

        sub = QLabel(
            f"已完成 {result.earned_credits:g} 学分"
            + (
                f" ｜ 还差 {result.remaining_credits:g}"
                if result.required_credits > 0
                else ""
            )
            + f" ｜ {len(result.courses)} 门课"
        )
        sub.setStyleSheet(f"color: {theme.fg_muted}; font-size: 12px;")
        layout.addWidget(sub)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        percent = round(result.completion_ratio * 100)
        self.progress.setValue(min(100, percent))
        self.progress.setFormat(
            "计划外"
            if result.required_credits <= 0
            else f"{min(100, percent)}%"
        )
        self.progress.setStyleSheet(
            "QProgressBar { height: 14px; border: none; border-radius: 0; "
            f"background-color: #eee7dc; text-align: center; font-size: 11px; color: {theme.fg}; }}"
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 0; }}"
        )
        layout.addWidget(self.progress)
        self.setToolTip(self._tooltip_text())

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click(self.result)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(theme.card_stylesheet(self.color, hovered=True))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(theme.card_stylesheet(theme.border, hovered=False))
        super().leaveEvent(event)

    def _tooltip_text(self):
        if self.result.required_credits <= 0:
            return (
                f"{self.result.name}: {len(self.result.courses)} 门，"
                f"{self.result.earned_credits:g} 学分"
            )
        return (
            f"{self.result.name}: 已完成 {self.result.earned_credits:g}/"
            f"{self.result.required_credits:g} 学分，"
            f"还差 {self.result.remaining_credits:g} 学分"
        )
