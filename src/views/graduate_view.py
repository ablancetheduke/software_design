"""Graduate school application tracking page."""

from datetime import date, datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..database.repositories.graduate_application_repo import (
    GraduateApplicationRepository,
)
from ..models.graduate_application import (
    GRADUATE_STATUSES,
    GraduateApplication,
)
from ..services.graduate_importer import import_from_excel
from ..utils.theme import theme
from .dialogs.graduate_dialog import GraduateDialog
from .widgets.gantt_timeline import GanttTimeline
from .widgets.record_table import RecordTable

# ── Status groups for card summaries ──
ACTIVE_STATUSES = {"已联系导师", "材料准备中", "已投递", "入营通知", "复试/面试"}
INTERVIEW_STATUSES = {"复试/面试"}
POSITIVE_STATUSES = {"拟录取"}
DONE_STATUSES = {"拒绝", "放弃", "拟录取"}


def reminder_text_for_application(
    app: GraduateApplication, today: date | None = None
) -> str:
    current_day = today or date.today()
    if app.status in DONE_STATUSES:
        return ""

    days_to_deadline = _days_between(current_day, app.deadline)
    if days_to_deadline is not None:
        if days_to_deadline < 0:
            return "已过截止"
        if 0 <= days_to_deadline <= 3:
            return f"{days_to_deadline} 天内截止"
        if 4 <= days_to_deadline <= 7:
            return "一周内截止"

    days_since_apply = _days_between(app.apply_date, current_day)
    if (
        days_since_apply is not None
        and app.status == "已投递"
        and days_since_apply >= 10
    ):
        return f"已投递 {days_since_apply} 天，建议跟进"

    if app.material_count < 3 and app.status in {
        "材料准备中", "已投递", "入营通知", "复试/面试"
    }:
        return "材料准备未完成"

    if app.interview_date and not app.has_interview_notes:
        return "⚠ 建议记录复试复盘"

    return "正常"


def _days_between(start, end):
    try:
        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d").date()
        if isinstance(end, str):
            end = datetime.strptime(end, "%Y-%m-%d").date()
        return (end - start).days
    except (TypeError, ValueError):
        return None


class SummaryCard(QFrame):
    """Compact dashboard card for graduate application statistics."""

    def __init__(self, title: str, value: str, caption: str, color: str,
                 parent=None):
        super().__init__(parent)
        self.color = color
        self.setObjectName("GradSummaryCard")
        self.setMinimumHeight(86)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {color};"
        )
        layout.addWidget(self.value_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {theme.fg};"
        )
        layout.addWidget(title_label)

        cap = QLabel(caption)
        cap.setStyleSheet(f"font-size: 11px; color: {theme.fg_muted};")
        layout.addWidget(cap)

    def _apply_style(self):
        self.setStyleSheet(
            f"#GradSummaryCard {{ background: {theme.bg_card}; "
            f"border: 1px solid {theme.border}; "
            f"border-left: 4px solid {self.color}; border-radius: 8px; }}"
        )


