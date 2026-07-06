"""Experience management page — tabbed by type."""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QMessageBox, QFileDialog, QTabWidget,
)
from PySide6.QtCore import Qt, Signal
from ..database.repositories.experience_repo import ExperienceRepository
from ..services.data_io import DataIO
from ..utils.constants import EXPERIENCE_TYPES
from ..utils.theme import theme
from .dialogs.experience_dialog import ExperienceDialog
from .widgets.record_table import RecordTable


# Tab labels → (experience type filter, upload button label)
TABS = [
    ("全部",            None,                 "全部经历"),
    ("📐 科研 & 项目",  ["科研", "项目"],      "科研/项目经历"),
    ("🏆 比赛",         ["竞赛"],              "比赛经历"),
    ("💼 实习",         ["实习"],              "实习经历"),
    ("📌 其他",         ["其他"],              "其他经历"),
]


class ExperienceView(QWidget):
    """Experience management page with type tabs."""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = ExperienceRepository()
        self.data_io = DataIO()
        self._current_filter = None  # None = all
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("经历管理")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # ── toolbar ─────────────────────────────────────────────
        toolbar = QHBoxLayout()

        self.upload_btn = QPushButton("📂 上传 CSV")
        self.upload_btn.setStyleSheet(theme.primary_btn_style())
        self.upload_btn.clicked.connect(self._import_csv)
        toolbar.addWidget(self.upload_btn)

        self.add_btn = QPushButton("+ 添加")
        self.add_btn.clicked.connect(self._add)
        toolbar.addWidget(self.add_btn)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._delete)
        toolbar.addWidget(self.delete_btn)

        toolbar.addStretch()

        self.clear_btn = QPushButton("清空本页")
        self.clear_btn.setStyleSheet(theme.danger_btn_style())
        self.clear_btn.clicked.connect(self._clear_visible)
        toolbar.addWidget(self.clear_btn)

        layout.addLayout(toolbar)

        # ── tabs ────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(theme.tab_widget_style())
        for label, _filter, _btn_label in TABS:
            tab_page = QWidget()
            self.tabs.addTab(tab_page, label)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # ── table (shared across tabs) ─────────────────────────
        self.table = RecordTable()
        self.table.set_columns(
            ["ID", "标题", "类型", "组织机构", "开始", "结束", "描述", "角色", "成果"],
            id_column=0,
        )
        self.table.row_double_clicked_signal.connect(self._edit_by_id)
        layout.addWidget(self.table)

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {theme.fg_muted}; font-size: 12px; padding: 4px;")
        layout.addWidget(self.stats_label)

        # trigger initial tab state (after table exists)
        self._on_tab_changed(0)

    # ── data ─────────────────────────────────────────────────────

    def _get_filtered(self):
        if self._current_filter is None:
            return self.repo.get_all()
        result = []
        for etype in self._current_filter:
            result.extend(self.repo.get_by_type(etype))
        result.sort(key=lambda e: e.start_date or "", reverse=True)
        return result

    def _refresh_table(self):
        exps = self._get_filtered()
        rows = [[
            e.exp_id, e.title, e.exp_type, e.organization,
            e.start_date, e.end_date, e.description, e.role, e.outcome,
        ] for e in exps]
        self.table.load_data(rows)
        self.stats_label.setText(f"共 {len(exps)} 条经历")

    def _on_tab_changed(self, index: int):
        _, self._current_filter, btn_label = TABS[index]
        self.upload_btn.setText(f"📂 上传{btn_label} CSV")
        self.upload_btn.setToolTip(f"选择一个 CSV 文件，仅替换「{TABS[index][0].strip()}」下的经历")
        self._refresh_table()

    # ── CRUD ─────────────────────────────────────────────────────

    def _add(self):
        dialog = ExperienceDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.repo.add(dialog.get_experience())
            self._refresh_table()
            self.data_changed.emit()

    def _edit(self):
        eid = self.table.get_selected_id()
        if eid < 0:
            QMessageBox.warning(self, "提示", "请先选择一条经历")
            return
        self._edit_by_id(eid)

    def _edit_by_id(self, eid: int):
        exp = self.repo.get_by_id(eid)
        if not exp:
            return
        dialog = ExperienceDialog(exp, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.repo.update(dialog.get_experience())
            self._refresh_table()
            self.data_changed.emit()

    def _delete(self):
        eid = self.table.get_selected_id()
        if eid < 0:
            QMessageBox.warning(self, "提示", "请先选择一条经历")
            return
        reply = QMessageBox.question(
            self, "确认删除", "确定删除这条经历吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete(eid)
            self._refresh_table()
            self.data_changed.emit()

    def _clear_visible(self):
        exps = self._get_filtered()
        if not exps:
            return
        tab_label = TABS[self.tabs.currentIndex()][0]
        reply = QMessageBox.question(
            self, "确认清空",
            f"确定要删除「{tab_label}」中的全部 {len(exps)} 条经历吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for e in exps:
                self.repo.delete(e.exp_id)
            self._refresh_table()
            self.data_changed.emit()

    # ── import ───────────────────────────────────────────────────

    def _import_csv(self):
        _, filter_types, btn_label = TABS[self.tabs.currentIndex()]

        filepath, _ = QFileDialog.getOpenFileName(
            self, f"选择{btn_label} CSV", "", "CSV Files (*.csv);;All Files (*)",
        )
        if not filepath:
            return

        # figure out what to replace and what type to force
        if filter_types is None:
            # "全部" tab → replace everything, don't force type
            scope_exps = self.repo.get_all()
            scope_label = "全部经历"
            force_type = ""
        else:
            scope_exps = []
            for ft in filter_types:
                scope_exps.extend(self.repo.get_by_type(ft))
            scope_label = "、".join(filter_types)
            force_type = filter_types[0]  # force first type in the filter list

        if scope_exps:
            reply = QMessageBox.question(
                self, "确认替换",
                f"当前「{scope_label}」有 {len(scope_exps)} 条记录。\n"
                f"上传 CSV 将<b>仅替换这一分类</b>，其他分类不受影响。\n"
                + (f"所有导入行将自动标记为「{force_type}」。\n" if force_type else "")
                + "\n是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            for e in scope_exps:
                self.repo.delete(e.exp_id)

        result = self.data_io.import_experiences_csv(filepath, force_exp_type=force_type)
        QMessageBox.information(
            self, "导入完成",
            f"成功导入 {result['imported']} 条{btn_label}"
            + (f"，跳过 {result['skipped']} 行" if result.get('skipped') else ""),
        )
        # switch to "全部" tab to show the just-imported data alongside everything
        self.tabs.setCurrentIndex(0)
        self._refresh_table()
        self.data_changed.emit()

    def refresh(self):
        self._refresh_table()
