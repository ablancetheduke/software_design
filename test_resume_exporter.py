"""Unit tests for resume_exporter service."""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.resume_exporter import (
    build_resume_html,
    build_resume_markdown,
    build_resume_json,
    compute_default_options,
)
from src.models.student import Student
from src.models.course import Course
from src.models.experience import Experience
from src.models.achievement import Achievement
from src.models.role import Role


# ── test fixtures ──────────────────────────────────────────────────────

def _make_student():
    return Student(
        student_id=1,
        name="张三",
        college="信息学院",
        major="数据科学与大数据技术",
        enrollment_year="2024",
        email="zhangsan@example.com",
        phone="13800000000",
        skills="Python, SQL, 数据分析",
        summary="热爱数据科学的大二学生。",
    )


def _make_courses():
    return [
        Course(course_id=1, name="高等数学", code="MAT108", credit=4.0, grade=92, semester="大一上"),
        Course(course_id=2, name="Python程序设计", code="CMP104", credit=3.0, grade=88, semester="大一上"),
        Course(course_id=3, name="线性代数", code="MAT109", credit=3.0, grade=78, semester="大一下"),
    ]


def _make_experiences():
    return [
        Experience(
            exp_id=1, title="数据分析项目", exp_type="项目",
            organization="信息学院", start_date="2025-03", end_date="2025-06",
            description="使用Python分析用户行为数据", role="组长", outcome="获院级优秀项目",
        ),
        Experience(
            exp_id=2, title="暑期实习", exp_type="实习",
            organization="某科技公司", start_date="2025-07", end_date="2025-09",
            description="负责数据清洗与报表开发", role="数据实习生", outcome="",
        ),
    ]


def _make_achievements():
    return [
        Achievement(
            ach_id=1, title="优秀学生奖学金", ach_type="奖学金",
            issuer="信息学院", date="2025-09", description="成绩排名前10%",
        ),
        Achievement(
            ach_id=2, title="数学建模竞赛二等奖", ach_type="奖项",
            issuer="中国数学会", date="2025-06", description="",
        ),
    ]


def _make_roles():
    return [
        Role(
            role_id=1, title="班级学习委员", role_type="班级代表",
            organization="数据科学2401班", start_date="2024-09", end_date="",
            description="组织学习小组，联系任课教师。",
        ),
    ]


def _make_options():
    return {
        "name": "张三",
        "title": "数据工程师",
        "email": "zhangsan@example.com",
        "phone": "13800000000",
        "city": "北京",
        "intent": "大数据工程师",
        "school": "信息学院",
        "major": "数据科学与大数据技术",
        "degree": "本科",
        "summary": "热爱数据科学的大二学生。",
        "education_body": "• GPA：86.00/100\n• 核心课程：高等数学、Python程序设计",
        "skills_body": "• Python, SQL, 数据分析",
        "project_name": "数据分析项目",
        "project_body": "• 使用Python分析用户行为数据\n• 负责数据清洗与可视化",
        "internship": "• 某科技公司 · 数据实习生 · 2025暑",
        "awards": "• 优秀学生奖学金 ｜ 奖学金 ｜ 信息学院",
        "custom_content": "自我评价补充内容。",
        "section_title_intent": "求职意向",
        "section_title_education": "教育背景",
        "section_title_skills": "技能特长",
        "section_title_projects": "项目经验",
        "section_title_internship": "实习经历",
        "section_title_awards": "竞赛获奖",
        "section_title_custom": "自我评价",
        "avatar_path": "",
        "show_intent": True,
        "show_education": True,
        "show_skills": True,
        "show_projects": True,
        "show_internship": True,
        "show_awards": True,
        "show_custom": True,
    }


# ── compute_default_options ────────────────────────────────────────────

def test_compute_default_options_fills_student():
    student = _make_student()
    opts = compute_default_options(student=student)
    assert opts["name"] == "张三"
    assert opts["school"] == "信息学院"
    assert opts["email"] == "zhangsan@example.com"
    assert opts["phone"] == "13800000000"
    assert "Python" in opts["skills_body"]


