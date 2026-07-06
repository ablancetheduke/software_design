"""Course management page — CRUD + CSV upload + export."""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Qt, Signal

from ..database.repositories.course_repo import CourseRepository
from ..services.data_io import DataIO
from ..utils.constants import COURSE_CATEGORIES, SEMESTERS
from ..utils.theme import theme
from .dialogs.course_dialog import CourseDialog
from .widgets.record_table import RecordTable
from .widgets.search_bar import SearchBar


class CourseView(QWidget):
    """Course management page."""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = CourseRepository()
        self.data_io = DataIO()
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("课程管理")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # ── toolbar ─────────────────────────────────────────────
        toolbar = QHBoxLayout()

        self.upload_btn = QPushButton("📂 上传成绩单 CSV")
        self.upload_btn.setToolTip("选择一个 CSV 文件，将替换当前全部课程数据")
        self.upload_btn.setStyleSheet(theme.primary_btn_style())
        self.upload_btn.clicked.connect(self._import_csv)
        toolbar.addWidget(self.upload_btn)

        toolbar.addSpacing(8)

        self.add_btn = QPushButton("+ 添加")
        self.add_btn.clicked.connect(self._add_course)
        toolbar.addWidget(self.add_btn)

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit_course)
        toolbar.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._delete_course)
        toolbar.addWidget(self.delete_btn)

        toolbar.addSpacing(20)

        toolbar.addWidget(QLabel("学期:"))
        self.semester_filter = QComboBox()
        self.semester_filter.addItem("全部")
        self.semester_filter.addItems(SEMESTERS)
        self.semester_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.semester_filter)

        toolbar.addWidget(QLabel("类别:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("全部")
        self.category_filter.addItems(COURSE_CATEGORIES)
        self.category_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.category_filter)

        toolbar.addStretch()

        self.export_btn = QPushButton("导出 CSV")
        self.export_btn.clicked.connect(self._export_csv)
        toolbar.addWidget(self.export_btn)

        self.clear_btn = QPushButton("清空全部")
        self.clear_btn.setStyleSheet(theme.danger_btn_style())
        self.clear_btn.clicked.connect(self._clear_all)
        toolbar.addWidget(self.clear_btn)

        layout.addLayout(toolbar)

        # ── empty-state hint ────────────────────────────────────
        self.empty_hint = QLabel(
            "还没有课程数据。点击 <b>「📂 上传成绩单 CSV」</b> 导入你的成绩单。\n"
            "CSV 列顺序：课程名, 代码, 学分, 学期, 成绩, 类别, 备注"
        )
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.setWordWrap(True)
        self.empty_hint.setStyleSheet(
            f"color: {theme.fg_muted}; font-size: 14px; background: {theme.warn_bg}; "
            f"border: 1px solid {theme.warn_border}; border-radius: 8px; "
            "padding: 32px 20px; margin: 20px 0;"
        )
        layout.addWidget(self.empty_hint)

        # ── search ──────────────────────────────────────────────
        self.search_bar = SearchBar("搜索课程名或代码...")
        self.search_bar.search_requested.connect(self._on_search)
        layout.addWidget(self.search_bar)

        # ── table ───────────────────────────────────────────────
        self.table = RecordTable()
        self.table.set_columns(
            ["ID", "课程名称", "代码", "学分", "学期", "成绩", "类别", "备注"],
            id_column=0,
        )
        self.table.row_double_clicked_signal.connect(self._edit_course_by_id)
        layout.addWidget(self.table)

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(
            f"color: {theme.fg_muted}; font-size: 12px; padding: 4px;"
        )
        layout.addWidget(self.stats_label)

    # ── helpers ──────────────────────────────────────────────────

    @staticmethod
    def _grade_display(course) -> str:
        if course.is_in_progress:
            return "在修"
        if course.is_pass_fail:
            return "通过"
        return f"{course.grade:g}"

    # ── data ─────────────────────────────────────────────────────

    def _refresh_table(self):
        courses = self.repo.get_all()
        rows = [[
            c.course_id, c.name, c.code, c.credit,
            c.semester, self._grade_display(c), c.category, c.note,
        ] for c in courses]
        self.table.load_data(rows)
        self._update_stats(courses)
        self.empty_hint.setVisible(len(courses) == 0)
        self.search_bar.setVisible(len(courses) > 0)

    def _update_stats(self, courses):
        total = len(courses)
        total_credits = sum(c.credit for c in courses)
        scored = [c for c in courses if not c.is_in_progress and not c.is_pass_fail]
        avg = round(sum(c.grade for c in scored) / len(scored), 1) if scored else 0
        in_progress = sum(1 for c in courses if c.is_in_progress)
        pass_count = sum(1 for c in courses if c.is_pass_fail)
        extra = ""
        if in_progress or pass_count:
            parts = []
            if in_progress:
                parts.append(f"{in_progress} 门在修")
            if pass_count:
                parts.append(f"{pass_count} 门通过制")
            extra = " | " + "，".join(parts)
        self.stats_label.setText(
            f"共 {total} 门课程 | 总学分: {total_credits} | 平均分: {avg}{extra}"
        )

    # ── CRUD ─────────────────────────────────────────────────────

    def _add_course(self):
        dialog = CourseDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.repo.add(dialog.get_course())
            self._refresh_table()
            self.data_changed.emit()

    def _edit_course(self):
        cid = self.table.get_selected_id()
        if cid < 0:
            QMessageBox.warning(self, "提示", "请先选择一门课程")
            return
        self._edit_course_by_id(cid)

    def _edit_course_by_id(self, cid: int):
        course = self.repo.get_by_id(cid)
        if not course:
            return
        dialog = CourseDialog(course, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.repo.update(dialog.get_course())
            self._refresh_table()
            self.data_changed.emit()

    def _delete_course(self):
        cid = self.table.get_selected_id()
        if cid < 0:
            QMessageBox.warning(self, "提示", "请先选择一门课程")
            return
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这门课程吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete(cid)
            self._refresh_table()
            self.data_changed.emit()

    def _clear_all(self):
        courses = self.repo.get_all()
        if not courses:
            return
        reply = QMessageBox.question(
            self, "确认清空",
            f"确定要删除全部 {len(courses)} 门课程吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for c in courses:
                self.repo.delete(c.course_id)
            self._refresh_table()
            self.data_changed.emit()

    # ── import / export ──────────────────────────────────────────

    def _import_csv(self):
        # pick file first — don't delete until user confirms the file
        filepath, _ = QFileDialog.getOpenFileName(
            self, "选择成绩单 CSV", "", "CSV Files (*.csv);;All Files (*)",
        )
        if not filepath:
            return

        courses = self.repo.get_all()
        if courses:
            reply = QMessageBox.question(
                self, "确认替换",
                f"当前有 {len(courses)} 门课程。上传 CSV 将<b>替换全部数据</b>。\n\n"
                f"是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            for c in courses:
                self.repo.delete(c.course_id)

        result = self.data_io.import_courses_csv(filepath)
        QMessageBox.information(
            self, "导入完成",
            f"成功导入 {result['imported']} 门课程"
            + (f"，跳过 {result['skipped']} 行" if result.get('skipped') else ""),
        )
        self._refresh_table()
        self.data_changed.emit()

    def _export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出课程 CSV", "courses_export.csv", "CSV Files (*.csv)",
        )
        if filepath:
            count = self.data_io.export_courses_csv(filepath)
            QMessageBox.information(self, "导出完成", f"已导出 {count} 门课程")

    # ── filters & search ─────────────────────────────────────────

    def _on_filter_changed(self):
        semester = self.semester_filter.currentText()
        category = self.category_filter.currentText()

        if semester == "全部" and category == "全部":
            courses = self.repo.get_all()
        elif semester != "全部" and category == "全部":
            courses = self.repo.get_by_semester(semester)
        elif semester == "全部" and category != "全部":
            courses = self.repo.get_by_category(category)
        else:
            courses = self.repo.get_by_semester(semester)
            courses = [c for c in courses if c.category == category]

        rows = [[
            c.course_id, c.name, c.code, c.credit,
            c.semester, self._grade_display(c), c.category, c.note,
        ] for c in courses]
        self.table.load_data(rows)
        self._update_stats(courses)

    def _on_search(self, keyword: str):
        if not keyword.strip():
            self._on_filter_changed()
            return
        courses = self.repo.search(keyword)
        rows = [[
            c.course_id, c.name, c.code, c.credit,
            c.semester, self._grade_display(c), c.category, c.note,
        ] for c in courses]
        self.table.load_data(rows)
        self._update_stats(courses)

    def refresh(self):
        self._refresh_table()
