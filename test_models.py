"""Unit tests for data models."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.course import Course, PF_MARKER
from src.models.experience import Experience
from src.models.achievement import Achievement
from src.models.role import Role
from src.models.student import Student


def test_course_creation():
    c = Course(name="高等数学", code="MAT108", credit=4.0, grade=92, semester="大一上")
    assert c.name == "高等数学"
    assert c.credit == 4.0
    assert c.to_grade_point() == 4.0


def test_course_to_dict():
    c = Course(course_id=1, name="线性代数", code="CMP104", credit=3.0, grade=88, semester="大一下")
    d = c.to_dict()
    assert d["type"] == "course"
    assert d["name"] == "线性代数"
    c2 = Course.from_dict(d)
    assert c2.name == c.name
    assert c2.grade == c.grade


def test_experience_to_dict():
    e = Experience(title="数学建模国赛", exp_type="竞赛", organization="CUMCM")
    d = e.to_dict()
    assert d["type"] == "experience"
    e2 = Experience.from_dict(d)
    assert e2.title == e.title


def test_achievement_to_dict():
    a = Achievement(title="国家奖学金", ach_type="奖学金")
    d = a.to_dict()
    assert d["type"] == "achievement"
    a2 = Achievement.from_dict(d)
    assert a2.title == a.title


def test_role_to_dict():
    r = Role(title="班级学习委员", role_type="班级代表")
    d = r.to_dict()
    assert d["type"] == "role"
    r2 = Role.from_dict(d)
    assert r2.title == r.title


def test_student_to_dict():
    s = Student(name="张三", student_no="20230001", college="信息学院", major="数据科学")
    d = s.to_dict()
    assert d["type"] == "student"
    s2 = Student.from_dict(d)
    assert s2.name == s.name


def test_pass_fail_course():
    c = Course(name="体育", credit=1.0, grade=60, note=f"{PF_MARKER} 体测通过")
    assert c.is_pass_fail is True
    assert c.is_in_progress is False


def test_real_60_not_pass_fail():
    c = Course(name="某课", credit=3.0, grade=60)
    assert c.is_pass_fail is False


def test_in_progress_course():
    c = Course(name="毕业论文", credit=6.0, grade=-1)
    assert c.is_in_progress is True
    assert c.is_pass_fail is False


def test_grade_to_point():
    c = Course(name="Test", credit=3.0)
    c.grade = 95
    assert c.to_grade_point() == 4.0
    c.grade = 83
    assert c.to_grade_point() == 3.3
    c.grade = 73
    assert c.to_grade_point() == 2.3
    c.grade = 55
    assert c.to_grade_point() == 0.0


if __name__ == "__main__":
    test_course_creation()
    test_course_to_dict()
    test_experience_to_dict()
    test_achievement_to_dict()
    test_role_to_dict()
    test_student_to_dict()
    test_pass_fail_course()
    test_real_60_not_pass_fail()
    test_in_progress_course()
    test_grade_to_point()
    print("All model tests passed!")
