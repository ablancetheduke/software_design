"""Achievement management page (awards, scholarships, honors)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QFormLayout, QDialog, QDialogButtonBox,
    QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt, Signal
from ..models.achievement import Achievement
from ..database.repositories.achievement_repo import AchievementRepository
from ..services.data_io import DataIO
from ..utils.constants import ACHIEVEMENT_TYPES
from ..utils.theme import theme
from .widgets.record_table import RecordTable


class AchievementDialog(QDialog):
    """Dialog for adding/editing an achievement."""

    def __init__(self, ach: Achievement = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑成就" if ach else "添加成就")
        self.setMinimumWidth(400)
        self.ach = ach
        self._setup_ui()
        if ach:
            self._populate(ach)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("如: 国家奖学金")
        form.addRow("标题:", self.title_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(ACHIEVEMENT_TYPES)
        form.addRow("类型:", self.type_combo)

        self.issuer_edit = QLineEdit()
        self.issuer_edit.setPlaceholderText("颁发机构")
        form.addRow("颁发机构:", self.issuer_edit)

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("如: 2025-06")
        form.addRow("日期:", self.date_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("备注描述")
        form.addRow("描述:", self.desc_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate(self, ach: Achievement):
        self.title_edit.setText(ach.title)
        idx = self.type_combo.findText(ach.ach_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.issuer_edit.setText(ach.issuer)
        self.date_edit.setText(ach.date)
        self.desc_edit.setText(ach.description)

    def get_achievement(self) -> Achievement:
        return Achievement(
            ach_id=self.ach.ach_id if self.ach else None,
            title=self.title_edit.text(),
            ach_type=self.type_combo.currentText(),
            issuer=self.issuer_edit.text(),
            date=self.date_edit.text(),
            description=self.desc_edit.text(),
        )


class AchievementView(QWidget):
    """Achievement management page."""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = AchievementRepository()
        self.data_io = DataIO()
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("荣誉与奖项")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        toolbar = QHBoxLayout()

        self.upload_btn = QPushButton("📂 上传荣誉 CSV")
        self.upload_btn.setToolTip("选择一个 CSV 文件，将替换当前全部荣誉数据")
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

        toolbar.addSpacing(20)
        toolbar.addWidget(QLabel("类型:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部")
        self.type_filter.addItems(ACHIEVEMENT_TYPES)
        self.type_filter.currentTextChanged.connect(self._on_filter)
        toolbar.addWidget(self.type_filter)
        toolbar.addStretch()

        self.clear_btn = QPushButton("清空全部")
        self.clear_btn.setStyleSheet(theme.danger_btn_style())
        self.clear_btn.clicked.connect(self._clear_all)
        toolbar.addWidget(self.clear_btn)

        layout.addLayout(toolbar)

        self.empty_hint = QLabel(
            "还没有荣誉数据。点击 <b>「📂 上传荣誉 CSV」</b> 批量导入。\n"
            "CSV 列顺序：标题, 类型, 颁发机构, 日期, 描述"
        )
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.setWordWrap(True)
        self.empty_hint.setStyleSheet(
            f"color: {theme.fg_muted}; font-size: 14px; background: {theme.warn_bg}; "
            f"border: 1px solid {theme.warn_border}; border-radius: 8px; padding: 32px 20px; margin: 20px 0;"
        )
        self.empty_hint.setVisible(False)
        layout.addWidget(self.empty_hint)

        self.table = RecordTable()
        self.table.set_columns(
            ["ID", "标题", "类型", "颁发机构", "日期", "描述"],
            id_column=0,
        )
        self.table.row_double_clicked_signal.connect(self._edit_by_id)
        layout.addWidget(self.table)

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {theme.fg_muted}; font-size: 12px; padding: 4px;")
        layout.addWidget(self.stats_label)

    def _refresh_table(self, achs=None):
        if achs is None:
            achs = self.repo.get_all()
        rows = [[a.ach_id, a.title, a.ach_type, a.issuer, a.date, a.description] for a in achs]
        self.table.load_data(rows)
        self.stats_label.setText(f"共 {len(achs)} 项成就")
        self.empty_hint.setVisible(len(achs) == 0)

    def _on_filter(self):
        atype = self.type_filter.currentText()
        achs = self.repo.get_all() if atype == "全部" else self.repo.get_by_type(atype)
        self._refresh_table(achs)

    def _add(self):
        dialog = AchievementDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.repo.add(dialog.get_achievement())
            self._refresh_table()
            self.data_changed.emit()

    def _edit(self):
        aid = self.table.get_selected_id()
        if aid < 0:
            QMessageBox.warning(self, "提示", "请先选择一项成就")
            return
        self._edit_by_id(aid)

    def _edit_by_id(self, aid: int):
        ach = self.repo.get_by_id(aid)
        if not ach:
            return
        dialog = AchievementDialog(ach, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.repo.update(dialog.get_achievement())
            self._refresh_table()
            self.data_changed.emit()

    def _delete(self):
        aid = self.table.get_selected_id()
        if aid < 0:
            QMessageBox.warning(self, "提示", "请先选择一项成就")
            return
        reply = QMessageBox.question(
            self, "确认删除", "确定删除这项成就吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete(aid)
            self._refresh_table()
            self.data_changed.emit()

    def _clear_all(self):
        achs = self.repo.get_all()
        if not achs:
            return
        reply = QMessageBox.question(
            self, "确认清空",
            f"确定要删除全部 {len(achs)} 项成就吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for a in achs:
                self.repo.delete(a.ach_id)
            self._refresh_table()
            self.data_changed.emit()

    def _import_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择荣誉 CSV", "", "CSV Files (*.csv);;All Files (*)",
        )
        if not filepath:
            return

        achs = self.repo.get_all()
        if achs:
            reply = QMessageBox.question(
                self, "确认替换",
                f"当前有 {len(achs)} 项荣誉。上传 CSV 将<b>替换全部数据</b>。\n\n是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            for a in achs:
                self.repo.delete(a.ach_id)

        result = self.data_io.import_achievements_csv(filepath)
        QMessageBox.information(
            self, "导入完成",
            f"成功导入 {result['imported']} 项荣誉"
            + (f"，跳过 {result['skipped']} 行" if result.get('skipped') else ""),
        )
        self._refresh_table()
        self.data_changed.emit()

    def refresh(self):
        self._refresh_table()
