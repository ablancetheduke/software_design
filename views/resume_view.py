"""Visual resume editor with live preview, candidate material browser, and PDF export.

Three-panel layout:
  Left   – collapsible-section form editor (drag any section open to edit)
  Center – candidate material browser (pull from courses/experiences/...)
  Right  – live HTML + Markdown preview
"""

from __future__ import annotations

import os
import tempfile
import webbrowser
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from ..database.repositories.achievement_repo import AchievementRepository
from ..database.repositories.course_repo import CourseRepository
from ..database.repositories.experience_repo import ExperienceRepository
from ..database.repositories.role_repo import RoleRepository
from ..database.repositories.student_repo import StudentRepository
from ..services.gpa_calculator import calculate_grade_overview
from ..services.resume_ai import (
    ResumeWorker,
    HTML_DOCUMENT_TEMPLATE,
)
from ..services.resume_exporter import (
    build_resume_html as build_new_html,
    build_resume_markdown as build_new_md,
    build_resume_json,
    compute_default_options,
    export_html_to_pdf,
)
from ..utils.theme import theme

# ── constants ──────────────────────────────────────────────────────────────

CANDIDATE_SOURCES = [
    ("课程亮点", "course"),
    ("实践经历", "experience"),
    ("成果记录", "achievement"),
    ("角色职责", "role"),
]

SOURCE_TO_EDITOR = {
    "course": "education_body_edit",
    "experience": "project_body_edit",
    "achievement": "awards_edit",
    "role": "custom_content_edit",
}

SOURCE_TO_LABEL = {
    "course": "插入到教育背景",
    "experience": "插入到项目经验",
    "achievement": "插入到竞赛获奖",
    "role": "插入到补充内容",
}


# ═══════════════════════════════════════════════════════════════════════════
#  CollapsibleSection — click header to expand/collapse a section of fields
# ═══════════════════════════════════════════════════════════════════════════


class CollapsibleSection(QWidget):
    """A section with a clickable header that toggles the content area.

    Usage::

        sec = CollapsibleSection("项目经验", expanded=True)
        sec.content_layout().addWidget(some_editor)
        form_layout.addWidget(sec)
    """

    def __init__(self, title: str, expanded: bool = True, parent=None):
        super().__init__(parent)
        self._expanded = expanded

        # outer vbox
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # header bar
        self._header = QFrame()
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet(
            f"QFrame {{"
            f"  background: {theme.bg_sidebar};"
            f"  border: 1px solid {theme.border};"
            f"  border-radius: 6px;"
            f"  padding: 6px 10px;"
            f"}}"
            f"QFrame:hover {{ background: {theme.bg_hover}; }}"
        )
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(8, 5, 8, 5)
        self._arrow = QLabel("▾" if expanded else "▸")
        self._arrow.setFixedWidth(16)
        self._arrow.setStyleSheet(
            f"color: {theme.accent}; font-size: 12px; font-weight: bold;"
        )
        hl.addWidget(self._arrow)
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            f"color: {theme.fg}; font-size: 13px; font-weight: 600;"
        )
        hl.addWidget(self._title_label, 1)
        outer.addWidget(self._header)

        # content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(4, 4, 4, 4)
        self._content_layout.setSpacing(6)
        if not expanded:
            self._content.hide()
        outer.addWidget(self._content)

        self._header.mousePressEvent = self._on_header_click

    def _on_header_click(self, event):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._arrow.setText("▾" if self._expanded else "▸")

    def content_layout(self) -> QVBoxLayout:
        """Return the content area's layout so callers can add widgets."""
        return self._content_layout

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._content.setVisible(expanded)
        self._arrow.setText("▾" if expanded else "▸")


# ── helper builders ────────────────────────────────────────────────────────


def _make_line_edit(placeholder: str = "", parent=None) -> QLineEdit:
    le = QLineEdit(parent)
    le.setPlaceholderText(placeholder)
    le.setStyleSheet(
        f"QLineEdit {{"
        f"  border: 1px solid {theme.border_input}; border-radius: 4px;"
        f"  padding: 6px 8px; background: {theme.bg_input}; color: {theme.fg};"
        f"  font-size: 13px;"
        f"}}"
        f"QLineEdit:focus {{ border: 1px solid {theme.accent}; }}"
    )
    le.setMinimumHeight(30)
    return le