class GraduateView(QWidget):
    """Graduate school application tracker — 升学规划."""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = GraduateApplicationRepository()
        self._setup_ui()
        self.refresh()

    # ── UI construction ──────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # ── Header ─────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("GraduateHeader")
        header.setStyleSheet(
            f"#GraduateHeader {{ background: {theme.bg_card}; "
            f"border: 1px solid {theme.border}; border-radius: 8px; }}"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 14, 18, 14)

        title_box = QVBoxLayout()
        title = QLabel("🎓 升学规划")
        title.setStyleSheet(theme.section_title_style(22))
        subtitle = QLabel(
            "追踪夏令营/预推免/统考申请进度、导师联系状态和材料准备情况"
        )
        subtitle.setStyleSheet(
            f"font-size: 13px; color: {theme.fg_muted};"
        )
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        hl.addLayout(title_box)
        hl.addStretch()

        self.import_btn = QPushButton("📥 从 Excel 导入")
        self.import_btn.setStyleSheet(theme.subtle_btn_style())
        self.import_btn.clicked.connect(self._import_excel)
        hl.addWidget(self.import_btn)

        self.add_btn = QPushButton("+ 添加申请")
        self.add_btn.setStyleSheet(theme.primary_btn_style())
        self.add_btn.clicked.connect(self._add)
        hl.addWidget(self.add_btn)
        layout.addWidget(header)

        # ── Summary cards ──────────────────────────────────────────
        cards = QGridLayout()
        cards.setSpacing(10)
        self.total_card = SummaryCard(
            "全部申请", "0", "当前记录总数", theme.accent
        )
        self.active_card = SummaryCard(
            "进行中", "0", "联系导师 / 材料 / 已投递 / 入营 / 复试",
            theme.purple,
        )
        self.interview_card = SummaryCard(
            "复试阶段", "0", "等待或已完成复试", theme.gold
        )
        self.offer_card = SummaryCard(
            "拟录取", "0", "已拿到 offer", theme.green
        )
        self.todo_card = SummaryCard(
            "待处理", "0", "临期或需跟进", theme.orange
        )
        for col, card in enumerate([
            self.total_card, self.active_card, self.interview_card,
            self.offer_card, self.todo_card,
        ]):
            cards.addWidget(card, 0, col)
        layout.addLayout(cards)

        # ── View toggle + Toolbar ──────────────────────────────────
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("GraduateToolbar")
        toolbar_frame.setStyleSheet(
            f"#GraduateToolbar {{ background: {theme.bg_card}; "
            f"border: 1px solid {theme.border}; border-radius: 8px; }}"
        )
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(12, 10, 12, 10)
        toolbar.setSpacing(8)

        # View toggle buttons
        self.table_view_btn = QPushButton("📊 表格视图")
        self.table_view_btn.setCheckable(True)
        self.table_view_btn.setChecked(True)
        self.table_view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.table_view_btn.clicked.connect(lambda: self._switch_view("table"))

        self.timeline_view_btn = QPushButton("📅 时间轴视图")
        self.timeline_view_btn.setCheckable(True)
        self.timeline_view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeline_view_btn.clicked.connect(lambda: self._switch_view("timeline"))

        for btn in [self.table_view_btn, self.timeline_view_btn]:
            btn.setStyleSheet(
                f"QPushButton {{ padding: 6px 14px; border: 1px solid {theme.border}; "
                f"border-radius: {theme.radius_sm}; font-size: 12px; "
                f"color: {theme.fg_muted}; background: transparent; }}"
                f"QPushButton:checked {{ background: {theme.primary_glow}; "
                f"color: {theme.primary_dark}; border-color: {theme.primary}; "
                f"font-weight: 600; }}"
                f"QPushButton:hover {{ border-color: {theme.primary_light}; }}"
            )

        toolbar.addWidget(self.table_view_btn)
        toolbar.addWidget(self.timeline_view_btn)
        toolbar.addSpacing(16)

        toolbar.addWidget(QLabel("状态"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部")
        self.status_filter.addItems(GRADUATE_STATUSES)
        self.status_filter.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        toolbar.addWidget(QLabel("批次"))
        self.batch_filter = QComboBox()
        self.batch_filter.addItem("全部")
        self.batch_filter.addItems([
            "夏令营", "预推免", "九月推免", "统考", "申请考核", "出国申请",
        ])
        self.batch_filter.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self.batch_filter)

        toolbar.addStretch()

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._delete)
        toolbar.addWidget(self.delete_btn)
        layout.addWidget(toolbar_frame)

        # ── Alert bar ──────────────────────────────────────────────
        self.alert_label = QLabel()
        self.alert_label.setWordWrap(True)
        self.alert_label.setStyleSheet(
            f"QLabel {{ {theme.warning_infobar_style()} }}"
        )
        layout.addWidget(self.alert_label)

        # ── Stacked: table + timeline placeholder ──────────────────
        self.view_stack = QStackedWidget()

        # --- Table view ---
        table_wrapper = QWidget()
        tl = QVBoxLayout(table_wrapper)
        tl.setContentsMargins(0, 0, 0, 0)

        self.table = RecordTable()
        self.table.set_columns(
            ["ID", "学校", "学院/项目", "专业方向", "学位", "批次", "状态",
             "报名日期", "截止日期", "导师", "导师联系", "材料准备",
             "复试复盘", "提醒", "备注"],
            id_column=0,
        )
        self.table.setStyleSheet(theme.table_style())
        self.table.row_double_clicked_signal.connect(self._edit_by_id)
        tl.addWidget(self.table)
        self.view_stack.addWidget(table_wrapper)  # index 0

        # --- Timeline view ---
        self.timeline = GanttTimeline()

        # Wrap in scroll area for schools with many entries
        timeline_scroll = QScrollArea()
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setWidget(self.timeline)
        timeline_scroll.setFrameShape(QFrame.Shape.NoFrame)
        timeline_scroll.setStyleSheet(
            f"QScrollArea {{ background: {theme.bg_card}; border: none; }}"
            f"QScrollBar:vertical {{ background: {theme.bg}; width: 8px; }}"
            f"QScrollBar::handle:vertical {{ background: {theme.border}; border-radius: 4px; }}"
            f"QScrollBar::handle:vertical:hover {{ background: {theme.fg_muted}; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
        )

        self.timeline.bar_double_clicked.connect(self._edit_by_id)
        self.view_stack.addWidget(timeline_scroll)  # index 1

        layout.addWidget(self.view_stack, 1)

    # ── View switching ───────────────────────────────────────────────

    def _switch_view(self, view: str):
        if view == "table":
            self.view_stack.setCurrentIndex(0)
            self.table_view_btn.setChecked(True)
            self.timeline_view_btn.setChecked(False)
        else:
            self.view_stack.setCurrentIndex(1)
            self.table_view_btn.setChecked(False)
            self.timeline_view_btn.setChecked(True)

    # ── Data & refresh ────────────────────────────────────────────────

    def refresh(self):
        apps = self._filtered_apps()
        self._refresh_cards()
        self._refresh_alerts()

        rows = []
        for app in apps:
            rows.append([
                app.app_id,
                app.school,
                app.college,
                app.major,
                app.degree_type,
                app.batch,
                app.status,
                app.apply_date,
                app.deadline,
                app.advisor,
                app.advisor_status,
                self._material_text(app),
                self._interview_text(app),
                self._reminder_text(app),
                app.note,
            ])
        self.table.load_data(rows)

        # Sync timeline
        if hasattr(self, "timeline"):
            self.timeline.load_data(apps)

    def _filtered_apps(self):
        apps = self.repo.get_all()
        status = (
            self.status_filter.currentText()
            if hasattr(self, "status_filter") else "全部"
        )
        batch = (
            self.batch_filter.currentText()
            if hasattr(self, "batch_filter") else "全部"
        )
        if status != "全部":
            apps = [a for a in apps if a.status == status]
        if batch != "全部":
            apps = [a for a in apps if a.batch == batch]
        return apps

    def _refresh_cards(self):
        apps = self.repo.get_all()
        self.total_card.value_label.setText(str(len(apps)))
        self.active_card.value_label.setText(
            str(sum(1 for a in apps if a.status in ACTIVE_STATUSES))
        )
        self.interview_card.value_label.setText(
            str(sum(1 for a in apps if a.status in INTERVIEW_STATUSES))
        )
        self.offer_card.value_label.setText(
            str(sum(1 for a in apps if a.status in POSITIVE_STATUSES))
        )
        self.todo_card.value_label.setText(
            str(sum(1 for a in apps if self._needs_attention(a)))
        )

    def _refresh_alerts(self):
        apps = self.repo.get_all()
        alerts = [
            f"{a.school} - {a.college or a.major}: {self._reminder_text(a)}"
            for a in apps
            if self._needs_attention(a)
        ]
        if alerts:
            self.alert_label.setText("⏰ 近期提醒：" + "；".join(alerts[:4]))
        else:
            self.alert_label.setText(
                "✅ 近期提醒：暂无临近截止或需要跟进的申请。"
            )

    # ── Import ──────────────────────────────────────────────────────

    def _import_excel(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Excel 文件",
            "",
            "Excel 文件 (*.xlsx *.xls)",
        )
        if not filepath:
            return

        result = import_from_excel(filepath)

        msg_parts = []
        if result["added"]:
            msg_parts.append(f"✅ 新增 {result['added']} 条")
        if result["updated"]:
            msg_parts.append(f"🔄 更新 {result['updated']} 条")
        if result["skipped"]:
            msg_parts.append(f"⏭️ 跳过 {result['skipped']} 条（空行）")

        if result["errors"]:
            msg_parts.append(
                f"\n⚠️ 错误:\n" + "\n".join(result["errors"][:5])
            )

        if not msg_parts:
            msg_parts.append("没有可导入的数据。")

        QMessageBox.information(
            self,
            "导入结果",
            "\n".join(msg_parts),
        )

        self.refresh()
        self.data_changed.emit()

    # ── CRUD actions ──────────────────────────────────────────────────

    def _add(self):
        dialog = GraduateDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            app = dialog.get_application()
            if not app.school:
                QMessageBox.warning(self, "提示", "学校名称不能为空。")
                return
            self.repo.add(app)
            self.refresh()
            self.data_changed.emit()

    def _edit(self):
        app_id = self.table.get_selected_id()
        if app_id < 0:
            QMessageBox.warning(self, "提示", "请先选择一条申请记录。")
            return
        self._edit_by_id(app_id)

    def _edit_by_id(self, app_id: int):
        app = self.repo.get_by_id(app_id)
        if not app:
            return
        dialog = GraduateDialog(app, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_application()
            if not updated.school:
                QMessageBox.warning(self, "提示", "学校名称不能为空。")
                return
            self.repo.update(updated)
            self.refresh()
            self.data_changed.emit()

    def _delete(self):
        app_id = self.table.get_selected_id()
        if app_id < 0:
            QMessageBox.warning(self, "提示", "请先选择一条申请记录。")
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定删除这条升学申请记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete(app_id)
            self.refresh()
            self.data_changed.emit()

    # ── Helpers ───────────────────────────────────────────────────────

    def _needs_attention(self, app: GraduateApplication) -> bool:
        return self._reminder_text(app) not in ("", "正常")

    def _reminder_text(self, app: GraduateApplication) -> str:
        return reminder_text_for_application(app)

    @staticmethod
    def _material_text(app: GraduateApplication) -> str:
        total = 6
        done = app.material_count
        detail = app.material_text
        return f"{done}/{total}  {detail}"

    @staticmethod
    def _interview_text(app: GraduateApplication) -> str:
        if app.interview_date:
            if app.has_interview_notes:
                preview = app.interview_notes[:30]
                return f"{app.interview_date} ✓ {preview}..."
            return f"{app.interview_date} ⚠ 待复盘"
        if app.status in INTERVIEW_STATUSES:
            return "待复试/待记录"
        if app.status in POSITIVE_STATUSES | {"拒绝"}:
            return "未记录"
        return ""

    @staticmethod
    def _days_between(start, end):
        return _days_between(start, end)
