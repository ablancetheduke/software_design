"""InternshipDialog — add/edit internship application with validation."""

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

from ...models.internship_application import InternshipApplication

APPLICATION_STATUSES = [
    "待投递", "已投递", "笔试", "一面", "二面", "Offer", "拒绝", "放弃"
]
APPLICATION_DIRECTIONS = [
    "数据分析", "算法", "后端开发", "前端开发", "产品", "运营", "科研助理", "其他"
]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _is_valid_date(text: str) -> bool:
    """Check if text is a valid YYYY-MM-DD date."""
    if not _DATE_RE.match(text):
        return False
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class InternshipDialog(QDialog):
    """Add/edit internship application dialog with input validation."""

    def __init__(self, app: InternshipApplication = None, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("编辑实习投递" if app else "添加实习投递")
        self.setMinimumWidth(560)
        self._setup_ui()
        if app:
            self._populate(app)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.company_edit = QLineEdit()
        self.company_edit.setPlaceholderText("例如：字节跳动、腾讯、某科技公司")
        form.addRow("公司:", self.company_edit)

        self.position_edit = QLineEdit()
        self.position_edit.setPlaceholderText("例如：数据分析实习生")
        form.addRow("岗位:", self.position_edit)

        self.direction_combo = QComboBox()
        self.direction_combo.addItems(APPLICATION_DIRECTIONS)
        form.addRow("方向:", self.direction_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(APPLICATION_STATUSES)
        form.addRow("状态:", self.status_combo)

        self.apply_date_edit = QLineEdit()
        self.apply_date_edit.setPlaceholderText("YYYY-MM-DD")
        form.addRow("投递日期:", self.apply_date_edit)

        self.deadline_edit = QLineEdit()
        self.deadline_edit.setPlaceholderText("YYYY-MM-DD")
        form.addRow("截止日期:", self.deadline_edit)

        self.link_edit = QLineEdit()
        self.link_edit.setPlaceholderText("岗位链接或官网链接")
        form.addRow("链接:", self.link_edit)

        prep_layout = QHBoxLayout()
        self.resume_check = QCheckBox("简历已准备")
        self.project_check = QCheckBox("项目介绍已准备")
        self.review_check = QCheckBox("面试复盘已记录")
        prep_layout.addWidget(self.resume_check)
        prep_layout.addWidget(self.project_check)
        prep_layout.addWidget(self.review_check)
        prep_layout.addStretch()
        form.addRow("准备情况:", prep_layout)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText(
            "备注、HR 联系方式、下一步跟进事项等"
        )
        self.note_edit.setMaximumHeight(100)
        form.addRow("备注:", self.note_edit)

        # interview tracking — visible for interview-status records
        self.interview_date_edit = QLineEdit()
        self.interview_date_edit.setPlaceholderText("YYYY-MM-DD 面试日期")
        form.addRow("面试日期:", self.interview_date_edit)

        self.interview_notes_edit = QTextEdit()
        self.interview_notes_edit.setPlaceholderText(
            "记录面试题、考察点、自己的表现——下次投类似岗位时 AI 可帮你总结薄弱点"
        )
        self.interview_notes_edit.setMaximumHeight(80)
        form.addRow("面试复盘:", self.interview_notes_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        """Validate before accepting."""
        company = self.company_edit.text().strip()
        position = self.position_edit.text().strip()

        if not company:
            QMessageBox.warning(self, "输入校验", "公司名称不能为空。")
            self.company_edit.setFocus()
            return
        if not position:
            QMessageBox.warning(self, "输入校验", "岗位名称不能为空。")
            self.position_edit.setFocus()
            return

        apply_date = self.apply_date_edit.text().strip()
        if apply_date and not _is_valid_date(apply_date):
            QMessageBox.warning(
                self, "日期格式错误",
                f"投递日期「{apply_date}」不符合 YYYY-MM-DD 格式（如 2025-03-15）。"
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

    def _populate(self, app: InternshipApplication):
        self.company_edit.setText(app.company)
        self.position_edit.setText(app.position)
        self._set_combo_text(
            self.direction_combo, app.direction, APPLICATION_DIRECTIONS[-1]
        )
        self._set_combo_text(
            self.status_combo, app.status, APPLICATION_STATUSES[0]
        )
        self.apply_date_edit.setText(app.apply_date)
        self.deadline_edit.setText(app.deadline)
        self.link_edit.setText(app.link)
        self.note_edit.setPlainText(app.note)
        self.resume_check.setChecked(app.resume_ready)
        self.project_check.setChecked(app.project_ready)
        self.review_check.setChecked(app.reviewed)
        self.interview_date_edit.setText(app.interview_date)
        self.interview_notes_edit.setPlainText(app.interview_notes)

    def get_application(self) -> InternshipApplication:
        return InternshipApplication(
            app_id=self.app.app_id if self.app else None,
            company=self.company_edit.text().strip(),
            position=self.position_edit.text().strip(),
            direction=self.direction_combo.currentText(),
            apply_date=self.apply_date_edit.text().strip(),
            deadline=self.deadline_edit.text().strip(),
            status=self.status_combo.currentText(),
            link=self.link_edit.text().strip(),
            note=self.note_edit.toPlainText().strip(),
            resume_ready=self.resume_check.isChecked(),
            project_ready=self.project_check.isChecked(),
            reviewed=self.review_check.isChecked(),
            interview_date=self.interview_date_edit.text().strip(),
            interview_notes=self.interview_notes_edit.toPlainText().strip(),
        )

    @staticmethod
    def _set_combo_text(combo: QComboBox, value: str, fallback: str):
        idx = combo.findText(value)
        combo.setCurrentText(value if idx >= 0 else fallback)
