"""Curriculum completion audit service.

Reads a markdown training plan and compares it with imported transcript courses.
The audit is code-first: course codes such as BDT220 or MAT108 are matched
against the student's course records, then credits are summed by requirement.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

from ..models.course import Course


@dataclass
class Requirement:
    """One curriculum requirement item."""

    module: str
    name: str
    required_credits: float
    course_codes: Set[str] = field(default_factory=set)
    course_names: Set[str] = field(default_factory=set)


@dataclass
class RequirementResult:
    """Completion result for one requirement item."""

    requirement: Requirement
    earned_credits: float
    matched_courses: List[Course]
    missing_codes: List[str]

    @property
    def remaining_credits(self) -> float:
        return max(0.0, self.requirement.required_credits - self.earned_credits)

    @property
    def completion_ratio(self) -> float:
        required = self.requirement.required_credits
        return min(1.0, self.earned_credits / required) if required > 0 else 1.0


@dataclass
class ModuleResult:
    """Completion result for a top-level curriculum module."""

    name: str
    required_credits: float
    earned_credits: float
    requirements: List[RequirementResult]

    @property
    def remaining_credits(self) -> float:
        return max(0.0, self.required_credits - self.earned_credits)

    @property
    def completion_ratio(self) -> float:
        return min(1.0, self.earned_credits / self.required_credits) if self.required_credits else 1.0


@dataclass
class CategoryAuditResult:
    """Dashboard-oriented audit result for one curriculum category."""

    name: str
    required_credits: float
    earned_credits: float
    courses: List[Course]
    missing_codes: List[str] = field(default_factory=list)
    note: str = ""

    @property
    def remaining_credits(self) -> float:
        if self.required_credits <= 0:
            return 0.0
        return max(0.0, self.required_credits - self.earned_credits)

    @property
    def completion_ratio(self) -> float:
        if self.required_credits <= 0:
            return 1.0 if self.earned_credits > 0 else 0.0
        return min(1.0, self.earned_credits / self.required_credits)


class CurriculumAuditor:
    """Audit transcript courses against a markdown curriculum plan."""

    CODE_PATTERN = re.compile(r"(?<![A-Z0-9])[A-Z]{2,4}\d{3}(?![A-Z0-9])")

    DASHBOARD_CATEGORIES = [
        ("政治理论与思想品德", 19),
        ("英语", 20),
        ("体育与健康", 4),
        ("新生研讨课", 1),
        ("核心通识课程", 4),
        ("美育通识课程", 2),
        ("非美育通识课程", 8),
        ("数学", 18),
        ("经管法基础", 6),
        ("职业发展与创新创业", 2),
        ("学科基础必修课", 32),
        ("学科基础选修课", 13),
        ("专业方向必修课", 16),
    ]

    # ── plan path resolution ──────────────────────────────────────

    _PROJECT_ROOT = os.path.dirname(
        os.path.dirname(os.path.dirname(__file__))
    )
    _DEFAULT_PLAN = os.path.join(_PROJECT_ROOT, "大数据专业培养方案要求学分.md")
    _PLANS_DIR = os.path.join(_PROJECT_ROOT, "training_plans")

    @classmethod
    def _resolve_plan_path(cls, plan_year: str | None) -> str:
        """Return the best plan file path for a given cohort year."""
        year = (plan_year or "").strip()
        if year:
            candidate = os.path.join(cls._PLANS_DIR, f"{year}.md")
            if os.path.exists(candidate):
                return candidate
        return cls._DEFAULT_PLAN

    @classmethod
    def load_plan_text(cls, plan_year: str | None = None) -> str:
        """Read the raw training plan markdown — used by the AI assistant."""
        path = cls._resolve_plan_path(plan_year)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "(培养方案文件不可用)"

    def __init__(self, plan_year: str | None = None, plan_path: str | None = None):
        self.plan_year = (plan_year or "").strip()
        if plan_path is not None:
            self.plan_path = plan_path
        else:
            self.plan_path = self._resolve_plan_path(self.plan_year)

    def audit(self, courses: List[Course]) -> List[ModuleResult]:
        modules, requirements = self._load_requirements()
        course_by_code = self._course_by_code(courses)
        used_course_ids = set()
        module_results: List[ModuleResult] = []

        for module_name, required_credits in modules.items():
            req_results = []
            module_earned = 0.0
            for req in [r for r in requirements if r.module == module_name]:
                matched = []
                for code in sorted(req.course_codes):
                    course = course_by_code.get(code)
                    if course and id(course) not in used_course_ids:
                        matched.append(course)
                        used_course_ids.add(id(course))

                earned = min(sum(c.credit for c in matched), req.required_credits)
                module_earned += earned
                matched_codes = {(c.code or "").upper().strip() for c in matched}
                missing_codes = sorted(req.course_codes - matched_codes)
                req_results.append(RequirementResult(req, earned, matched, missing_codes))

            module_results.append(ModuleResult(
                name=module_name,
                required_credits=required_credits,
                earned_credits=min(module_earned, required_credits),
                requirements=req_results,
            ))

        return module_results

    def audit_dashboard_categories(self, courses: List[Course]) -> List[CategoryAuditResult]:
        """Classify transcript courses into dashboard curriculum categories."""
        _, requirements = self._load_requirements()
        code_sets = self._dashboard_code_sets(requirements)
        name_sets = self._dashboard_name_sets(requirements)
        results: List[CategoryAuditResult] = []
        used_ids = set()

        for name, required in self.DASHBOARD_CATEGORIES:
            matched = []
            for course in courses:
                if id(course) in used_ids:
                    continue
                if self._matches_dashboard_category(
                    course,
                    name,
                    code_sets.get(name, set()),
                    name_sets.get(name, set()),
                ):
                    matched.append(course)
                    used_ids.add(id(course))

            earned = min(sum(c.credit for c in matched), float(required))
            matched_codes = {(c.code or "").upper().strip() for c in matched if c.code}
            missing_codes = sorted(code_sets.get(name, set()) - matched_codes)
            matched_names = {self._normalize_name(c.name) for c in matched if c.name}
            missing_names = sorted(
                display for display in name_sets.get(name, set())
                if self._normalize_name(display) not in matched_names
            )
            results.append(CategoryAuditResult(
                name=name,
                required_credits=float(required),
                earned_credits=earned,
                courses=matched,
                missing_codes=missing_names[:12] or missing_codes[:12],
                note=self._category_note(name),
            ))

        plan_out = [course for course in courses if id(course) not in used_ids]
        results.append(CategoryAuditResult(
            name="计划外",
            required_credits=0,
            earned_credits=sum(c.credit for c in plan_out),
            courses=plan_out,
            note="未被当前培养方案规则匹配的课程，可人工核对后补充分类规则。",
        ))
        return results

    def audit_total(self, courses: List[Course]) -> CategoryAuditResult:
        """Return total 145-credit completion based on dashboard categories."""
        categories = self.audit_dashboard_categories(courses)
        earned = sum(c.earned_credits for c in categories if c.required_credits > 0)
        return CategoryAuditResult(
            name="总课程学分",
            required_credits=145,
            earned_credits=min(earned, 145),
            courses=courses,
            note="按培养方案各分类已匹配学分汇总，计划外课程不计入培养方案完成学分。",
        )

    def _dashboard_code_sets(self, requirements: List[Requirement]) -> Dict[str, Set[str]]:
        def contains(keyword: str) -> Set[str]:
            codes = set()
            for req in requirements:
                if keyword in req.name:
                    codes.update(req.course_codes)
            return codes

        def contains_exact(keyword: str, exclude: str = "") -> Set[str]:
            codes = set()
            for req in requirements:
                if keyword in req.name and (not exclude or exclude not in req.name):
                    codes.update(req.course_codes)
            return codes

        return {
            "核心通识课程": contains("核心通识课程"),
            "美育通识课程": contains_exact("选修通识课程-美育", "非美育"),
            "非美育通识课程": contains("非美育"),
            "数学": contains("数学"),
            "经管法基础": contains("经管法基础"),
            "职业发展与创新创业": contains("职业发展与创新创业"),
            "学科基础必修课": contains("学科基础必修课"),
            "学科基础选修课": contains("学科基础选修课"),
            "专业方向必修课": contains("专业方向必修课"),
            "英语": contains("英语"),
            "体育与健康": contains("体育"),
            "政治理论与思想品德": contains("政治理论与思想品德"),
            "新生研讨课": contains("新生研讨课"),
        }

    def _dashboard_name_sets(self, requirements: List[Requirement]) -> Dict[str, Set[str]]:
        def contains(keyword: str) -> Set[str]:
            names = set()
            for req in requirements:
                if keyword in req.name:
                    names.update(req.course_names)
            return names

        def contains_exact(keyword: str, exclude: str = "") -> Set[str]:
            names = set()
            for req in requirements:
                if keyword in req.name and (not exclude or exclude not in req.name):
                    names.update(req.course_names)
            return names

        return {
            "核心通识课程": contains("核心通识课程"),
            "美育通识课程": contains_exact("选修通识课程-美育", "非美育"),
            "非美育通识课程": contains("非美育"),
            "数学": contains("数学"),
            "经管法基础": contains("经管法基础"),
            "职业发展与创新创业": contains("职业发展与创新创业"),
            "学科基础必修课": contains("学科基础必修课"),
            "学科基础选修课": contains("学科基础选修课"),
            "专业方向必修课": contains("专业方向必修课"),
            "英语": contains("英语"),
            "体育与健康": contains("体育"),
            "政治理论与思想品德": contains("政治理论与思想品德"),
            "新生研讨课": contains("新生研讨课"),
        }

    def _matches_dashboard_category(
        self,
        course: Course,
        category: str,
        codes: Set[str],
        plan_names: Set[str],
    ) -> bool:
        code = (course.code or "").upper().strip()
        name = course.name or ""
        normalized_name = self._normalize_name(name)
        if normalized_name and any(
            self._normalize_name(plan_name) in normalized_name
            or normalized_name in self._normalize_name(plan_name)
            for plan_name in plan_names
        ):
            return True
        if code and code in codes:
            return True

        if category == "政治理论与思想品德":
            return any(key in name for key in (
                "马克思", "毛泽东", "思想道德", "近现代史", "形势与政策",
                "习近平", "思想政治", "中国共产党", "政治理论",
            ))
        if category == "英语":
            return (
                code.startswith("ENG") or
                any(key in name for key in ("英语", "英汉翻译", "口译", "莎士比亚", "跨文化交际"))
            )
        if category == "体育与健康":
            return code.startswith("PED") or any(key in name for key in ("体育", "体质健康", "篮球", "排球", "乒乓球", "游泳", "瑜伽", "武术"))
        if category == "新生研讨课":
            return "新生研讨" in name
        if category == "经管法基础":
            return code == "SEC318" or any(key in name for key in ("投资学", "货币银行学"))
        return False

    @staticmethod
    def _category_note(category: str) -> str:
        notes = {
            "政治理论与思想品德": "培养方案未列完整课程代码，当前按课程名称关键词辅助识别。",
            "英语": "优先用课程名匹配培养方案英语课程，代码 ENG 仅作辅助。",
            "体育与健康": "优先用课程名匹配体育课程，代码 PED 仅作辅助。",
            "计划外": "这类课程不会计入培养方案完成度，但会保留在成绩单和简历数据中。",
        }
        return notes.get(category, "优先按课程名称匹配培养方案，课程代码作为辅助。")

    def _load_requirements(self):
        with open(self.plan_path, "r", encoding="utf-8") as f:
            text = f.read()

        modules: Dict[str, float] = {}
        requirements: List[Requirement] = []
        current_module = ""

        for raw_line in text.splitlines():
            line = raw_line.strip().strip("`")
            if not line:
                continue

            module_match = re.match(r"^(通识课程|通修课程|专业课程)\s+(\d+(?:\.\d+)?)", line)
            if module_match:
                current_module = module_match.group(1)
                modules[current_module] = float(module_match.group(2))
                continue

            req_match = re.match(r"^-\s*(.*?)\s*(\d+(?:\.\d+)?)\s*(?=[（(]|$)", line)
            if not req_match or not current_module:
                continue

            name = req_match.group(1).strip(" -")
            credits = float(req_match.group(2))
            codes = set(self.CODE_PATTERN.findall(line.upper()))
            names = self._extract_course_names(line)
            requirements.append(Requirement(
                module=current_module,
                name=name,
                required_credits=credits,
                course_codes=codes,
                course_names=names,
            ))

        return modules, requirements

    @classmethod
    def _extract_course_names(cls, line: str) -> Set[str]:
        names = set()
        normalized_line = line.replace("，", ",")
        for match in re.finditer(r"([A-Z]{2,4}\d{3})([^,，)）]+)", normalized_line):
            name = match.group(2).strip()
            name = re.sub(r"^[：:\s-]+", "", name)
            if name and "..." not in name:
                names.add(name)
        if "货币银行学" in line:
            names.add("货币银行学")
        return names

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"[\s（）()《》<>:：,，、\-—_·]+", "", (name or "").lower())

    @staticmethod
    def _course_by_code(courses: List[Course]) -> Dict[str, Course]:
        return {
            (course.code or "").upper().strip(): course
            for course in courses
            if (course.code or "").strip()
        }