def _make_text_edit(placeholder: str = "", min_h: int = 100, parent=None) -> QTextEdit:
    """Create a QTextEdit with minimum height (no max — user can type freely)."""
    te = QTextEdit(parent)
    te.setPlaceholderText(placeholder)
    te.setMinimumHeight(min_h)
    te.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    te.setWordWrapMode(te.wordWrapMode())
    te.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    te.setStyleSheet(
        f"QTextEdit {{"
        f"  border: 1px solid {theme.border_input}; border-radius: 4px;"
        f"  padding: 6px 8px; background: {theme.bg_input}; color: {theme.fg};"
        f"  font-size: 13px;"
        f"}}"
        f"QTextEdit:focus {{ border: 1px solid {theme.accent}; }}"
    )
    return te


def _make_checkbox(text: str, parent=None) -> QCheckBox:
    cb = QCheckBox(text, parent)
    cb.setStyleSheet(
        f"QCheckBox {{ color: {theme.fg_muted}; font-size: 13px; spacing: 6px; }}"
        f"QCheckBox::indicator {{"
        f"  width: 16px; height: 16px;"
        f"  border: 1px solid {theme.border}; border-radius: 3px;"
        f"  background: {theme.bg_input};"
        f"}}"
        f"QCheckBox::indicator:checked {{"
        f"  background: {theme.accent}; border-color: {theme.accent};"
        f"}}"
    )
    return cb


# ═══════════════════════════════════════════════════════════════════════════
#  ResumeView
# ═══════════════════════════════════════════════════════════════════════════


