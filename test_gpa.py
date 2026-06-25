"""Unit tests for GPA calculation strategies."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.course import Course
from src.services.gpa_calculator import (
    GpaCalculator,
    Standard40Strategy,
    WeightedAverageStrategy,
    ArithmeticAverageStrategy,
    calculate_grade_overview,
    calculate_semester_trend,
)


def make_courses():
    return [
        Course(name="数学", code="M001", credit=5.0, grade=92, semester="大一上"),
        Course(name="英语", code="E001", credit=4.0, grade=85, semester="大一上"),
        Course(name="物理", code="P001", credit=4.0, grade=78, semester="大一下"),
        Course(name="体育", code="PE01", credit=1.0, grade=88, semester="大一上"),
    ]


def test_standard_40():
    calc = GpaCalculator(Standard40Strategy())
    result = calc.calculate(make_courses())
    # 92→4.0*5=20, 85→3.7*4=14.8, 78→3.0*4=12, 88→3.7*1=3.7
    # sum=50.5, credits=14, gpa=50.5/14≈3.61
    assert abs(result["gpa"] - 3.61) < 0.01
    assert result["total_credits"] == 14
    assert result["course_count"] == 4


def test_weighted_average():
    calc = GpaCalculator(WeightedAverageStrategy())
    result = calc.calculate(make_courses())
    # 92*5 + 85*4 + 78*4 + 88*1 = 460+340+312+88 = 1200, /14 = 85.71
    assert abs(result["gpa"] - 85.71) < 0.1


def test_arithmetic_average():
    calc = GpaCalculator(ArithmeticAverageStrategy())
    result = calc.calculate(make_courses())
    # (92 + 85 + 78 + 88) / 4 = 85.75
    assert abs(result["gpa"] - 85.75) < 0.01


def test_empty_courses():
    calc = GpaCalculator(Standard40Strategy())
    result = calc.calculate([])
    assert result["gpa"] == 0.0
    assert result["course_count"] == 0


def test_strategy_switch():
    calc = GpaCalculator(Standard40Strategy())
    result1 = calc.calculate(make_courses())

    calc.set_strategy(WeightedAverageStrategy())
    result2 = calc.calculate(make_courses())

    # Results should differ between strategies
    assert result1["gpa"] != result2["gpa"]


def test_available_strategies():
    strategies = GpaCalculator.available_strategies()
    assert len(strategies) >= 3
    names = [s.name() for s in strategies]
    assert "标准4.0绩点制" in names
    assert "加权平均分" in names
    assert "算术平均分" in names
    assert "北大4.0绩点制" not in names


def test_grade_overview_and_trend():
    overview = calculate_grade_overview(make_courses())
    trend = calculate_semester_trend(make_courses())

    assert overview["gpa"] > 0
    assert overview["weighted_average"] > 0
    assert overview["arithmetic_average"] > 0
    assert len(trend) == 2
    assert {item["semester"] for item in trend} == {"大一上", "大一下"}


if __name__ == "__main__":
    test_standard_40()
    test_weighted_average()
    test_empty_courses()
    test_strategy_switch()
    test_available_strategies()
    print("All GPA tests passed!")
