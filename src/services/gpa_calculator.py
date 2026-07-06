"""GPA calculation with pluggable algorithms.

Usage:
    calc = GpaCalculator(Standard40Strategy())
    gpa = calc.calculate(courses)
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from ..models.course import Course


class GpaStrategy(ABC):
    """Abstract strategy for GPA calculation."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        ...

    @abstractmethod
    def grade_to_point(self, grade: float) -> float:
        """Convert a percentage grade to a grade point."""
        ...

    @abstractmethod
    def description(self) -> str:
        """Description of the grading scheme."""
        ...


# ── Concrete Strategies ─────────────────────────────────────────────

class Standard40Strategy(GpaStrategy):
    """Standard 4.0 scale (common in Chinese universities)."""

    def name(self) -> str:
        return "标准4.0绩点制"

    def description(self) -> str:
        return (
            "90-100 → 4.0 | 85-89 → 3.7 | 82-84 → 3.3 | "
            "78-81 → 3.0 | 75-77 → 2.7 | 72-74 → 2.3 | "
            "68-71 → 2.0 | 64-67 → 1.5 | 60-63 → 1.0 | <60 → 0"
        )

    def grade_to_point(self, grade: float) -> float:
        if grade >= 90:
            return 4.0
        elif grade >= 85:
            return 3.7
        elif grade >= 82:
            return 3.3
        elif grade >= 78:
            return 3.0
        elif grade >= 75:
            return 2.7
        elif grade >= 72:
            return 2.3
        elif grade >= 68:
            return 2.0
        elif grade >= 64:
            return 1.5
        elif grade >= 60:
            return 1.0
        else:
            return 0.0


class WeightedAverageStrategy(GpaStrategy):
    """Simple weighted average (100-point scale)."""

    def name(self) -> str:
        return "加权平均分"

    def description(self) -> str:
        return "直接计算学分加权的平均分数（百分制）"

    def grade_to_point(self, grade: float) -> float:
        return grade  # Identity — keep as percentage


class ArithmeticAverageStrategy(GpaStrategy):
    """Simple arithmetic average (100-point scale)."""

    def name(self) -> str:
        return "算术平均分"

    def description(self) -> str:
        return "不按学分加权，直接计算所有课程成绩的算术平均分（百分制）"

    def grade_to_point(self, grade: float) -> float:
        return grade


class GpaCalculator:
    """GPA calculator. Call set_strategy() to switch algorithms at runtime."""

    def __init__(self, strategy: GpaStrategy = None):
        self.strategy = strategy or Standard40Strategy()

    def set_strategy(self, strategy: GpaStrategy) -> None:
        """Switch the GPA calculation strategy at runtime."""
        self.strategy = strategy

    def calculate(self, courses: List[Course]) -> Dict:
        """Calculate GPA for a list of courses.

        Courses with grade < 0 are "在修" (in-progress) — excluded from GPA.
        Courses with grade == 60 may be pass/fail "通过" — excluded from GPA.

        Returns a dict with:
            - gpa: overall GPA
            - total_credits: total credits considered (scored + pass/fail + in-progress)
            - scored_credits: credits contributing to GPA
            - weighted_sum: sum of (grade_point * credit)
            - course_count: total number of courses
            - scored_count: courses with numeric scores
            - by_semester: {semester: {gpa, credits, count}}
        """
        if not courses:
            return {
                "gpa": 0.0, "total_credits": 0, "scored_credits": 0,
                "weighted_sum": 0.0, "course_count": 0, "scored_count": 0,
                "by_semester": {},
            }

        total_weighted = 0.0
        scored_credits = 0.0
        total_credits = 0.0
        scored_count = 0
        by_semester: Dict[str, Dict] = {}

        for course in courses:
            total_credits += course.credit

            # skip in-progress and pass/fail for GPA calculation
            if course.is_in_progress or course.is_pass_fail:
                continue
            if course.credit <= 0 and not isinstance(self.strategy, ArithmeticAverageStrategy):
                continue

            point = self.strategy.grade_to_point(course.grade)
            if isinstance(self.strategy, ArithmeticAverageStrategy):
                weighted = point
                credit_weight = 1.0
            else:
                weighted = point * course.credit
                credit_weight = course.credit
            total_weighted += weighted
            scored_credits += credit_weight
            scored_count += 1

            sem = course.semester or "未知学期"
            if sem not in by_semester:
                by_semester[sem] = {"weighted_sum": 0.0, "credits": 0.0, "count": 0}
            by_semester[sem]["weighted_sum"] += weighted
            by_semester[sem]["credits"] += credit_weight
            by_semester[sem]["count"] += 1

        for sem in by_semester:
            c = by_semester[sem]["credits"]
            by_semester[sem]["gpa"] = (
                round(by_semester[sem]["weighted_sum"] / c, 2) if c > 0 else 0.0
            )

        overall_gpa = round(total_weighted / scored_credits, 2) if scored_credits > 0 else 0.0

        return {
            "gpa": overall_gpa,
            "total_credits": total_credits,
            "scored_credits": scored_credits,
            "weighted_sum": round(total_weighted, 2),
            "course_count": len(courses),
            "scored_count": scored_count,
            "by_semester": by_semester,
        }

    @staticmethod
    def available_strategies() -> List[GpaStrategy]:
        """Return all available GPA strategies."""
        return [
            Standard40Strategy(),
            WeightedAverageStrategy(),
            ArithmeticAverageStrategy(),
        ]


def calculate_grade_overview(courses: List[Course]) -> Dict:
    """Return the three metrics used by the GPA page."""
    gpa = GpaCalculator(Standard40Strategy()).calculate(courses)
    weighted = GpaCalculator(WeightedAverageStrategy()).calculate(courses)
    arithmetic = GpaCalculator(ArithmeticAverageStrategy()).calculate(courses)
    return {
        "gpa": gpa["gpa"],
        "weighted_average": weighted["gpa"],
        "arithmetic_average": arithmetic["gpa"],
        "total_credits": weighted["total_credits"],
        "course_count": len(courses),
    }


def calculate_semester_trend(courses: List[Course]) -> List[Dict]:
    """Calculate per-semester GPA, weighted average, and arithmetic average."""
    semesters = sorted({c.semester or "未知学期" for c in courses})
    trend = []
    for semester in semesters:
        sem_courses = [c for c in courses if (c.semester or "未知学期") == semester]
        overview = calculate_grade_overview(sem_courses)
        trend.append({"semester": semester, **overview})
    return trend