class ResumeView(QWidget):
    """Visual resume editor — collapsible form left, materials center, preview right."""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.student_repo = StudentRepository()
        self.course_repo = CourseRepository()
        self.exp_repo = ExperienceRepository()
        self.ach_repo = AchievementRepository()
        self.role_repo = RoleRepository()

        self._worker: Optional[ResumeWorker] = None
        self._selected_course_ids: Optional[set] = None
        self._first_load = True
        self._text_edits: Dict[str, QTextEdit] = {}
        self._line_edits: Dict[str, QLineEdit] = {}
        self._checkboxes: Dict[str, QCheckBox] = {}

        # debounce timer
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._regenerate_preview)

        self._setup_ui()
        self.refresh()

    # ── UI setup ────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel("简历工作台")
        title.setStyleSheet(theme.section_title_style(22))
        root.addWidget(title)

        root.addLayout(self._build_toolbar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet(theme.splitter_style())

        splitter.addWidget(self._build_form_editor())
        splitter.addWidget(self._build_candidate_panel())
        splitter.addWidget(self._build_preview_tabs())

        splitter.setSizes([580, 260, 540])
        root.addWidget(splitter, 1)

    def _build_toolbar(self) -> QHBoxLayout:
        tb = QHBoxLayout()
        tb.setSpacing(8)

        self.refresh_btn = QPushButton("刷新预览")
        self.refresh_btn.setStyleSheet(theme.primary_btn_style())
        self.refresh_btn.clicked.connect(self._regenerate_preview)
        tb.addWidget(self.refresh_btn)

        self.ai_star_btn = QPushButton("AI 优化 STAR")
        self.ai_star_btn.setToolTip("用 DeepSeek 将经历改写为 STAR 法则描述")
        self.ai_star_btn.setStyleSheet(
            f"QPushButton {{ background: {theme.purple}; color: white; "
            f"padding: 8px 18px; border-radius: 4px; "
            f"border: 1px solid {theme.purple}; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {theme.purple}; }}"
            f"QPushButton:disabled {{ background: {theme.bg_badge}; "
            f"border-color: {theme.border}; color: {theme.fg_faint}; }}"
        )
        self.ai_star_btn.clicked.connect(self._on_ai_star)
        tb.addWidget(self.ai_star_btn)

        tb.addStretch()

        for label, slot in [
            ("复制 Markdown", self._copy_markdown),
            ("导出 Markdown", self._export_markdown),
            ("导出 HTML", self._export_html),
            ("导出 PDF", self._export_pdf),
            ("浏览器预览", self._preview_browser),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(theme.subtle_btn_style())
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        return tb

    # ── LEFT: form editor with collapsible sections ───────────────────

    def _build_form_editor(self) -> QWidget:
        """Build the left panel: scrollable form with collapsible sections."""
        outer = QFrame()
        outer.setObjectName("contentCard")
        outer.setStyleSheet(
            f"QFrame#contentCard {{"
            f"  background: {theme.bg_card};"
            f"  border: 1px solid {theme.border};"
            f"  border-radius: 8px;"
            f"}}"
        )
        ol = QVBoxLayout(outer)
        ol.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # ── Section: 基本信息 ──
        sec_basic = CollapsibleSection("基本信息", expanded=True)
        cl = sec_basic.content_layout()

        self.name_edit = _make_line_edit("姓名（如：张三）")
        self.name_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["name"] = self.name_edit
        cl.addWidget(self.name_edit)

        self.title_edit = _make_line_edit("身份标题（如：大数据工程师 / 求职岗位）")
        self.title_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["title"] = self.title_edit
        cl.addWidget(self.title_edit)

        row1 = QHBoxLayout()
        self.email_edit = _make_line_edit("邮箱")
        self.email_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["email"] = self.email_edit
        row1.addWidget(self.email_edit)
        self.phone_edit = _make_line_edit("电话")
        self.phone_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["phone"] = self.phone_edit
        row1.addWidget(self.phone_edit)
        cl.addLayout(row1)

        row2 = QHBoxLayout()
        self.city_edit = _make_line_edit("城市（如：北京）")
        self.city_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["city"] = self.city_edit
        row2.addWidget(self.city_edit)
        self.intent_edit = _make_line_edit("求职意向（如：数据工程师）")
        self.intent_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["intent"] = self.intent_edit
        row2.addWidget(self.intent_edit)
        cl.addLayout(row2)

        layout.addWidget(sec_basic)

        # ── Section: 教育信息 ──
        sec_edu = CollapsibleSection("教育信息", expanded=True)
        cl = sec_edu.content_layout()

        row3 = QHBoxLayout()
        self.school_edit = _make_line_edit("学校（如：信息学院）")
        self.school_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["school"] = self.school_edit
        row3.addWidget(self.school_edit)
        self.major_edit = _make_line_edit("专业（如：数据科学与大数据技术）")
        self.major_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["major"] = self.major_edit
        row3.addWidget(self.major_edit)
        cl.addLayout(row3)

        self.degree_edit = _make_line_edit("学历（如：本科 / 硕士）")
        self.degree_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["degree"] = self.degree_edit
        cl.addWidget(self.degree_edit)

        self.summary_edit = _make_text_edit(
            "用 2-4 句话概括学习方向、实践重点和成长亮点。",
            min_h=80,
        )
        self.summary_edit.textChanged.connect(self._on_field_changed)
        self._text_edits["summary"] = self.summary_edit
        cl.addWidget(self.summary_edit)

        layout.addWidget(sec_edu)

        # ── Section: 教育背景描述 ──
        sec_edubody = CollapsibleSection("教育背景描述", expanded=True)
        cl = sec_edubody.content_layout()
        self.education_body_edit = _make_text_edit(
            "• GPA：85/100，专业排名前列\n"
            "• 核心课程：机器学习、数据分析、数据库系统\n"
            "• 荣誉：院级奖学金",
            min_h=100,
        )
        self.education_body_edit.textChanged.connect(self._on_field_changed)
        self._text_edits["education_body"] = self.education_body_edit
        cl.addWidget(self.education_body_edit)
        layout.addWidget(sec_edubody)

        # ── Section: 技能特长 ──
        sec_skills = CollapsibleSection("技能特长", expanded=True)
        cl = sec_skills.content_layout()
        self.skills_body_edit = _make_text_edit(
            "• 熟悉 Python、SQL 与数据分析流程\n"
            "• 能够使用 PySide6、Flask 完成项目开发",
            min_h=100,
        )
        self.skills_body_edit.textChanged.connect(self._on_field_changed)
        self._text_edits["skills_body"] = self.skills_body_edit
        cl.addWidget(self.skills_body_edit)
        layout.addWidget(sec_skills)

        # ── Section: 项目经验 ──
        sec_proj = CollapsibleSection("项目经验", expanded=True)
        cl = sec_proj.content_layout()
        self.project_name_edit = _make_line_edit("项目名称（如：个人发展规划系统）")
        self.project_name_edit.textChanged.connect(self._on_field_changed)
        self._line_edits["project_name"] = self.project_name_edit
        cl.addWidget(self.project_name_edit)

        self.project_body_edit = _make_text_edit(
            "• 负责系统设计、模块拆分与界面实现\n"
            "• 完成课程、经历、目标、AI 助手等模块联动",
            min_h=110,
        )
        self.project_body_edit.textChanged.connect(self._on_field_changed)
        self._text_edits["project_body"] = self.project_body_edit
        cl.addWidget(self.project_body_edit)
        layout.addWidget(sec_proj)

        # ── Section: 实习经历 ──
        sec_intern = CollapsibleSection("实习经历", expanded=True)
        cl = sec_intern.content_layout()
        self.internship_edit = _make_text_edit(
            "• 公司 · 岗位 · 时间\n• 描述职责、方法和成果",
            min_h=100,
        )
        self.internship_edit.textChanged.connect(self._on_field_changed)
        self._text_edits["internship"] = self.internship_edit
        cl.addWidget(self.internship_edit)
        layout.addWidget(sec_intern)

        # ── Section: 竞赛获奖 ──
        sec_awards = CollapsibleSection("竞赛获奖", expanded=False)
        cl = sec_awards.content_layout()
        self.awards_edit = _make_text_edit(
            "• 奖项名称 ｜ 级别 ｜ 颁发机构 ｜ 日期\n• 描述成果价值和影响",
            min_h=100,
        )
        self.awards_edit.textChanged.connect(self._on_field_changed)
        self._text_edits["awards"] = self.awards_edit
        cl.addWidget(self.awards_edit)
        layout.addWidget(sec_awards)

        # ── Section: 补充内容 ──
        sec_custom = CollapsibleSection("补充内容 / 自我评价", expanded=False)
        cl = sec_custom.content_layout()
        self.custom_content_edit = _make_text_edit(
            "可补充个人优势、职业目标、社会活动等。\n"
            "右侧素材面板支持点击插入，你也可以直接编辑。",
            min_h=100,
        )
        self.custom_content_edit.textChanged.connect(self._on_field_changed)
        self._text_edits["custom_content"] = self.custom_content_edit
        cl.addWidget(self.custom_content_edit)
        layout.addWidget(sec_custom)

        # ── Section: 课程选择 ──
        sec_courses = CollapsibleSection("选择展示课程", expanded=False)
        cl = sec_courses.content_layout()
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(4)
        self.course_table.setHorizontalHeaderLabels(["展示", "课程", "学分", "成绩"])
        self.course_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.course_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.course_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.course_table.verticalHeader().setVisible(False)
        self.course_table.setMinimumHeight(160)
        self.course_table.setStyleSheet(theme.table_style())
        cl.addWidget(self.course_table)
        layout.addWidget(sec_courses)

        # ── Section: 分区开关 ──
        sec_toggles = CollapsibleSection("分区开关", expanded=False)
        cl = sec_toggles.content_layout()
        tg_hint = QLabel("控制简历中各区块的显示/隐藏：")
        tg_hint.setStyleSheet(f"color: {theme.fg_muted}; font-size: 11px;")
        cl.addWidget(tg_hint)

        toggles = [
            ("show_intent", "求职意向"),
            ("show_education", "教育背景"),
            ("show_skills", "技能特长"),
            ("show_projects", "项目经验"),
            ("show_internship", "实习经历"),
            ("show_awards", "竞赛获奖"),
            ("show_custom", "补充内容"),
        ]
        for key, label in toggles:
            cb = _make_checkbox(label)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_field_changed)
            self._checkboxes[key] = cb
            cl.addWidget(cb)

        layout.addWidget(sec_toggles)
        layout.addStretch()

        scroll.setWidget(content)
        ol.addWidget(scroll)
        return outer

    # ── CENTER: candidate material browser ──────────────────────────────

    def _build_candidate_panel(self) -> QWidget:
        outer = QFrame()
        outer.setObjectName("contentCard")
        outer.setStyleSheet(
            f"QFrame#contentCard {{"
            f"  background: {theme.bg_card};"
            f"  border: 1px solid {theme.border};"
            f"  border-radius: 8px;"
            f"}}"
        )
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        sec_title = QLabel("备选素材")
        sec_title.setStyleSheet(f"color: {theme.fg}; font-size: 14px; font-weight: 600;")
        layout.addWidget(sec_title)

        hint = QLabel("从已有数据中选内容，点击插入到简历对应区域。")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme.fg_muted}; font-size: 11px;")
        layout.addWidget(hint)

        self.source_combo = QComboBox()
        self.source_combo.setStyleSheet(
            f"QComboBox {{"
            f"  border: 1px solid {theme.border}; border-radius: 4px;"
            f"  padding: 6px 8px; background: {theme.bg_input};"
            f"  color: {theme.fg}; font-size: 13px;"
            f"}}"
        )
        for label, key in CANDIDATE_SOURCES:
            self.source_combo.addItem(label, key)
        self.source_combo.currentIndexChanged.connect(self._populate_candidates)
        layout.addWidget(self.source_combo)

        self.material_list = QListWidget()
        self.material_list.setWordWrap(True)
        self.material_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.material_list.setStyleSheet(
            f"QListWidget {{"
            f"  border: 1px solid {theme.border}; border-radius: 4px;"
            f"  background: {theme.bg_input}; color: {theme.fg};"
            f"  font-size: 12px;"
            f"}}"
            f"QListWidget::item {{ padding: 8px 8px; border-bottom: 1px solid {theme.border}; }}"
            f"QListWidget::item:hover {{ background: {theme.bg_hover}; }}"
            f"QListWidget::item:selected {{ background: {theme.bg_active}; color: {theme.fg}; }}"
        )
        self.material_list.itemDoubleClicked.connect(lambda item: self._insert_candidate())
        layout.addWidget(self.material_list, 1)

        self.insert_btn = QPushButton("插入到教育背景")
        self.insert_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent; border: 1px solid {theme.border};"
            f"  border-radius: 6px; padding: 8px 12px; color: {theme.fg_muted};"
            f"  font-size: 13px;"
            f"}}"
            f"QPushButton:hover {{ background: {theme.bg_active}; color: {theme.accent}; }}"
        )
        self.insert_btn.clicked.connect(self._insert_candidate)
        layout.addWidget(self.insert_btn)

        self.source_combo.currentIndexChanged.connect(self._update_insert_label)
        self._update_insert_label()

        return outer

    def _update_insert_label(self):
        key = self.source_combo.currentData()
        self.insert_btn.setText(SOURCE_TO_LABEL.get(key, "插入到简历"))

    # ── RIGHT: preview tabs ─────────────────────────────────────────────

    def _build_preview_tabs(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.preview_tabs = QTabWidget()
        self.preview_tabs.setStyleSheet(theme.tab_widget_style())

        # HTML tab
        html_tab = QWidget()
        html_layout = QVBoxLayout(html_tab)
        html_layout.setContentsMargins(0, 0, 0, 0)
        self.html_preview = QTextBrowser()
        self.html_preview.setOpenExternalLinks(True)
        self.html_preview.setStyleSheet(
            f"QTextBrowser {{"
            f"  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;"
            f"  font-size: 13px; background: {theme.bg_card};"
            f"  color: {theme.fg}; border: 1px solid {theme.border};"
            f"  border-radius: 4px; padding: 10px;"
            f"}}"
        )
        html_layout.addWidget(self.html_preview)
        self.preview_tabs.addTab(html_tab, "HTML 预览")

        # Markdown tab
        md_tab = QWidget()
        md_layout = QVBoxLayout(md_tab)
        md_layout.setContentsMargins(0, 0, 0, 0)
        md_hint = QLabel("Markdown 格式简历，可直接编辑后复制或导出。")
        md_hint.setStyleSheet(f"color: {theme.fg_muted}; font-size: 11px; padding: 4px 0;")
        md_layout.addWidget(md_hint)
        self.md_edit = QTextEdit()
        self.md_edit.setStyleSheet(
            f"QTextEdit {{"
            f"  font-family: 'Consolas', 'Microsoft YaHei', monospace;"
            f"  font-size: 13px; background: {theme.bg_code};"
            f"  color: {theme.fg}; border: 1px solid {theme.border};"
            f"  border-radius: 4px; padding: 10px;"
            f"}}"
        )
        md_layout.addWidget(self.md_edit)
        self.preview_tabs.addTab(md_tab, "Markdown")

        layout.addWidget(self.preview_tabs, 1)
        return panel

    # ── data flow ───────────────────────────────────────────────────────

    def _on_field_changed(self):
        self._debounce_timer.start()

    def collect_options(self) -> Dict[str, Any]:
        return {
            "name": self.name_edit.text().strip(),
            "title": self.title_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "city": self.city_edit.text().strip(),
            "intent": self.intent_edit.text().strip(),
            "school": self.school_edit.text().strip(),
            "major": self.major_edit.text().strip(),
            "degree": self.degree_edit.text().strip(),
            "summary": self.summary_edit.toPlainText().strip(),
            "education_body": self.education_body_edit.toPlainText().strip(),
            "skills_body": self.skills_body_edit.toPlainText().strip(),
            "project_name": self.project_name_edit.text().strip(),
            "project_body": self.project_body_edit.toPlainText().strip(),
            "internship": self.internship_edit.toPlainText().strip(),
            "awards": self.awards_edit.toPlainText().strip(),
            "custom_content": self.custom_content_edit.toPlainText().strip(),
            "avatar_path": "",
            "section_title_intent": "求职意向",
            "section_title_education": "教育背景",
            "section_title_skills": "技能特长",
            "section_title_projects": "项目经验",
            "section_title_internship": "实习经历",
            "section_title_awards": "竞赛获奖",
            "section_title_custom": "自我评价",
            "show_intent": self._checkboxes.get("show_intent", QCheckBox()).isChecked() if "show_intent" in self._checkboxes else True,
            "show_education": self._checkboxes.get("show_education", QCheckBox()).isChecked() if "show_education" in self._checkboxes else True,
            "show_skills": self._checkboxes.get("show_skills", QCheckBox()).isChecked() if "show_skills" in self._checkboxes else True,
            "show_projects": self._checkboxes.get("show_projects", QCheckBox()).isChecked() if "show_projects" in self._checkboxes else True,
            "show_internship": self._checkboxes.get("show_internship", QCheckBox()).isChecked() if "show_internship" in self._checkboxes else True,
            "show_awards": self._checkboxes.get("show_awards", QCheckBox()).isChecked() if "show_awards" in self._checkboxes else True,
            "show_custom": self._checkboxes.get("show_custom", QCheckBox()).isChecked() if "show_custom" in self._checkboxes else True,
        }

    def load_options(self, options: Dict[str, Any]):
        """Load a dict into form fields without triggering signals."""
        for edit, key in [
            (self.name_edit, "name"),
            (self.title_edit, "title"),
            (self.email_edit, "email"),
            (self.phone_edit, "phone"),
            (self.city_edit, "city"),
            (self.intent_edit, "intent"),
            (self.school_edit, "school"),
            (self.major_edit, "major"),
            (self.degree_edit, "degree"),
            (self.project_name_edit, "project_name"),
        ]:
            edit.blockSignals(True)
            edit.setText(str(options.get(key, "")))
            edit.blockSignals(False)

        for edit, key in [
            (self.summary_edit, "summary"),
            (self.education_body_edit, "education_body"),
            (self.skills_body_edit, "skills_body"),
            (self.project_body_edit, "project_body"),
            (self.internship_edit, "internship"),
            (self.awards_edit, "awards"),
            (self.custom_content_edit, "custom_content"),
        ]:
            edit.blockSignals(True)
            edit.setPlainText(str(options.get(key, "")))
            edit.blockSignals(False)

        for key, cb in self._checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(options.get(key, True))
            cb.blockSignals(False)

    # ── refresh ─────────────────────────────────────────────────────────

    def refresh(self):
        self._load_courses()

        if self._first_load:
            self._first_load = False
            student = self.student_repo.get()
            courses = self.course_repo.get_all()
            overview = calculate_grade_overview(courses)
            experiences = self.exp_repo.get_all()
            achievements = self.ach_repo.get_all()
            roles = self.role_repo.get_all()
            defaults = compute_default_options(
                student=student, courses=courses, overview=overview,
                experiences=experiences, achievements=achievements, roles=roles,
            )
            self.load_options(defaults)

        self._populate_candidates()
        self._regenerate_preview()

    def _selected_courses(self) -> list:
        all_courses = sorted(self.course_repo.get_all(), key=lambda c: c.grade, reverse=True)
        selected = []
        for row, course in enumerate(all_courses):
            cb = self.course_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                selected.append(course)
        return selected

    def _load_courses(self):
        courses = sorted(self.course_repo.get_all(), key=lambda c: c.grade, reverse=True)
        self.course_table.setRowCount(len(courses))
        restore_ids = self._selected_course_ids
        if restore_ids is None:
            default_ids = {c.course_id for c in courses[:8]}
        else:
            default_ids = restore_ids

        for row, course in enumerate(courses):
            checkbox = QCheckBox()
            checkbox.setChecked(course.course_id in default_ids)
            checkbox.stateChanged.connect(self._on_course_checkbox_changed)
            self.course_table.setCellWidget(row, 0, checkbox)
            self.course_table.setItem(row, 1, QTableWidgetItem(course.name))
            self.course_table.setItem(row, 2, QTableWidgetItem(f"{course.credit:g}"))
            self.course_table.setItem(row, 3, QTableWidgetItem(f"{course.grade:g}"))
        self.course_table.resizeColumnsToContents()

    def _on_course_checkbox_changed(self):
        self._selected_course_ids = self._collect_checked_ids()

    def _collect_checked_ids(self) -> set:
        ids = set()
        all_courses = sorted(self.course_repo.get_all(), key=lambda c: c.grade, reverse=True)
        for row, course in enumerate(all_courses):
            cb = self.course_table.cellWidget(row, 0)
            if cb and cb.isChecked():
                ids.add(course.course_id)
        return ids

    # ── preview generation ─────────────────────────────────────────────

    def _regenerate_preview(self):
        options = self.collect_options()
        student = self.student_repo.get()
        courses = self._selected_courses()
        all_courses = self.course_repo.get_all()
        overview = calculate_grade_overview(all_courses)
        experiences = self.exp_repo.get_all()
        achievements = self.ach_repo.get_all()
        roles = self.role_repo.get_all()

        html = build_new_html(
            options=options, student=student, courses=courses,
            overview=overview, experiences=experiences,
            achievements=achievements, roles=roles,
        )
        self.html_preview.setHtml(html)

        md = build_new_md(
            options=options, student=student, courses=courses,
            overview=overview, experiences=experiences,
            achievements=achievements, roles=roles,
        )
        self.md_edit.setPlainText(md)

        self._save_to_student(options)

    def _save_to_student(self, options: Dict[str, Any]):
        student = self.student_repo.get()
        if student is None:
            return
        student.name = options.get("name") or student.name
        student.email = options.get("email") or student.email
        student.phone = options.get("phone") or student.phone
        student.college = options.get("school") or student.college
        student.major = options.get("major") or student.major
        student.summary = options.get("summary") or student.summary
        student.skills = options.get("skills_body") or student.skills
        self.student_repo.save(student)

    # ── candidate panel ────────────────────────────────────────────────

    def _populate_candidates(self):
        self.material_list.clear()
        key = self.source_combo.currentData()
        if not key:
            return

        if key == "course":
            for c in self.course_repo.get_all():
                title = c.name
                detail = f"{c.semester or '学期'} · {c.credit:.1f}学分 · {c.grade:g}分"
                snippet = (
                    f"课程：{c.name}（{c.semester or '学期待补充'}），"
                    f"学分{c.credit:.1f}，成绩{c.grade:g}。"
                    f"{c.note or '可突出学习成果与方法。'}"
                )
                self._add_item(title, detail, snippet)

        elif key == "experience":
            for e in self.exp_repo.get_all():
                title = e.title
                dates = f"{e.start_date} - {e.end_date}".strip(" -")
                detail = f"{e.exp_type} · {e.organization or '组织'} · {dates}"
                snippet = (
                    f"经历：在{e.organization or '相关组织'}参与{e.title}，"
                    f"担任{e.role or '核心成员'}。"
                    f"{e.description or '可突出项目职责、方法与结果。'}"
                )
                self._add_item(title, detail, snippet)

        elif key == "achievement":
            for a in self.ach_repo.get_all():
                title = a.title
                detail = f"{a.ach_type} · {a.issuer or '颁发机构'} · {a.date}"
                snippet = (
                    f"获奖：{a.title}（{a.ach_type}，{a.issuer or '待补充'}）。"
                    f"{a.description or '可突出成果价值与影响。'}"
                )
                self._add_item(title, detail, snippet)

        elif key == "role":
            for r in self.role_repo.get_all():
                title = r.title
                detail = f"{r.role_type} · {r.organization or '组织'}"
                snippet = (
                    f"角色：在{r.organization or '相关组织'}担任{r.title}"
                    f"（{r.role_type}）。"
                    f"{r.description or '可强调组织协调与执行成果。'}"
                )
                self._add_item(title, detail, snippet)

    def _add_item(self, title: str, detail: str, snippet: str):
        item = QListWidgetItem(f"{title}\n{detail}", self.material_list)
        item.setData(Qt.ItemDataRole.UserRole, snippet)
        item.setToolTip(snippet)

    def _insert_candidate(self):
        current = self.material_list.currentItem()
        if not current:
            QMessageBox.information(self, "提示", "请先选择一条素材。")
            return
        snippet = current.data(Qt.ItemDataRole.UserRole)
        if not snippet:
            return
        key = self.source_combo.currentData()
        attr = SOURCE_TO_EDITOR.get(key, "custom_content")
        target: QTextEdit = getattr(self, f"{attr}", self.custom_content_edit)
        existing = target.toPlainText().strip()
        if existing:
            target.setPlainText(existing + "\n• " + snippet)
        else:
            target.setPlainText("• " + snippet)
        cursor = target.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        target.setTextCursor(cursor)
        self.material_list.setCurrentRow(-1)

    # ── AI STAR ─────────────────────────────────────────────────────────

    def _on_ai_star(self):
        experiences = self.exp_repo.get_all()
        if not experiences:
            QMessageBox.information(self, "提示", "还没有录入经历。请先在「经历管理」中添加。")
            return
        reply = QMessageBox.question(
            self, "AI 优化 STAR",
            f"将对 {len(experiences)} 条经历用 STAR 法则改写。继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.ai_star_btn.setEnabled(False)
        self.ai_star_btn.setText("优化中…")
        self._worker = ResumeWorker("rewrite_all_experiences", experiences, parent=self)
        self._worker.finished.connect(self._on_star_done)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_star_done(self, text: str):
        self.ai_star_btn.setEnabled(True)
        self.ai_star_btn.setText("AI 优化 STAR")
        if text.startswith("请求失败") or text.startswith("尚未配置"):
            QMessageBox.warning(self, "优化失败", text)
            return
        self.preview_tabs.setCurrentIndex(1)
        self.md_edit.setPlainText(
            "## AI STAR 优化结果\n\n" + text
            + "\n\n---\n\n复制上方优化描述，回到「经历管理」逐条粘贴替换。"
        )

    # ── export actions ──────────────────────────────────────────────────

    def _copy_markdown(self):
        md = self.md_edit.toPlainText().strip()
        if not md:
            self._regenerate_preview()
            md = self.md_edit.toPlainText().strip()
        QApplication.clipboard().setText(md)
        QMessageBox.information(self, "已复制", "Markdown 简历已复制到剪贴板。")

    def _export_markdown(self):
        md = self.md_edit.toPlainText().strip()
        if not md:
            self._regenerate_preview()
            md = self.md_edit.toPlainText().strip()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出 Markdown 简历", "个人简历.md",
            "Markdown Files (*.md);;All Files (*)",
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
            QMessageBox.information(self, "导出成功", f"简历已保存到:\n{filepath}")
        except OSError as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def _current_html_document(self) -> str:
        return HTML_DOCUMENT_TEMPLATE.format(body=self.html_preview.toHtml())

    def _export_html(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出 HTML 简历", "个人简历.html", "HTML Files (*.html)",
        )
        if not filepath:
            return
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self._current_html_document())
            QMessageBox.information(self, "导出成功", f"简历已保存到:\n{filepath}")
        except OSError as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def _export_pdf(self):
        """Export resume as PDF via QPrinter."""
        options = self.collect_options()
        student = self.student_repo.get()
        courses = self._selected_courses()
        all_courses = self.course_repo.get_all()
        overview = calculate_grade_overview(all_courses)
        experiences = self.exp_repo.get_all()
        achievements = self.ach_repo.get_all()
        roles = self.role_repo.get_all()

        html = build_new_html(
            options=options, student=student, courses=courses,
            overview=overview, experiences=experiences,
            achievements=achievements, roles=roles,
        )

        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出 PDF 简历", "个人简历.pdf", "PDF Files (*.pdf)",
        )
        if not filepath:
            return

        ok = export_html_to_pdf(html, filepath)
        if ok:
            QMessageBox.information(self, "导出成功", f"PDF 简历已保存到:\n{filepath}")
        else:
            QMessageBox.critical(self, "错误", "PDF 导出失败，请检查 PySide6 QtPrintSupport 模块。")

    def _preview_browser(self):
        try:
            tmp = os.path.join(tempfile.gettempdir(), "pdptool_resume_preview.html")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(self._current_html_document())
            webbrowser.open(f"file://{tmp}")
        except OSError as e:
            QMessageBox.critical(self, "错误", f"预览失败: {e}")
