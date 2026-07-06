"""ExperienceDialog — add/edit an experience with input validation."""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from ...models.experience import Experience
from ...utils.constants import EXPERIENCE_TYPES


class ExperienceDialog(QDialog):
    """Dialog for adding/editing an experience with input validation."""

    def __init__(self, exp: Experience = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑经历" if exp else "添加经历")
        self.setMinimumWidth(450)
        self.exp = exp
        self._setup_ui()
        if exp:
            self._populate(exp)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("如: 全国数学建模竞赛")
        form.addRow("标题:", self.title_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(EXPERIENCE_TYPES)
        form.addRow("类型:", self.type_combo)

        self.org_edit = QLineEdit()
        self.org_edit.setPlaceholderText("组织/公司/学校")
        form.addRow("组织机构:", self.org_edit)

        self.start_edit = QLineEdit()
        self.start_edit.setPlaceholderText("如: 2024-09")
        form.addRow("开始日期:", self.start_edit)

        self.end_edit = QLineEdit()
        self.end_edit.setPlaceholderText("如: 2025-01")
        form.addRow("结束日期:", self.end_edit)

        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("担任的角色")
        form.addRow("角色:", self.role_edit)

        self.outcome_edit = QLineEdit()
        self.outcome_edit.setPlaceholderText("成果/收获")
        form.addRow("成果:", self.outcome_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("详细描述...")
        self.desc_edit.setMaximumHeight(100)
        form.addRow("描述:", self.desc_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        """Validate inputs before accepting."""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "输入校验", "标题不能为空。")
            self.title_edit.setFocus()
            return
        self.accept()

    def _populate(self, exp: Experience):
        self.title_edit.setText(exp.title)
        idx = self.type_combo.findText(exp.exp_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.org_edit.setText(exp.organization)
        self.start_edit.setText(exp.start_date)
        self.end_edit.setText(exp.end_date)
        self.role_edit.setText(exp.role)
        self.outcome_edit.setText(exp.outcome)
        self.desc_edit.setPlainText(exp.description)

    def get_experience(self) -> Experience:
        return Experience(
            exp_id=self.exp.exp_id if self.exp else None,
            title=self.title_edit.text().strip(),
            exp_type=self.type_combo.currentText(),
            organization=self.org_edit.text().strip(),
            start_date=self.start_edit.text().strip(),
            end_date=self.end_edit.text().strip(),
            description=self.desc_edit.toPlainText().strip(),
            role=self.role_edit.text().strip(),
            outcome=self.outcome_edit.text().strip(),
        )
