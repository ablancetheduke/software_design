"""AssistantPetWidget — floating anime mascot with shadow/glow effects.

Extracted from main_window.py for reuse and testability.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from ...utils.theme import theme


class AssistantPetWidget(QWidget):
    """Floating anime-style assistant entry — draws shadow + glow.

    Emits:
        clicked: left mouse button pressed
        hovered_changed(bool): mouse entered/left
    """

    clicked = Signal()
    hovered_changed = Signal(bool)

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.hovered = False
        self.base_width = 128
        self.source_pixmap = QPixmap(image_path)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("我是你的 AI 助手，有什么可以帮助你的？")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        self.update_size(self.base_width)

    def update_size(self, width: int):
        self.base_width = width
        if self.source_pixmap.isNull():
            self.setFixedSize(width, width)
            return

        ratio = self.source_pixmap.height() / max(1, self.source_pixmap.width())
        self.setFixedSize(int(width * 1.22), int(width * ratio * 1.18))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if self.source_pixmap.isNull():
            painter.setPen(QColor(f"{theme.accent}"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "AI")
            return

        scale = 1.055 if self.hovered else 1.0
        draw_w = self.base_width * scale
        draw_h = draw_w * self.source_pixmap.height() / self.source_pixmap.width()

        x = (self.width() - draw_w) / 2
        y = self.height() - draw_h - 4

        # ── drop shadow ──
        shadow_rect = self._rectf(
            x + draw_w * 0.18, y + draw_h * 0.82,
            draw_w * 0.66, draw_h * 0.16,
        )
        for grow, alpha in ((2, 48), (9, 26), (18, 12)):
            painter.setBrush(QColor(94, 82, 70, alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                shadow_rect.adjusted(-grow, -grow * 0.35, grow, grow * 0.35)
            )

        # ── hover glow ──
        if self.hovered:
            glow_rect = self._rectf(
                x + draw_w * 0.08, y + draw_h * 0.06,
                draw_w * 0.84, draw_h * 0.88,
            )
            for i, alpha in enumerate((42, 24, 12)):
                painter.setBrush(QColor(111, 159, 152, alpha))
                painter.setPen(Qt.PenStyle.NoPen)
                grow = 10 + i * 12
                painter.drawEllipse(glow_rect.adjusted(-grow, -grow, grow, grow))

        painter.drawPixmap(
            self._rectf(x, y, draw_w, draw_h),
            self.source_pixmap,
            self._rectf(0, 0, self.source_pixmap.width(), self.source_pixmap.height()),
        )

    @staticmethod
    def _rectf(x, y, w, h):
        from PySide6.QtCore import QRectF
        return QRectF(x, y, w, h)

    def enterEvent(self, event):
        self.hovered = True
        self.hovered_changed.emit(True)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.hovered_changed.emit(False)
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
