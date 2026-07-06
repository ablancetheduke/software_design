"""Unit tests for curriculum completion audit."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.course import Course
from src.services.curriculum_auditor import CurriculumAuditor


def test_curriculum_auditor_loads_plan():
    auditor = CurriculumAuditor()
    modules, requirements = auditor._load_requirements()

    assert modules["通识课程"] == 14
    assert modules["通修课程"] == 70
    assert modules["专业课程"] == 61
    assert any("BDT220" in req.course_codes for req in requirements)


def test_curriculum_auditor_matches_course_codes():
    auditor = CurriculumAuditor()
    results = auditor.audit([
        Course(name="软件体系结构与设计模式", code="BDT220", credit=3, grade=90),
        Course(name="高等数学（一）", code="MAT108", credit=5, grade=88),
    ])

    professional = next(r for r in results if r.name == "专业课程")
    common = next(r for r in results if r.name == "通修课程")

    assert professional.earned_credits > 0
    assert common.earned_credits > 0
    assert professional.remaining_credits < professional.required_credits


def test_dashboard_categories_classify_courses():
    auditor = CurriculumAuditor()
    results = auditor.audit_dashboard_categories([
        Course(name="软件体系结构与设计模式", code="BDT220", credit=3, grade=90),
        Course(name="高等数学（一）", code="MAT108", credit=5, grade=88),
        Course(name="大学英语", code="ENG595", credit=4, grade=86),
        Course(name="体育基础", code="PED001", credit=1, grade=92),
    ])

    by_name = {item.name: item for item in results}
    assert by_name["学科基础必修课"].earned_credits == 3
    assert by_name["数学"].earned_credits == 5
    assert by_name["英语"].earned_credits == 4
    assert by_name["体育与健康"].earned_credits == 1


def test_dashboard_categories_prefer_course_names():
    auditor = CurriculumAuditor()
    results = auditor.audit_dashboard_categories([
        Course(name="软件体系结构与设计模式", code="", credit=3, grade=90),
        Course(name="高等数学（一）", code="", credit=5, grade=88),
        Course(name="大学英语自主听力", code="", credit=2, grade=86),
    ])

    by_name = {item.name: item for item in results}
    assert by_name["学科基础必修课"].earned_credits == 3
    assert by_name["数学"].earned_credits == 5
    assert by_name["英语"].earned_credits == 2
