"""Dashboard / home page with summary statistics."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..database.repositories.achievement_repo import AchievementRepository
from ..database.repositories.course_repo import CourseRepository
from ..database.repositories.experience_repo import ExperienceRepository
from ..database.repositories.internship_application_repo import (
    InternshipApplicationRepository,
)
from ..database.repositories.role_repo import RoleRepository
from ..database.repositories.student_repo import StudentRepository
from ..services.curriculum_auditor import CurriculumAuditor
from ..services.gpa_calculator import (
    GpaCalculator,
    Standard40Strategy,
    WeightedAverageStrategy,
)
from ..services.insight_analyzer import InsightAnalyzer
from .dialogs.category_detail_dialog import CategoryDetailDialog
from .widgets.category_card import CategoryCard
from .widgets.stat_card import StatCard
from ..utils.theme import theme


class DashboardView(QWidget):
    """Home dashboard showing summary of all data."""

    # Per-audit palette of category colours
    CATEGORY_COLORS = [
        f"{theme.accent}", "{theme.orange}", "{theme.green}", "{theme.fg_muted}",
        f"{theme.gold}", "{theme.accent}", "{theme.orange}", "{theme.green}",
        f"{theme.purple}", "{theme.accent}", "{theme.orange}", "{theme.fg_muted}",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.course_repo = CourseRepository()
        self.exp_repo = ExperienceRepository()
        self.ach_repo = AchievementRepository()
        self.student_repo = StudentRepository()
        self.role_repo = RoleRepository()
        self.internship_repo = InternshipApplicationRepository()
        self.insight_analyzer = InsightAnalyzer()

        student = self.student_repo.get()
        self._plan_year = (
            (student.enrollment_year or "").strip() if student else ""
        )
        self.curriculum_auditor = CurriculumAuditor(plan_year=self._plan_year)

        self._setup_ui()

    # ── Data bundle (loaded once per refresh) ──────────────────────

    def _load_all_data(self):
        """Load all data from repositories in one batch to avoid
        repeated DB round-trips in refresh()."""
        courses = self.course_repo.get_all()
        return {
            "courses": courses,
            "experiences": self.exp_repo.get_all(),
            "achievements": self.ach_repo.get_all(),
            "roles": self.role_repo.get_all(),
            "internships": self.internship_repo.get_all(),
            "student": self.student_repo.get(),
            "total_audit": self.curriculum_auditor.audit_total(courses),
            "categories": self.curriculum_auditor.audit_dashboard_categories(courses),
            "gpa": GpaCalculator(Standard40Strategy()).calculate(courses),
            "weighted": GpaCalculator(WeightedAverageStrategy()).calculate(courses),
        }

    # ── UI construction ────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background-color: {theme.bg}; border: none;")
        outer.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet(f"background-color: {theme.bg};")
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("情况总览")
        title.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {theme.fg}; margin-bottom: 10px;"
        )
        layout.addWidget(title)

        # Student name
        student = self.student_repo.get()
        name = (
            student.name
            if student and student.name != "未设置"
            else "同学"
        )
        welcome = QLabel(f"欢迎，{name}！")
        welcome.setStyleSheet(
            f"font-size: 16px; color: {theme.fg_muted}; margin-bottom: 20px;"
        )
        layout.addWidget(welcome)

        # ── stat cards grid ──
        grid = QGridLayout()
        grid.setSpacing(12)

        self.completion_card = StatCard("培养方案完成度", "0%", f"{theme.accent}")
        grid.addWidget(self.completion_card, 0, 0)

        self.credit_card = StatCard("总课程学分", "0", f"{theme.green}")
        grid.addWidget(self.credit_card, 0, 1)

        self.activity_card = StatCard("经历/荣誉/投递", "0", f"{theme.orange}")
        grid.addWidget(self.activity_card, 1, 0)

        self.gpa_card = StatCard("GPA (4.0制)", "0.00", f"{theme.purple}")
        grid.addWidget(self.gpa_card, 1, 1)

        layout.addLayout(grid)

        # ── quick summary label ──
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            f"font-size: 14px; color: {theme.fg}; background-color: {theme.bg_card}; "
            f"padding: 16px; border-radius: 6px; margin-top: 10px; border: 1px solid {theme.border};"
        )
        layout.addWidget(self.summary_label)

        plan_label = (
            f"培养方案分类审计（{self._plan_year + ' 级方案' if self._plan_year else '默认方案'}）"
        )
        self.curriculum_title = QLabel(plan_label)
        self.curriculum_title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; margin-top: 8px; color: {theme.fg};"
        )
        layout.addWidget(self.curriculum_title)

        if not self._plan_year:
            hint = QLabel(
                "💡 提示：在「个人设置」中设置入学年份后，"
                "将使用对应年级的培养方案进行审计。"
            )
            hint.setStyleSheet(
                f"font-size: 12px; color: {theme.fg_muted}; "
                f"background-color: {theme.warn_bg}; border: 1px solid {theme.warn_border}; "
                "border-radius: 6px; padding: 8px 12px;"
            )
            hint.setWordWrap(True)
            layout.addWidget(hint)

        self.curriculum_grid = QGridLayout()
        self.curriculum_grid.setSpacing(10)
        layout.addLayout(self.curriculum_grid)

        self.curriculum_detail = QLabel()
        self.curriculum_detail.setWordWrap(True)
        self.curriculum_detail.setTextFormat(Qt.TextFormat.RichText)
        self.curriculum_detail.setStyleSheet(
            f"font-size: 13px; color: {theme.fg}; background-color: {theme.ai_bubble}; "
            f"padding: 12px; border-radius: 6px; border: 1px solid {theme.accent};"
        )
        layout.addWidget(self.curriculum_detail)

        self.insight_label = QLabel()
        self.insight_label.setWordWrap(True)
        self.insight_label.setTextFormat(Qt.TextFormat.RichText)
        self.insight_label.setStyleSheet(
            f"font-size: 13px; color: {theme.fg}; background-color: {theme.warn_bg}; "
            f"padding: 14px; border-radius: 6px; border: 1px solid {theme.warn_border}; "
            "margin-top: 15px;"
        )
        layout.addWidget(self.insight_label)

        layout.addStretch()

        # Load initial data
        self.refresh()

    # ── refresh ────────────────────────────────────────────────────

    def refresh(self):
        """Refresh all statistics (called when data changes).

        Loads all data once, then delegates to targeted update methods.
        """
        # re-check plan year in case user changed it in settings
        student = self.student_repo.get()
        new_year = (
            (student.enrollment_year or "").strip() if student else ""
        )
        if new_year != self._plan_year:
            self._plan_year = new_year
            self.curriculum_auditor = CurriculumAuditor(plan_year=new_year)
            plan_label = (
                f"培养方案分类审计（{self._plan_year + ' 级方案' if self._plan_year else '默认方案'}）"
            )
            self.curriculum_title.setText(plan_label)

        data = self._load_all_data()
        self._update_cards(data)
        self._update_summary(data)
        self._update_curriculum_audit(data)
        self._update_insight(data)

    # ── card updates ───────────────────────────────────────────────

    def _update_cards(self, data: dict):
        total_audit = data["total_audit"]
        courses = data["courses"]
        gpa = data["gpa"]

        self.completion_card.value_label.setText(
            f"{round(total_audit.completion_ratio * 100)}%"
        )
        target = total_audit.required_credits
        total_credits = sum(c.credit for c in courses)
        self.credit_card.value_label.setText(f"{total_credits:g}/{target:g}")
        self.activity_card.value_label.setText(
            str(
                len(data["experiences"])
                + len(data["achievements"])
                + len(data["internships"])
            )
        )
        self.gpa_card.value_label.setText(f"{gpa['gpa']:.2f}")

    def _update_summary(self, data: dict):
        courses = data["courses"]
        total_audit = data["total_audit"]
        weighted = data["weighted"]

        total_credits = sum(c.credit for c in courses)
        semesters = len({c.semester for c in courses if c.semester})

        self.summary_label.setText(
            f"总览：培养方案目标 <b>{total_audit.required_credits:g}</b> 学分，"
            f"当前已匹配 <b>{total_audit.earned_credits:g}</b> 学分，"
            f"仍需 <b>{total_audit.remaining_credits:g}</b> 学分。"
            f"&nbsp;&nbsp;|&nbsp;&nbsp; "
            f"成绩单总学分: <b>{total_credits:g}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"涉及学期: <b>{semesters}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"加权平均: <b>{weighted['gpa']:.2f}</b>"
        )

    # ── curriculum audit ───────────────────────────────────────────

    def _update_curriculum_audit(self, data: dict):
        self._clear_layout(self.curriculum_grid)

        categories = [data["total_audit"]] + data["categories"]

        for idx, result in enumerate(categories):
            color = self.CATEGORY_COLORS[idx % len(self.CATEGORY_COLORS)]
            card = CategoryCard(
                result, color, self._show_category_detail
            )
            row = idx // 3
            col = idx % 3
            self.curriculum_grid.addWidget(card, row, col)

        urgent = [
            r
            for r in categories
            if r.required_credits > 0 and r.remaining_credits > 0
        ]
        if urgent:
            lines = [
                f"<b>{item.name}</b>：已完成 {item.earned_credits:g}/"
                f"{item.required_credits:g}，还差 {item.remaining_credits:g}"
                for item in urgent[:5]
            ]
            self.curriculum_detail.setText(
                "当前优先补齐：<br>" + "<br>".join(lines)
            )
        else:
            self.curriculum_detail.setText(
                "当前培养方案分类均已达到目标学分。"
            )

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _show_category_detail(self, result):
        dialog = CategoryDetailDialog(result, self)
        dialog.exec()

    # ── insight ────────────────────────────────────────────────────

    def _update_insight(self, data: dict):
        insight = self.insight_analyzer.analyze(
            data["courses"],
            data["experiences"],
            data["achievements"],
            data["roles"],
        )
        score_text = " ｜ ".join(
            f"{name}: {score}"
            for name, score in insight.category_scores.items()
        )
        highlights = "<br>".join(
            f"• {item}" for item in insight.highlights[:3]
        )
        risks = "<br>".join(f"• {item}" for item in insight.risks[:3])
        suggestions = "<br>".join(
            f"• {item}" for item in insight.suggestions[:4]
        )
        self.insight_label.setText(
            f"<b>记录概览</b><br>"
            f"当前类型：<b>{insight.level}</b>　完整度：<b>{insight.score}/100</b><br>"
            f"<span style=f'color:{theme.fg_muted}'>{{score_text}}</span><br><br>"
            f"<b>亮点</b><br>{highlights}<br><br>"
            f"<b>待补充内容</b><br>{risks}<br><br>"
            f"<b>后续整理</b><br>{suggestions}"
        )
