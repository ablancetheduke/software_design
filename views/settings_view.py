"""Student profile settings page."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QGroupBox, QLabel, QMessageBox,
    QComboBox,
)
from ..database.repositories.student_repo import StudentRepository
from ..models.student import Student
from ..utils.theme import theme


class SettingsView(QWidget):
    """Page for editing student personal information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo = StudentRepository()
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("个人信息设置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Basic info group
        basic_group = QGroupBox("基本信息")
        form = QFormLayout(basic_group)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("姓名")
        form.addRow("姓名:", self.name_edit)

        self.student_no_edit = QLineEdit()
        self.student_no_edit.setPlaceholderText("学号")
        form.addRow("学号:", self.student_no_edit)

        self.college_edit = QLineEdit()
        self.college_edit.setPlaceholderText("如: 信息学院")
        form.addRow("学院:", self.college_edit)

        self.major_edit = QLineEdit()
        self.major_edit.setPlaceholderText("如: 数据科学与大数据技术")
        form.addRow("专业:", self.major_edit)

        self.enrollment_edit = QComboBox()
        self.enrollment_edit.addItems(["", "2023", "2024", "2025"])
        self.enrollment_edit.setEditable(True)
        self.enrollment_edit.setCurrentText("")
        form.addRow("入学年份 (培养方案):", self.enrollment_edit)

        layout.addWidget(basic_group)

        # Contact group
        contact_group = QGroupBox("联系方式")
        form2 = QFormLayout(contact_group)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@example.com")
        form2.addRow("邮箱:", self.email_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("手机号")
        form2.addRow("电话:", self.phone_edit)

        self.github_edit = QLineEdit()
        self.github_edit.setPlaceholderText("GitHub 用户名或链接")
        form2.addRow("GitHub:", self.github_edit)

        self.linkedin_edit = QLineEdit()
        self.linkedin_edit.setPlaceholderText("LinkedIn 链接")
        form2.addRow("LinkedIn:", self.linkedin_edit)

        layout.addWidget(contact_group)

        # Skills & Summary
        profile_group = QGroupBox("个人简介与技能")
        form3 = QFormLayout(profile_group)

        self.skills_edit = QLineEdit()
        self.skills_edit.setPlaceholderText("技能，用逗号分隔，如: Python, SQL, 数据分析")
        form3.addRow("技能:", self.skills_edit)

        self.summary_edit = QTextEdit()
        self.summary_edit.setPlaceholderText("简要介绍自己...")
        self.summary_edit.setMaximumHeight(100)
        form3.addRow("简介:", self.summary_edit)

        layout.addWidget(profile_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet(
            f"QPushButton {{ background: {theme.accent}; color: white; padding: 8px 24px; "
            f"border-radius: 4px; border: 1px solid {theme.accent_hover}; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {theme.accent_hover}; }}"
        )
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _load_data(self):
        """Load student profile from database."""
        student = self.repo.get()
        if student:
            self.name_edit.setText(student.name if student.name != "未设置" else "")
            self.student_no_edit.setText(student.student_no)
            self.college_edit.setText(student.college)
            self.major_edit.setText(student.major)
            self.enrollment_edit.setCurrentText(student.enrollment_year if (student.enrollment_year and student.enrollment_year != "未设置") else "")
            self.email_edit.setText(student.email)
            self.phone_edit.setText(student.phone)
            self.github_edit.setText(student.github)
            self.linkedin_edit.setText(student.linkedin)
            self.skills_edit.setText(student.skills)
            self.summary_edit.setPlainText(student.summary)

    def _save(self):
        """Save student profile to database."""
        student = Student(
            name=self.name_edit.text(),
            student_no=self.student_no_edit.text(),
            college=self.college_edit.text(),
            major=self.major_edit.text(),
            enrollment_year=self.enrollment_edit.currentText().strip(),
            email=self.email_edit.text(),
            phone=self.phone_edit.text(),
            github=self.github_edit.text(),
            linkedin=self.linkedin_edit.text(),
            skills=self.skills_edit.text(),
            summary=self.summary_edit.toPlainText(),
        )
        self.repo.save(student)
        QMessageBox.information(self, "成功", "个人信息已保存！")