def test_compute_default_options_fills_courses():
    student = _make_student()
    courses = _make_courses()
    overview = {"weighted_average": 86.0, "gpa": 3.5, "arithmetic_average": 85.0}
    opts = compute_default_options(student=student, courses=courses, overview=overview)
    assert "高等数学" in opts["education_body"]
    assert "GPA" in opts["education_body"]
    assert "86.00" in opts["education_body"]


def test_compute_default_options_fills_experiences():
    exps = _make_experiences()
    opts = compute_default_options(experiences=exps)
    assert "某科技公司" in opts["internship"]
    assert "数据分析项目" in opts["project_body"]


def test_compute_default_options_fills_achievements():
    achs = _make_achievements()
    opts = compute_default_options(achievements=achs)
    assert "优秀学生奖学金" in opts["awards"]
    assert "数学建模" in opts["awards"]


def test_compute_default_options_empty_data():
    opts = compute_default_options()
    assert opts["name"] == ""
    assert opts["show_education"] is True
    assert opts["show_custom"] is True


# ── build_resume_html ──────────────────────────────────────────────────

def test_build_resume_html_basic():
    opts = _make_options()
    html = build_resume_html(opts)
    assert "<!DOCTYPE html>" in html
    assert "张三" in html
    assert "数据工程师" in html
    assert "zhangsan@example.com" in html


def test_build_resume_html_section_toggle_off():
    opts = _make_options()
    opts["show_education"] = False
    opts["show_awards"] = False
    html = build_resume_html(opts)
    # education section should still be absent
    # section titles are emitted only if the toggle is on
    assert "GPA" not in html  # education_body has GPA
    assert "优秀学生奖学金" not in html


def test_build_resume_html_custom_section_missing_when_empty():
    opts = _make_options()
    opts["show_custom"] = True
    opts["custom_content"] = ""
    html = build_resume_html(opts)
    # empty sections should not appear
    assert "自我评价" not in html  # section title won't render if body is empty


def test_build_resume_html_intent_section():
    """show_intent=False hides the separate intent section, but header still shows intent."""
    opts = _make_options()
    opts["show_intent"] = False
    html = build_resume_html(opts)
    # intent still in header subtitle (design choice: header always shows identity)
    assert "大数据工程师" in html
    # but the separate "职位方向" section row should not render
    assert "职位方向" not in html


# ── build_resume_markdown ──────────────────────────────────────────────

def test_build_resume_markdown_basic():
    opts = _make_options()
    md = build_resume_markdown(opts)
    assert "# 张三" in md
    assert "数据工程师" in md
    assert "zhangsan@example.com" in md
    assert "## 教育背景" in md


def test_build_resume_markdown_section_toggles():
    opts = _make_options()
    opts["show_projects"] = False
    opts["show_awards"] = False
    md = build_resume_markdown(opts)
    assert "项目经验" not in md
    assert "竞赛获奖" not in md


def test_build_resume_markdown_empty_body_skipped():
    opts = _make_options()
    opts["internship"] = ""
    opts["show_internship"] = True
    md = build_resume_markdown(opts)
    # empty body → section should not appear
    assert "实习经历" not in md


# ── build_resume_json ──────────────────────────────────────────────────

def test_build_resume_json_structure():
    opts = _make_options()
    resume = build_resume_json(opts)
    assert resume["basics"]["name"] == "张三"
    assert resume["basics"]["email"] == "zhangsan@example.com"
    sections = resume["sections"]
    assert isinstance(sections, list)
    # at least education and skills should be present
    section_keys = [s["key"] for s in sections]
    assert "education" in section_keys
    assert "skills" in section_keys


def test_build_resume_json_respects_toggles():
    opts = _make_options()
    opts["show_education"] = False
    resume = build_resume_json(opts)
    section_keys = [s["key"] for s in resume["sections"]]
    assert "education" not in section_keys


# ── run ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback
    tests = [
        fn for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS {test.__name__}")
            passed += 1
        except Exception:
            print(f"  FAIL {test.__name__}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
