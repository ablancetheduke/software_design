"""CourseDialog — add/edit a course with input validation."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from ...models.course import Course, PF_MARKER
from ...utils.constants import COURSE_CATEGORIES, SEMESTERS


class CourseDialog(QDialog):
    """Dialog for adding/editing a course with input validation."""

    def __init__(self, course: Course = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑课程" if course else "添加课程")
        self.setMinimumWidth(450)
        self.course = course
        self._setup_ui()
        if course:
            self._populate(course)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("如: 高等数学（一）")
        form.addRow("课程名称:", self.name_edit)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("如: MAT108")
        form.addRow("课程代码:", self.code_edit)

        self.credit_spin = QDoubleSpinBox()
        self.credit_spin.setRange(0, 20)
        self.credit_spin.setValue(3.0)
        self.credit_spin.setSingleStep(0.5)
        form.addRow("学分:", self.credit_spin)

        self.semester_combo = QComboBox()
        self.semester_combo.addItems(SEMESTERS)
        form.addRow("学期:", self.semester_combo)

        # ── grade mode + spinner ──
        grade_row = QHBoxLayout()
        self.grade_mode_combo = QComboBox()
        self.grade_mode_combo.addItems(["百分制", "通过制 (P/F)", "在修"])
        self.grade_mode_combo.currentTextChanged.connect(self._on_grade_mode)
        grade_row.addWidget(self.grade_mode_combo)

        self.grade_spin = QDoubleSpinBox()
        self.grade_spin.setRange(0, 100)
        self.grade_spin.setValue(85)
        self.grade_spin.setSingleStep(1)
        self.grade_spin.setSuffix(" 分")
        grade_row.addWidget(self.grade_spin)
        grade_row.addStretch()
        form.addRow("成绩:", grade_row)

        self.category_combo = QComboBox()
        self.category_combo.addItems(COURSE_CATEGORIES)
        form.addRow("类别:", self.category_combo)

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("备注（可选）")
        form.addRow("备注:", self.note_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        """Validate inputs before accepting the dialog."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "输入校验", "课程名称不能为空。")
            self.name_edit.setFocus()
            return

        credit = self.credit_spin.value()
        if credit <= 0:
            QMessageBox.warning(self, "输入校验", "学分必须大于 0。")
            self.credit_spin.setFocus()
            return

        self.accept()

    def _on_grade_mode(self, mode: str):
        """Show/hide the number spinner based on grade mode."""
        is_numeric = mode == "百分制"
        self.grade_spin.setVisible(is_numeric)

    def _populate(self, course: Course):
        self.name_edit.setText(course.name)
        self.code_edit.setText(course.code)
        self.credit_spin.setValue(course.credit)
        idx = self.semester_combo.findText(course.semester)
        if idx >= 0:
            self.semester_combo.setCurrentIndex(idx)

        # detect existing grade mode using [P/F] marker
        if course.grade < 0:
            self.grade_mode_combo.setCurrentText("在修")
            self.grade_spin.setValue(0)
        elif course.note and PF_MARKER in course.note:
            self.grade_mode_combo.setCurrentText("通过制 (P/F)")
            self.grade_spin.setValue(0)
        else:
            self.grade_mode_combo.setCurrentText("百分制")
            self.grade_spin.setValue(course.grade)

        self._on_grade_mode(self.grade_mode_combo.currentText())

        idx = self.category_combo.findText(course.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        # Strip [P/F] from displayed note
        note = course.note or ""
        note = note.replace(PF_MARKER, "").strip()
        self.note_edit.setText(note)

    def get_course(self) -> Course:
        mode = self.grade_mode_combo.currentText()
        if mode == "在修":
            grade = -1.0
            note = self.note_edit.text().strip()
        elif "通过" in mode:
            grade = 60.0
            base_note = self.note_edit.text().strip()
            note = (PF_MARKER + " " + base_note).strip() if base_note else PF_MARKER
        else:
            grade = self.grade_spin.value()
            note = self.note_edit.text().strip()

        return Course(
            course_id=self.course.course_id if self.course else None,
            name=self.name_edit.text().strip(),
            code=self.code_edit.text().strip().upper(),
            credit=self.credit_spin.value(),
            semester=self.semester_combo.currentText(),
            grade=grade,
            category=self.category_combo.currentText(),
            note=note,
        )
