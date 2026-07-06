"""Personal development record summary service.

Turns course, experience, achievement, and role records into a compact
local summary for the dashboard.
"""

from dataclasses import dataclass
from typing import List, Dict

from ..models.course import Course
from ..models.experience import Experience
from ..models.achievement import Achievement
from ..models.role import Role
from .gpa_calculator import GpaCalculator, Standard40Strategy


@dataclass
class DevelopmentInsight:
    """Summary of a student's current development profile."""

    level: str
    score: int
    highlights: List[str]
    risks: List[str]
    suggestions: List[str]
    category_scores: Dict[str, int]


class InsightAnalyzer:
    """Analyze PDP records and produce a local record summary."""

    def analyze(
        self,
        courses: List[Course],
        experiences: List[Experience],
        achievements: List[Achievement],
        roles: List[Role],
    ) -> DevelopmentInsight:
        gpa = GpaCalculator(Standard40Strategy()).calculate(courses)["gpa"]
        total_credits = sum(c.credit for c in courses)

        course_score = self._clamp(int(total_credits * 1.5 + gpa * 12), 0, 100)
        practice_score = self._clamp(len(experiences) * 22, 0, 100)
        honor_score = self._clamp(len(achievements) * 25, 0, 100)
        leadership_score = self._clamp(len(roles) * 25, 0, 100)

        category_scores = {
            "课程积累": course_score,
            "实践经历": practice_score,
            "荣誉成果": honor_score,
            "组织角色": leadership_score,
        }
        score = round(sum(category_scores.values()) / len(category_scores))
        level = self._level(score)

        highlights = self._build_highlights(
            courses, experiences, achievements, roles, gpa, total_credits
        )
        risks = self._build_risks(courses, experiences, achievements, roles, gpa)
        suggestions = self._build_suggestions(
            courses, experiences, achievements, roles, gpa, category_scores
        )

        return DevelopmentInsight(
            level=level,
            score=score,
            highlights=highlights,
            risks=risks,
            suggestions=suggestions,
            category_scores=category_scores,
        )

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(high, value))

    @staticmethod
    def _level(score: int) -> str:
        if score >= 80:
            return "发展均衡型"
        if score >= 60:
            return "稳步成长型"
        if score >= 40:
            return "待完善型"
        return "起步记录型"

    @staticmethod
    def _build_highlights(courses, experiences, achievements, roles, gpa, total_credits):
        highlights = []
        if courses:
            highlights.append(f"已记录 {len(courses)} 门课程，累计 {total_credits:g} 学分。")
        if gpa >= 3.5:
            highlights.append(f"GPA 达到 {gpa:.2f}，课程表现较突出。")
        if experiences:
            types = sorted({e.exp_type for e in experiences if e.exp_type})
            highlights.append(f"实践经历覆盖 {len(types)} 类：{'、'.join(types)}。")
        if achievements:
            highlights.append(f"已有 {len(achievements)} 项荣誉/证书，可用于简历展示。")
        if roles:
            highlights.append(f"记录了 {len(roles)} 段组织角色，体现协作与责任经历。")
        return highlights or ["当前数据较少，可先导入课程和经历形成个人档案。"]

    @staticmethod
    def _build_risks(courses, experiences, achievements, roles, gpa):
        risks = []
        if len(courses) < 5:
            risks.append("课程记录偏少，难以体现四年学习轨迹。")
        if courses and gpa < 2.5:
            risks.append("当前 GPA 偏低，可标记薄弱课程并制定复盘计划。")
        if not experiences:
            risks.append("缺少竞赛、项目、实习或科研经历，简历支撑会偏弱。")
        if not achievements:
            risks.append("暂无荣誉/证书记录，成果展示维度不足。")
        if not roles:
            risks.append("暂无班级、社团或志愿者角色记录，组织协作维度不足。")
        return risks or ["暂未发现明显短板，可以继续保持记录频率。"]

    @staticmethod
    def _build_suggestions(courses, experiences, achievements, roles, gpa, scores):
        suggestions = []
        weakest = min(scores, key=scores.get)
        suggestions.append(f"当前「{weakest}」记录较少，可优先补充。")
        if len(courses) >= 3:
            low_courses = [c.name for c in courses if c.grade and c.grade < 75]
            if low_courses:
                suggestions.append(f"低分课程可单独复盘：{'、'.join(low_courses[:3])}。")
        if not any(e.exp_type in ("项目", "科研", "实习") for e in experiences):
            suggestions.append("可补充一个项目、科研或实习经历，便于简历展示。")
        if not achievements:
            suggestions.append("可以把证书、竞赛参与证明、课程项目奖项也纳入荣誉成果。")
        if gpa >= 3.5 and experiences:
            suggestions.append("课程和实践基础较好，可在简历导出中突出核心课程与项目成果。")
        return suggestions[:4]
