"""Interactive Gantt timeline for graduate school applications.

Custom QWidget with paintEvent — same pattern as TrendChart in gpa_view.
Left panel: school names with count badges.
Right area: colored bars positioned by deadline date, hover tooltips.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

from ...models.graduate_application import GraduateApplication
from ...utils.theme import theme

# ═══════════════════════════════════════════════════════════════════════
#  Layout constants
# ═══════════════════════════════════════════════════════════════════════
LEFT_PANEL   = 160
ROW_HEIGHT   = 42
HEADER_H     = 42
BAR_H        = 26
BAR_R        = 7
PAD_X        = 12
PAD_Y        = 10
TL_LEFT      = LEFT_PANEL + 20
RIGHT_PAD    = 28
MIN_BAR_W    = 50

PANEL_BG     = QColor("#f8f7f4")
PANEL_LINE   = QColor("#e2e0d8")
GRID_LINE    = QColor(theme.border).lighter(110)
ROW_ALT      = QColor("#fafaf8")
ROW_HOVER    = QColor("#fff7ed")
TEXT_MAIN    = QColor(theme.fg)
TEXT_MUTED   = QColor(theme.fg_muted)
WARM_ACCENT  = QColor("#f59e0b")
TODAY_RED    = QColor("#ef4444")

# ═══════════════════════════════════════════════════════════════════════
#  Status → bar color
# ═══════════════════════════════════════════════════════════════════════
STATUS_COLORS: Dict[str, QColor] = {}

def _init_colors():
    if STATUS_COLORS:
        return
    STATUS_COLORS.update({
        "拟录取":     QColor("#10b981"),
        "入营通知":    QColor("#3b82f6"),
        "复试/面试":   QColor("#8b5cf6"),
        "已投递":      QColor("#f59e0b"),
        "材料准备中":  QColor("#f97316"),
        "已联系导师":  QColor("#14b8a6"),
        "了解中":      QColor("#d97706"),
        "拒绝":        QColor("#94a3b8"),
        "放弃":        QColor("#94a3b8"),
    })

def _bar_color(status: str) -> QColor:
    _init_colors()
    return STATUS_COLORS.get(status, QColor("#94a3b8"))


class GanttTimeline(QWidget):
    """Gantt chart for graduate applications — school rows + deadline bars."""

    bar_double_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(400)

        self._apps: List[GraduateApplication] = []
        self._grouped: Dict[str, List[GraduateApplication]] = {}
        self._school_order: List[str] = []
        self._school_rows: Dict[str, int] = {}
        self._school_bars: Dict[str, Tuple[float, float, str, str]] = {}

        self._d_start: date = date.today()
        self._d_end:   date = date.today() + timedelta(days=30)
        self._total_days: int = 30

        self._hover_row: int = -1
        self._hover_apps: List[GraduateApplication] = []
        self._hover_bar: bool = False

    # ── Public ─────────────────────────────────────────────────────

    def load_data(self, apps: List[GraduateApplication]):
        self._apps = sorted(apps, key=lambda a: a.deadline if a.deadline else "z")
        self._compute_range()
        self._group()
        h = int(self._content_height() + 40)
        self.setMinimumHeight(h)
        self.update()

    # ── Date helpers ───────────────────────────────────────────────

    def _compute_range(self):
        dates = []
        for a in self._apps:
            if a.deadline:
                try:
                    dates.append(datetime.strptime(a.deadline, "%Y-%m-%d").date())
                except ValueError:
                    pass
        if dates:
            self._d_start = min(dates) - timedelta(days=2)
            self._d_end   = max(dates) + timedelta(days=3)
        else:
            self._d_start = date.today() - timedelta(days=7)
            self._d_end   = date.today() + timedelta(days=30)
        self._total_days = max((self._d_end - self._d_start).days, 1)

    def _x_for_date(self, d: date) -> float:
        ratio = (d - self._d_start).days / self._total_days
        area_w = max(self.width() - TL_LEFT - RIGHT_PAD, 120)
        return TL_LEFT + ratio * area_w

    def _row_y(self, row: int) -> float:
        return HEADER_H + PAD_Y + row * ROW_HEIGHT

    def _total_rows(self) -> int:
        return len(self._school_order)

    def _content_height(self) -> float:
        return self._row_y(self._total_rows())

    # ── Group & compute bar positions ──────────────────────────────

    def _group(self):
        self._grouped = defaultdict(list)
        for a in self._apps:
            self._grouped[a.school].append(a)

        def sort_key(school: str):
            dates = [a.deadline for a in self._grouped[school] if a.deadline]
            return min(dates) if dates else "z"

        self._school_order = sorted(self._grouped.keys(), key=sort_key)
        self._school_bars.clear()
        self._school_rows.clear()

        for i, school in enumerate(self._school_order):
            self._school_rows[school] = i
            apps = self._grouped[school]
            d_dates = []
            for a in apps:
                if a.deadline:
                    try:
                        d_dates.append(datetime.strptime(a.deadline, "%Y-%m-%d").date())
                    except ValueError:
                        pass
            if d_dates:
                earliest = min(d_dates)
                latest   = max(d_dates)
                x1  = self._x_for_date(earliest)
                x2  = self._x_for_date(latest)
                bw  = max(x2 - x1, MIN_BAR_W)
                self._school_bars[school] = (x1, bw,
                    earliest.strftime("%m/%d"), latest.strftime("%m/%d"))
            else:
                self._school_bars[school] = (TL_LEFT, MIN_BAR_W, "", "")

    # ═══════════════════════════════════════════════════════════════
    #  PAINT
    # ═══════════════════════════════════════════════════════════════

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # ── Background ──
        p.fillRect(self.rect(), QColor(theme.bg_card))

        if not self._apps:
            self._draw_empty(p)
            p.end()
            return

        # ── Left panel background ──
        panel = QRectF(0, 0, LEFT_PANEL, h)
        p.fillRect(panel, PANEL_BG)

        self._draw_grid(p, w)
        self._draw_header(p, w)
        self._draw_row_backgrounds(p, w)
        self._draw_bars(p, w)
        self._draw_today(p)
        self._draw_tooltip(p)

        p.end()

    def _draw_empty(self, p: QPainter):
        p.setPen(QColor(theme.fg_muted))
        p.setFont(QFont("Microsoft YaHei", 14))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                   "暂无申请数据\n\n点击「从 Excel 导入」或「添加申请」开始记录")

    # ── Grid ──────────────────────────────────────────────────────

    def _draw_grid(self, p: QPainter, w: float):
        bottom = self._content_height()

        # Week grid (every 7 days)
        pen = QPen(GRID_LINE, 1, Qt.PenStyle.DotLine)
        p.setPen(pen)
        d = self._d_start
        while d <= self._d_end:
            x = int(self._x_for_date(d))
            p.drawLine(x, HEADER_H, x, int(bottom))
            d += timedelta(days=7)

        # Horizontal row lines — just subtle alternating
        # (done in _draw_row_backgrounds)

        # Strong left-panel separator
        p.setPen(QPen(PANEL_LINE, 1.5))
        p.drawLine(TL_LEFT, HEADER_H, TL_LEFT, int(bottom))

        # Bottom line
        p.setPen(QPen(QColor(theme.border), 1))
        p.drawLine(0, int(bottom), w, int(bottom))

    # ── Header ────────────────────────────────────────────────────

    def _draw_header(self, p: QPainter, w: float):
        # Header background
        header_bg = QRectF(0, 0, w, HEADER_H)
        p.fillRect(header_bg, QColor("#f1f0eb"))

        # Title in left panel
        p.setPen(TEXT_MUTED)
        title_font = QFont("Microsoft YaHei", 8, QFont.Weight.Bold)
        p.setFont(title_font)
        p.drawText(QRectF(PAD_X, 0, LEFT_PANEL - PAD_X, HEADER_H),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   "学校")

        # Month labels in timeline area
        month_font = QFont("Microsoft YaHei", 10, QFont.Weight.DemiBold)
        p.setFont(month_font)

        d = self._d_start.replace(day=1)
        while d <= self._d_end:
            if d >= self._d_start:
                x = self._x_for_date(d)
                # Alternating month background
                if d.month % 2 == 0:
                    p.fillRect(QRectF(x, 0, self._days_to_width(d), HEADER_H),
                               QColor("#ecebe5"))

                is_today_month = (d.year == date.today().year and
                                  d.month == date.today().month)
                p.setPen(QColor(theme.coral) if is_today_month else QColor(theme.fg))
                p.drawText(QRectF(x - 30, 0, 60, HEADER_H),
                           Qt.AlignmentFlag.AlignCenter,
                           f"{d.month}月")
                # Day markers below month
                p.setPen(QColor(theme.fg_muted))
                day_font = QFont("Consolas", 7)
                p.setFont(day_font)
                p.drawText(QRectF(x - 30, 18, 60, HEADER_H - 18),
                           Qt.AlignmentFlag.AlignCenter,
                           f"{d.day}日")
            # next month
            if d.month == 12:
                d = d.replace(year=d.year + 1, month=1)
            else:
                d = d.replace(month=d.month + 1)

    def _days_to_width(self, d: date) -> float:
        """How many pixels does this month span?"""
        if d.month == 12:
            nxt = d.replace(year=d.year + 1, month=1)
        else:
            nxt = d.replace(month=d.month + 1)
        return self._x_for_date(nxt) - self._x_for_date(d)

    # ── Row backgrounds ───────────────────────────────────────────

    def _draw_row_backgrounds(self, p: QPainter, w: float):
        for i in range(self._total_rows()):
            y = self._row_y(i)
            rect = QRectF(0, y - 3, w, ROW_HEIGHT)

            if i == self._hover_row:
                # Highlighted row
                p.fillRect(rect, ROW_HOVER)
                # Also highlight left panel
                p.fillRect(QRectF(0, y - 3, TL_LEFT, ROW_HEIGHT),
                           QColor("#ffedd5"))
            elif i % 2 == 0:
                # Subtle alternating
                p.fillRect(QRectF(TL_LEFT, y - 3, w - TL_LEFT, ROW_HEIGHT),
                           ROW_ALT)

    # ── Bars ──────────────────────────────────────────────────────

    def _draw_bars(self, p: QPainter, w: float):
        for i, school in enumerate(self._school_order):
            y = self._row_y(i)
            apps = self._grouped[school]
            count = len(apps)

            # ── School name ──
            p.setPen(QColor(theme.fg))
            name_font = QFont("Microsoft YaHei", 10, QFont.Weight.DemiBold)
            p.setFont(name_font)
            # Truncate if too long
            name = school
            fm = p.fontMetrics()
            max_name_w = LEFT_PANEL - PAD_X - 42
            if fm.horizontalAdvance(name) > max_name_w:
                name = fm.elidedText(name, Qt.TextElideMode.ElideRight, max_name_w)
            p.drawText(QRectF(PAD_X, y, max_name_w, ROW_HEIGHT),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                       name)

            # ── Count badge (pill) ──
            badge_w = max(28, fm.horizontalAdvance(str(count)) + 14)
            badge_x = LEFT_PANEL - badge_w - 6
            badge_rect = QRectF(badge_x, y + (ROW_HEIGHT - 20) / 2, badge_w, 20)
            badge_path = QPainterPath()
            badge_path.addRoundedRect(badge_rect, 10, 10)
            p.fillPath(badge_path, QBrush(QColor("#f0ebe2")))
            p.setPen(QColor(theme.fg_muted))
            badge_font = QFont("Microsoft YaHei", 8, QFont.Weight.Bold)
            p.setFont(badge_font)
            p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, str(count))

            # ── Bar ──
            bar = self._school_bars.get(school)
            if not bar:
                continue
            bar_x, bar_w, early_str, late_str = bar

            # Clamp
            bar_x = max(bar_x, TL_LEFT + 4)
            max_right = w - RIGHT_PAD
            if bar_x + bar_w > max_right:
                bar_w = max(max_right - bar_x, MIN_BAR_W)

            bar_rect = QRectF(bar_x, y + (ROW_HEIGHT - BAR_H) / 2, bar_w, BAR_H)

            c = _bar_color(apps[0].status)

            # ── Soft shadow ──
            shadow_rect = bar_rect.translated(0, 2)
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(shadow_rect, BAR_R, BAR_R)
            p.fillPath(shadow_path, QBrush(QColor(0, 0, 0, 18)))

            # ── Bar body ──
            grad = QLinearGradient(bar_rect.topLeft(), bar_rect.bottomLeft())
            grad.setColorAt(0.0, c.lighter(135))
            grad.setColorAt(0.48, c)
            grad.setColorAt(1.0, c.darker(112))

            bar_path = QPainterPath()
            bar_path.addRoundedRect(bar_rect, BAR_R, BAR_R)
            p.fillPath(bar_path, QBrush(grad))

            p.setPen(QPen(c.darker(118), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(bar_path)

            # ── Bar gloss (top highlight) ──
            gloss_rect = QRectF(bar_x + 2, bar_rect.y() + 2,
                                bar_w - 4, bar_rect.height() / 2)
            gloss_path = QPainterPath()
            gloss_path.addRoundedRect(gloss_rect, BAR_R - 1, BAR_R - 1)
            p.fillPath(gloss_path, QBrush(QColor(255, 255, 255, 42)))

            # ── Hover highlight ring ──
            if i == self._hover_row:
                p.setPen(QPen(c.lighter(150), 2.5))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(bar_path)

            # ── Individual college dots ──
            if count > 1:
                for a in apps:
                    if a.deadline:
                        try:
                            ad = datetime.strptime(a.deadline, "%Y-%m-%d").date()
                            mx = self._x_for_date(ad)
                            if bar_x + 4 <= mx <= bar_x + bar_w - 4:
                                p.setBrush(QBrush(QColor(255, 255, 255, 230)))
                                p.setPen(QPen(c.darker(130), 1))
                                p.drawEllipse(QPoint(int(mx), int(bar_rect.center().y())), 3, 3)
                        except ValueError:
                            pass

            # ── Date labels on bar ──
            date_font = QFont("Consolas", 8, QFont.Weight.Bold)
            p.setFont(date_font)
            p.setPen(QColor(255, 255, 255, 245))

            if early_str and bar_w > 80:
                p.drawText(QRectF(bar_x + 7, bar_rect.y(), 55, BAR_H),
                           Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                           early_str)
            if late_str and late_str != early_str and bar_w > 150:
                p.drawText(QRectF(bar_x + bar_w - 62, bar_rect.y(), 56, BAR_H),
                           Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                           late_str)

    # ── Today line ────────────────────────────────────────────────

    def _draw_today(self, p: QPainter):
        today = date.today()
        if today < self._d_start or today > self._d_end:
            return

        x = int(self._x_for_date(today))
        bottom = self._content_height()

        # Line
        p.setPen(QPen(TODAY_RED, 2, Qt.PenStyle.DashLine))
        p.drawLine(x, HEADER_H, x, int(bottom))

        # Top label
        p.setPen(TODAY_RED)
        label_font = QFont("Microsoft YaHei", 8, QFont.Weight.Bold)
        p.setFont(label_font)

        label_w, label_h = 44, 18
        label_rect = QRectF(x - label_w / 2, HEADER_H - label_h - 2, label_w, label_h)
        label_path = QPainterPath()
        label_path.addRoundedRect(label_rect, 4, 4)
        p.fillPath(label_path, QBrush(QColor("#fef2f2")))
        p.setPen(TODAY_RED)
        p.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, "今天")

        # Bottom dot
        p.setBrush(QBrush(TODAY_RED))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(x, int(bottom)), 4, 4)

    # ── Tooltip ───────────────────────────────────────────────────

    def _draw_tooltip(self, p: QPainter):
        apps = self._hover_apps
        if not apps or self._hover_row < 0:
            return

        school = apps[0].school
        lines = [f"{school}  ({len(apps)} 个项目)"]
        for a in apps[:8]:
            name = a.college or a.major or "(未命名)"
            dl = a.deadline or "无截止"
            lines.append(f"  {name}  —  {dl}")
        if len(apps) > 8:
            lines.append(f"  ... 还有 {len(apps) - 8} 个")

        p.setFont(QFont("Microsoft YaHei", 9))
        fm = p.fontMetrics()
        line_h = fm.height() + 3
        text_w = max(fm.horizontalAdvance(ln) for ln in lines) + 28
        text_h = len(lines) * line_h + 18

        pos = self.mapFromGlobal(QCursor.pos())
        tx = min(pos.x() + 16, self.width() - text_w - 10)
        ty = min(pos.y() - text_h // 2, self.height() - text_h - 10)
        ty = max(ty, 6)

        bg = QRectF(tx, ty, text_w, text_h)
        tooltip_path = QPainterPath()
        tooltip_path.addRoundedRect(bg, 10, 10)

        # Shadow behind tooltip
        shadow = bg.translated(2, 3)
        sp = QPainterPath()
        sp.addRoundedRect(shadow, 10, 10)
        p.fillPath(sp, QBrush(QColor(0, 0, 0, 40)))

        # Tooltip background
        p.fillPath(tooltip_path, QBrush(QColor(30, 30, 42, 245)))
        p.setPen(QPen(QColor(theme.primary_light), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(tooltip_path)

        # Text
        for j, line in enumerate(lines):
            is_header = (j == 0)
            p.setPen(QColor("#fbbf24") if is_header else QColor("#d4d4d8"))
            f = QFont("Microsoft YaHei", 9, QFont.Weight.Bold if is_header else QFont.Weight.Normal)
            p.setFont(f)
            p.drawText(QRectF(tx + 14, ty + 9 + j * line_h, text_w - 28, line_h),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                       line)

    # ═══════════════════════════════════════════════════════════════
    #  MOUSE
    # ═══════════════════════════════════════════════════════════════

    def _row_at(self, y: float) -> int:
        row = int((y - HEADER_H - PAD_Y) / ROW_HEIGHT)
        return row if 0 <= row < self._total_rows() else -1

    def mouseMoveEvent(self, event: QMouseEvent):
        row = self._row_at(event.position().y())
        if row != self._hover_row:
            self._hover_row = row
            if row >= 0:
                school = self._school_order[row]
                self._hover_apps = self._grouped.get(school, [])
            else:
                self._hover_apps = []
            self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        row = self._row_at(event.position().y())
        if row >= 0:
            school = self._school_order[row]
            apps = self._grouped.get(school, [])
            if apps:
                self.bar_double_clicked.emit(apps[0].app_id)

    def leaveEvent(self, event):
        self._hover_row = -1
        self._hover_apps = []
        self.update()

    # ── Resize ───────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._apps:
            self._group()
            self.setMinimumHeight(int(self._content_height() + 40))
            self.update()
