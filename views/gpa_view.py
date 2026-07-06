"""Grade trend page: GPA, weighted average, and arithmetic average."""

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..database.repositories.course_repo import CourseRepository
from ..services.gpa_calculator import (
    calculate_grade_overview,
    calculate_semester_trend,
)
from ..utils.constants import SEMESTERS
from ..utils.theme import theme
from .widgets.stat_card import StatCard


class TrendChart(QWidget):
    """Qt-painted line chart for semester grade changes.

    Series:
      - 加权平均 (teal)    — percentage scale, dynamic min/max
      - 算术平均 (purple)  — percentage scale, shares same Y
      - 绩点 (gold)        — 0–4 scale, separate Y axis on right
    """

    GPA_MIN, GPA_MAX = 0.0, 4.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        self.trend: list[dict] = []
        self.hover_index = -1
        self.setMouseTracking(True)

    def set_trend(self, trend: list[dict]):
        self.trend = trend
        self.hover_index = -1
        self.update()

    # ── dynamic range helpers ─────────────────────────────────────

    @staticmethod
    def _percent_range(trend: list[dict]) -> tuple[float, float]:
        """Compute a sensible Y range for percentage-scale series."""
        values = []
        for item in trend:
            for key in ("weighted_average", "arithmetic_average"):
                if key in item and item[key] > 0:
                    values.append(item[key])
        if not values:
            return 60.0, 100.0
        lo = min(values)
        hi = max(values)
        # Add 5% padding; floor to nearest 5
        lo = max(0.0, (int(lo // 5) * 5) - 5)
        hi = min(100.0, (int((hi + 4) // 5) * 5) + 5)
        return lo, hi

    # ── mouse interaction ─────────────────────────────────────────

    def mouseMoveEvent(self, event):
        if not self.trend:
            return
        points = self._x_points()
        x = event.position().x()
        self.hover_index = min(
            range(len(points)), key=lambda i: abs(points[i] - x)
        )
        self.update()

    def leaveEvent(self, event):
        self.hover_index = -1
        self.update()
        super().leaveEvent(event)

    # ── painting ──────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(theme.bg_card))

        if not self.trend:
            painter.setPen(QColor(theme.fg_muted))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "导入课程成绩后，这里会显示成绩变化趋势",
            )
            return

        left, top, right, bottom = 54, 28, 54, 54
        chart_w = max(1, self.width() - left - right)
        chart_h = max(1, self.height() - top - bottom)
        plot_left = left
        plot_top = top
        plot_bottom = top + chart_h

        # grid lines (percentage scale)
        painter.setPen(QPen(QColor(theme.border), 1))
        for i in range(5):
            y = plot_top + i * chart_h / 4
            painter.drawLine(
                plot_left, int(y), plot_left + chart_w, int(y)
            )

        # percentage range
        pct_lo, pct_hi = self._percent_range(self.trend)

        self._draw_series(
            painter, "weighted_average", QColor(theme.accent),
            pct_lo, pct_hi, left, top, chart_w, chart_h,
        )
        self._draw_series(
            painter, "arithmetic_average", QColor(theme.purple),
            pct_lo, pct_hi, left, top, chart_w, chart_h,
        )
        self._draw_series(
            painter, "gpa", QColor(theme.gold),
            self.GPA_MIN, self.GPA_MAX, left, top, chart_w, chart_h,
        )

        # X-axis labels
        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.setPen(QColor(f"{theme.fg_faint}"))
        for i, item in enumerate(self.trend):
            x = self._x_for_index(i, left, chart_w)
            painter.drawText(
                int(x - 38), plot_bottom + 22, 76, 20,
                Qt.AlignmentFlag.AlignCenter, item["semester"],
            )

        self._draw_legend(painter)
        if 0 <= self.hover_index < len(self.trend):
            self._draw_hover(
                painter, self.hover_index, left, top, chart_w, chart_h,
                pct_lo, pct_hi,
            )

    def _x_points(self):
        left, right = 54, 54
        chart_w = max(1, self.width() - left - right)
        return [
            self._x_for_index(i, left, chart_w)
            for i in range(len(self.trend))
        ]

    def _x_for_index(self, index, left, chart_w):
        if len(self.trend) == 1:
            return left + chart_w / 2
        return left + index * chart_w / (len(self.trend) - 1)

    @staticmethod
    def _y_for_value(value, minimum, maximum, top, chart_h):
        if maximum == minimum:
            return top + chart_h / 2
        ratio = (value - minimum) / (maximum - minimum)
        ratio = max(0.0, min(1.0, ratio))
        return top + chart_h * (1 - ratio)

    def _draw_series(
        self, painter, key, color, y_min, y_max,
        left, top, chart_w, chart_h,
    ):
        points = []
        for i, item in enumerate(self.trend):
            val = item.get(key, 0)
            if val <= 0 and key in ("weighted_average", "arithmetic_average"):
                continue
            x = self._x_for_index(i, left, chart_w)
            y = self._y_for_value(val, y_min, y_max, top, chart_h)
            points.append(QPointF(x, y))

        if len(points) < 2:
            return

        painter.setPen(QPen(color, 3))
        for start, end in zip(points, points[1:]):
            painter.drawLine(start, end)

        painter.setBrush(color)
        painter.setPen(QPen(QColor(theme.bg_card), 2))
        for point in points:
            painter.drawEllipse(point, 5, 5)

    @staticmethod
    def _draw_legend(painter):
        items = [
            ("加权平均", theme.accent),
            ("算术平均", theme.purple),
            ("绩点", theme.gold),
        ]
        x = 66
        painter.setFont(QFont("Microsoft YaHei", 9))
        for text, color in items:
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x, 16, 9, 9)
            painter.setPen(QColor(theme.fg))
            painter.drawText(x + 14, 25, text)
            x += 92

    def _draw_hover(
        self, painter, index, left, top, chart_w, chart_h,
        pct_lo, pct_hi,
    ):
        item = self.trend[index]
        x = self._x_for_index(index, left, chart_w)
        painter.setPen(QPen(QColor("#aaa197"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(x), top, int(x), top + chart_h)

        text = (
            f"{item['semester']}\n"
            f"绩点 {item['gpa']:.2f}\n"
            f"加权 {item['weighted_average']:.2f}\n"
            f"算术 {item['arithmetic_average']:.2f}"
        )
        box_w, box_h = 128, 86
        box_x = int(min(max(8, x + 12), self.width() - box_w - 8))
        box_y = 44
        painter.setBrush(QColor(theme.bg_card))
        painter.setPen(QPen(QColor(theme.accent), 1))
        painter.drawRoundedRect(box_x, box_y, box_w, box_h, 8, 8)
        painter.setPen(QColor(theme.fg))
        painter.drawText(box_x + 10, box_y + 18, text)


class GpaView(QWidget):
    """GPA calculation and trend analysis page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.course_repo = CourseRepository()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("成绩变化分析")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {theme.fg};"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "按学期展示绩点、加权平均分和算术平均分的变化。"
        )
        subtitle.setStyleSheet(f"color: {theme.fg_muted};")
        layout.addWidget(subtitle)

        cards = QHBoxLayout()
        self.gpa_card = StatCard("绩点", "0.00", theme.gold)
        self.weighted_card = StatCard("加权平均分", "0.00", theme.accent)
        self.arithmetic_card = StatCard("算术平均分", "0.00", theme.purple)
        cards.addWidget(self.gpa_card)
        cards.addWidget(self.weighted_card)
        cards.addWidget(self.arithmetic_card)
        layout.addLayout(cards)

        self.chart = TrendChart()
        self.chart.setStyleSheet("border-radius: 8px;")
        layout.addWidget(self.chart)

        self.semester_table = QTableWidget()
        self.semester_table.setColumnCount(5)
        self.semester_table.setHorizontalHeaderLabels(
            ["学期", "绩点", "加权平均分", "算术平均分", "课程数"]
        )
        self.semester_table.setAlternatingRowColors(True)
        self.semester_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.semester_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.semester_table.verticalHeader().setVisible(False)
        self.semester_table.setStyleSheet(
            f"QTableWidget {{ background-color: {theme.bg_card}; "
            f"color: {theme.fg}; gridline-color: {theme.border}; }}"
            f"QHeaderView::section {{ background-color: {theme.nav_hover_bg}; "
            f"color: {theme.fg}; padding: 6px; border: none; }}"
            f"QTableWidget::item:selected {{ background-color: {theme.bg_active}; "
            f"color: {theme.fg}; }}"
        )
        layout.addWidget(self.semester_table)

        self.refresh()

    def refresh(self):
        courses = self.course_repo.get_all()
        overview = calculate_grade_overview(courses)
        trend = self._sort_trend(calculate_semester_trend(courses))

        self.gpa_card.value_label.setText(f"{overview['gpa']:.2f}")
        self.weighted_card.value_label.setText(
            f"{overview['weighted_average']:.2f}"
        )
        self.arithmetic_card.value_label.setText(
            f"{overview['arithmetic_average']:.2f}"
        )
        self.chart.set_trend(trend)
        self._update_table(trend)

    def _update_table(self, trend):
        self.semester_table.setRowCount(len(trend))
        for row, item in enumerate(trend):
            values = [
                item["semester"],
                f"{item['gpa']:.2f}",
                f"{item['weighted_average']:.2f}",
                f"{item['arithmetic_average']:.2f}",
                str(item["course_count"]),
            ]
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.semester_table.setItem(row, col, table_item)

    @staticmethod
    def _sort_trend(trend):
        sem_order = {
            semester: i for i, semester in enumerate(SEMESTERS)
        }
        return sorted(
            trend,
            key=lambda item: sem_order.get(item["semester"], 99),
        )
