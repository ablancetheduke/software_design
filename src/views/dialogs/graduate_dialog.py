"""GraduateDialog — add/edit graduate school application with validation."""

import re
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from ...models.graduate_application import (
    ADVISOR_STATUSES,
    APPLICATION_BATCHES,
    DEGREE_TYPES,
    GRADUATE_STATUSES,
    GraduateApplication,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _is_valid_date(text: str) -> bool:
    if not _DATE_RE.match(text):
        return False
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class GraduateDialog(QDialog):
    """Add/edit graduate school application dialog."""

    def __init__(self, app: GraduateApplication = None, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("编辑升学申请" if app else "添加升学申请")
        self.setMinimumWidth(580)
        self._setup_ui()
        if app:
            self._populate(app)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # ── 基本信息 ──
        self.school_edit = QLineEdit()
        self.school_edit.setPlaceholderText("例如：清华大学、北京大学、MIT")
        form.addRow("🏫 学校:", self.school_edit)

        self.college_edit = QLineEdit()
        self.college_edit.setPlaceholderText("例如：软件与微电子学院、计算机学院")
        form.addRow("🏛️ 学院/项目:", self.college_edit)

        self.major_edit = QLineEdit()
        self.major_edit.setPlaceholderText("例如：计算机科学与技术、数据科学")
        form.addRow("📚 专业方向:", self.major_edit)

        self.degree_combo = QComboBox()
        self.degree_combo.addItems(DEGREE_TYPES)
        form.addRow("🎓 学位类型:", self.degree_combo)

        self.batch_combo = QComboBox()
        self.batch_combo.addItems(APPLICATION_BATCHES)
        form.addRow("📅 申请批次:", self.batch_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(GRADUATE_STATUSES)
        form.addRow("📌 当前状态:", self.status_combo)

        # ── 日期 ──
        self.apply_date_edit = QLineEdit()
        self.apply_date_edit.setPlaceholderText("YYYY-MM-DD  报名/投递日期")
        form.addRow("报名日期:", self.apply_date_edit)

        self.deadline_edit = QLineEdit()
        self.deadline_edit.setPlaceholderText("YYYY-MM-DD  材料截止日期")
        form.addRow("截止日期:", self.deadline_edit)

        # ── 导师 ──
        self.advisor_edit = QLineEdit()
        self.advisor_edit.setPlaceholderText("意向导师姓名")
        form.addRow("👤 意向导师:", self.advisor_edit)

        self.advisor_status_combo = QComboBox()
        self.advisor_status_combo.addItems(ADVISOR_STATUSES)
        form.addRow("导师联系状态:", self.advisor_status_combo)

        # ── 链接 ──
        self.link_edit = QLineEdit()
        self.link_edit.setPlaceholderText("招生简章、导师主页或报名系统链接")
        form.addRow("🔗 链接:", self.link_edit)

        # ── 材料准备 ──
        mat_row1 = QHBoxLayout()
        self.ps_check = QCheckBox("个人陈述")
        self.recommendation_check = QCheckBox("推荐信")
        self.cv_check = QCheckBox("简历")
        mat_row1.addWidget(self.ps_check)
        mat_row1.addWidget(self.recommendation_check)
        mat_row1.addWidget(self.cv_check)
        mat_row1.addStretch()
        form.addRow("材料准备 (1/2):", mat_row1)

        mat_row2 = QHBoxLayout()
        self.transcript_check = QCheckBox("成绩单")
        self.ranking_check = QCheckBox("排名证明")
        self.english_check = QCheckBox("英语成绩")
        mat_row2.addWidget(self.transcript_check)
        mat_row2.addWidget(self.ranking_check)
        mat_row2.addWidget(self.english_check)
        mat_row2.addStretch()
        form.addRow("材料准备 (2/2):", mat_row2)

        # ── 备注 ──
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("备注、招生办联系方式、特殊要求等")
        self.note_edit.setMaximumHeight(80)
        form.addRow("📝 备注:", self.note_edit)

        # ── 复试记录 ──
        self.interview_date_edit = QLineEdit()
        self.interview_date_edit.setPlaceholderText("YYYY-MM-DD  复试/面试日期")
        form.addRow("复试日期:", self.interview_date_edit)

        self.interview_notes_edit = QTextEdit()
        self.interview_notes_edit.setPlaceholderText(
            "记录复试问题、考察重点、自我表现——方便后续复盘和 AI 分析薄弱点"
        )
        self.interview_notes_edit.setMaximumHeight(80)
        form.addRow("复试复盘:", self.interview_notes_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        school = self.school_edit.text().strip()
        major = self.major_edit.text().strip()

        if not school:
            QMessageBox.warning(self, "输入校验", "学校名称不能为空。")
            self.school_edit.setFocus()
            return
        if not major:
            QMessageBox.warning(self, "输入校验", "专业方向不能为空。")
            self.major_edit.setFocus()
            return

        apply_date = self.apply_date_edit.text().strip()
        if apply_date and not _is_valid_date(apply_date):
            QMessageBox.warning(
                self, "日期格式错误",
                f"报名日期「{apply_date}」不符合 YYYY-MM-DD 格式（如 2025-03-15）。"
            )
            self.apply_date_edit.setFocus()
            return

        deadline = self.deadline_edit.text().strip()
        if deadline and not _is_valid_date(deadline):
            QMessageBox.warning(
                self, "日期格式错误",
                f"截止日期「{deadline}」不符合 YYYY-MM-DD 格式（如 2025-04-01）。"
            )
            self.deadline_edit.setFocus()
            return

        link = self.link_edit.text().strip()
        if link and not _URL_RE.match(link):
            QMessageBox.warning(
                self, "链接格式错误",
                f"链接「{link}」必须以 http:// 或 https:// 开头。"
            )
            self.link_edit.setFocus()
            return

        self.accept()

    def _populate(self, app: GraduateApplication):
        self.school_edit.setText(app.school)
        self.college_edit.setText(app.college)
        self.major_edit.setText(app.major)
        self._set_combo(self.degree_combo, app.degree_type, DEGREE_TYPES[0])
        self._set_combo(self.batch_combo, app.batch, APPLICATION_BATCHES[0])
        self._set_combo(self.status_combo, app.status, GRADUATE_STATUSES[0])
        self.apply_date_edit.setText(app.apply_date)
        self.deadline_edit.setText(app.deadline)
        self.advisor_edit.setText(app.advisor)
        self._set_combo(
            self.advisor_status_combo, app.advisor_status, ADVISOR_STATUSES[0]
        )
        self.link_edit.setText(app.link)
        self.note_edit.setPlainText(app.note)
        self.ps_check.setChecked(app.ps_ready)
        self.recommendation_check.setChecked(app.recommendation_ready)
        self.cv_check.setChecked(app.cv_ready)
        self.transcript_check.setChecked(app.transcript_ready)
        self.ranking_check.setChecked(app.ranking_ready)
        self.english_check.setChecked(app.english_ready)
        self.interview_date_edit.setText(app.interview_date)
        self.interview_notes_edit.setPlainText(app.interview_notes)

    def get_application(self) -> GraduateApplication:
        return GraduateApplication(
            app_id=self.app.app_id if self.app else None,
            school=self.school_edit.text().strip(),
            college=self.college_edit.text().strip(),
            major=self.major_edit.text().strip(),
            degree_type=self.degree_combo.currentText(),
            batch=self.batch_combo.currentText(),
            status=self.status_combo.currentText(),
            apply_date=self.apply_date_edit.text().strip(),
            deadline=self.deadline_edit.text().strip(),
            advisor=self.advisor_edit.text().strip(),
            advisor_status=self.advisor_status_combo.currentText(),
            link=self.link_edit.text().strip(),
            note=self.note_edit.toPlainText().strip(),
            ps_ready=self.ps_check.isChecked(),
            recommendation_ready=self.recommendation_check.isChecked(),
            cv_ready=self.cv_check.isChecked(),
            transcript_ready=self.transcript_check.isChecked(),
            ranking_ready=self.ranking_check.isChecked(),
            english_ready=self.english_check.isChecked(),
            interview_date=self.interview_date_edit.text().strip(),
            interview_notes=self.interview_notes_edit.toPlainText().strip(),
        )

    @staticmethod
    def _set_combo(combo: QComboBox, value: str, fallback: str):
        idx = combo.findText(value)
        combo.setCurrentText(value if idx >= 0 else fallback)
