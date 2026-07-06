"""CategoryCard — clickable curriculum category card with rounded progress bar.

Used by: DashboardView.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout

from ...utils.theme import theme


class CategoryCard(QFrame):
    """Clickable curriculum category card — rounded, warm style."""

    def __init__(self, result, color: str, on_click, parent=None):
        super().__init__(parent)
        self.color = color
        self.result = result
        self.on_click = on_click
        self.setObjectName("CategoryCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style(hovered=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

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
            "QProgressBar {"
            f"  height: 12px; border: none; border-radius: {theme.radius_pill};"
            f"  background-color: {theme.bg_hover};"
            f"  text-align: center; font-size: 11px; color: {theme.fg};"
            f"}}"
            f"QProgressBar::chunk {{"
            f"  background-color: {color}; border-radius: {theme.radius_pill};"
            f"}}"
            f"QProgressBar::chunk:hover {{"
            f"  background-color: {color};"
            f"}}"
        )
        layout.addWidget(self.progress)
        self.setToolTip(self._tooltip_text())

    def _apply_style(self, hovered: bool):
        if hovered:
            self.setStyleSheet(
                f"CategoryCard {{"
                f"  background: {theme.bg_card};"
                f"  border: 2px solid {self.color};"
                f"  border-radius: {theme.radius_lg};"
                f"}}"
            )
        else:
            self.setStyleSheet(
                f"CategoryCard {{"
                f"  background: {theme.bg_card};"
                f"  border: 1px solid {theme.border};"
                f"  border-radius: {theme.radius_lg};"
                f"}}"
            )

    def mousePressEvent(self, event):
        if self.on_click:
            self.on_click(self.result)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._apply_style(hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(hovered=False)
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
