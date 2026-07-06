"""Internship application tracking page."""

from datetime import date, datetime

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..database.repositories.internship_application_repo import InternshipApplicationRepository
from ..models.internship_application import InternshipApplication
from ..utils.theme import theme
from .dialogs.internship_dialog import (
    APPLICATION_DIRECTIONS, APPLICATION_STATUSES, InternshipDialog,
)
from .widgets.record_table import RecordTable


ACTIVE_STATUSES = {"已投递", "笔试", "一面", "二面"}
INTERVIEW_STATUSES = {"笔试", "一面", "二面"}
INTERVIEW_DONE_STATUSES = {"Offer", "拒绝", "放弃", "已投递", "待投递"}
DONE_STATUSES = {"Offer", "拒绝", "放弃"}


class SummaryCard(QFrame):
    """Compact dashboard card for application statistics."""

    def __init__(self, title: str, value: str, caption: str, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.setObjectName("InternshipSummaryCard")
        self.setMinimumHeight(86)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        layout.addWidget(self.value_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {theme.fg};")
        layout.addWidget(title_label)

        caption_label = QLabel(caption)
        caption_label.setStyleSheet(f"font-size: 11px; color: {theme.fg_muted};")
        layout.addWidget(caption_label)

    def _apply_style(self):
        self.setStyleSheet(
            f"#InternshipSummaryCard {{ background: {theme.bg_card}; "
            f"border: 1px solid {theme.border}; "
            f"border-left: 4px solid {self.color}; border-radius: 8px; }}"
        )


class InternshipView(QWidget):
    """Internship application tracker."""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = InternshipApplicationRepository()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("InternshipHeader")
        header.setStyleSheet(
            f"#InternshipHeader {{ background: {theme.bg_card}; "
            f"border: 1px solid {theme.border}; border-radius: 8px; }}"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)

        title_box = QVBoxLayout()
        title = QLabel("实习投递追踪")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {theme.fg};")
        subtitle = QLabel("集中记录岗位状态、截止日期、面试准备和后续跟进事项")
        subtitle.setStyleSheet(f"font-size: 13px; color: {theme.fg_muted};")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.add_btn = QPushButton("+ 添加投递")
        self.add_btn.setStyleSheet(theme.primary_btn_style())
        self.add_btn.clicked.connect(self._add)
        header_layout.addWidget(self.add_btn)
        layout.addWidget(header)

        cards = QGridLayout()
        cards.setSpacing(10)
        self.total_card = SummaryCard("全部投递", "0", "当前记录总数", theme.accent)
        self.active_card = SummaryCard("进行中", "0", "已投递/笔试/面试", theme.purple)
        self.interview_card = SummaryCard("面试阶段", "0", "笔试、一面、二面", theme.gold)
        self.offer_card = SummaryCard("Offer", "0", "已拿到结果", theme.green)
        self.todo_card = SummaryCard("待处理", "0", "临期或需跟进", theme.orange)
        for col, card in enumerate([
            self.total_card,
            self.active_card,
            self.interview_card,
            self.offer_card,
            self.todo_card,
        ]):
            cards.addWidget(card, 0, col)
        layout.addLayout(cards)

        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("InternshipToolbar")
        toolbar_frame.setStyleSheet(
            f"#InternshipToolbar {{ background: {theme.bg_card}; "
            f"border: 1px solid {theme.border}; border-radius: 8px; }}"
        )
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(12, 10, 12, 10)
        toolbar.setSpacing(8)

        toolbar.addWidget(QLabel("状态"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部")
        self.status_filter.addItems(APPLICATION_STATUSES)
        self.status_filter.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self.status_filter)

        toolbar.addWidget(QLabel("方向"))
        self.direction_filter = QComboBox()
        self.direction_filter.addItem("全部")
        self.direction_filter.addItems(APPLICATION_DIRECTIONS)
        self.direction_filter.currentTextChanged.connect(self.refresh)
        toolbar.addWidget(self.direction_filter)

        toolbar.addStretch()

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._delete)
        toolbar.addWidget(self.delete_btn)
        layout.addWidget(toolbar_frame)

        self.alert_label = QLabel()
        self.alert_label.setWordWrap(True)
        self.alert_label.setStyleSheet(f"QLabel {{ {theme.warning_infobar_style()} }}")
        layout.addWidget(self.alert_label)

        self.table = RecordTable()
        self.table.set_columns(
            ["ID", "公司", "岗位", "方向", "状态", "投递日期", "截止日期",
             "准备度", "面试复盘", "提醒", "备注"],
            id_column=0,
        )
        self.table.setStyleSheet(theme.table_style())
        self.table.row_double_clicked_signal.connect(self._edit_by_id)
        layout.addWidget(self.table, 1)

    def refresh(self):
        apps = self._filtered_apps()
        self._refresh_cards()
        self._refresh_alerts()

        rows = []
        for app in apps:
            rows.append([
                app.app_id, app.company, app.position, app.direction,
                app.status, app.apply_date, app.deadline,
                self._prep_text(app),
                self._interview_text(app),
                self._reminder_text(app),
                app.note,
            ])
        self.table.load_data(rows)

    def _filtered_apps(self):
        apps = self.repo.get_all()
        status = self.status_filter.currentText() if hasattr(self, "status_filter") else "全部"
        direction = self.direction_filter.currentText() if hasattr(self, "direction_filter") else "全部"

        if status != "全部":
            apps = [app for app in apps if app.status == status]
        if direction != "全部":
            apps = [app for app in apps if app.direction == direction]
        return apps

    def _refresh_cards(self):
        apps = self.repo.get_all()
        self.total_card.value_label.setText(str(len(apps)))
        self.active_card.value_label.setText(str(sum(1 for app in apps if app.status in ACTIVE_STATUSES)))
        self.interview_card.value_label.setText(str(sum(1 for app in apps if app.status in INTERVIEW_STATUSES)))
        self.offer_card.value_label.setText(str(sum(1 for app in apps if app.status == "Offer")))
        self.todo_card.value_label.setText(str(sum(1 for app in apps if self._needs_attention(app))))

    def _refresh_alerts(self):
        apps = self.repo.get_all()
        alerts = [
            f"{app.company} - {app.position}: {self._reminder_text(app)}"
            for app in apps
            if self._needs_attention(app)
        ]
        if alerts:
            self.alert_label.setText("近期提醒：" + "；".join(alerts[:4]))
        else:
            self.alert_label.setText("近期提醒：暂无临近截止或需要跟进的投递。")

    def _add(self):
        dialog = InternshipDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            app = dialog.get_application()
            if not app.company or not app.position:
                QMessageBox.warning(self, "提示", "公司和岗位不能为空。")
                return
            self.repo.add(app)
            self.refresh()
            self.data_changed.emit()

    def _edit(self):
        app_id = self.table.get_selected_id()
        if app_id < 0:
            QMessageBox.warning(self, "提示", "请先选择一条投递记录。")
            return
        self._edit_by_id(app_id)

    def _edit_by_id(self, app_id: int):
        app = self.repo.get_by_id(app_id)
        if not app:
            return
        dialog = InternshipDialog(app, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_application()
            if not updated.company or not updated.position:
                QMessageBox.warning(self, "提示", "公司和岗位不能为空。")
                return
            self.repo.update(updated)
            self.refresh()
            self.data_changed.emit()

    def _delete(self):
        app_id = self.table.get_selected_id()
        if app_id < 0:
            QMessageBox.warning(self, "提示", "请先选择一条投递记录。")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定删除这条投递记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete(app_id)
            self.refresh()
            self.data_changed.emit()

    def _needs_attention(self, app: InternshipApplication) -> bool:
        return self._reminder_text(app) not in ("", "正常")

    def _reminder_text(self, app: InternshipApplication) -> str:
        if app.status in DONE_STATUSES:
            return ""

        days_to_deadline = self._days_between(date.today(), app.deadline)
        if days_to_deadline is not None:
            if days_to_deadline < 0 and app.status == "待投递":
                return "已过截止"
            if 0 <= days_to_deadline <= 3:
                return f"{days_to_deadline} 天内截止"
            if 4 <= days_to_deadline <= 7:
                return "一周内截止"

        days_since_apply = self._days_between(app.apply_date, date.today())
        if days_since_apply is not None and app.status == "已投递" and days_since_apply >= 7:
            return f"已投递 {days_since_apply} 天，建议跟进"

        if app.prep_count < 2 and app.status in INTERVIEW_STATUSES:
            return "面试准备未完成"

        # interview happened (has date) but no notes → prompt review
        if app.interview_date and not app.has_interview_notes:
            return "⚠ 建议记录面试复盘"

        return "正常"

    @staticmethod
    def _interview_text(app: InternshipApplication) -> str:
        """Show interview tracking status in the table."""
        if app.interview_date:
            if app.has_interview_notes:
                preview = app.interview_notes[:30]
                return f"{app.interview_date} ✓ {preview}..."
            return f"{app.interview_date} ⚠ 待复盘"
        if app.status in INTERVIEW_STATUSES:
            return "待面试/待记录"
        if app.status in ("Offer", "拒绝"):
            return "未记录"
        return ""

    @staticmethod
    def _prep_text(app: InternshipApplication) -> str:
        items = []
        if app.resume_ready:
            items.append("简历")
        if app.project_ready:
            items.append("项目")
        if app.reviewed:
            items.append("复盘")
        return f"{app.prep_count}/3 " + ("、".join(items) if items else "未完成")

    @staticmethod
    def _days_between(start, end):
        try:
            if isinstance(start, str):
                start = datetime.strptime(start, "%Y-%m-%d").date()
            if isinstance(end, str):
                end = datetime.strptime(end, "%Y-%m-%d").date()
            return (end - start).days
        except (TypeError, ValueError):
            return None
