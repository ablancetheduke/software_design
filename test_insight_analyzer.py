"""Unit tests for the development insight analyzer."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.course import Course
from src.models.experience import Experience
from src.models.achievement import Achievement
from src.models.role import Role
from src.services.insight_analyzer import InsightAnalyzer


def test_insight_analyzer_generates_profile():
    analyzer = InsightAnalyzer()
    insight = analyzer.analyze(
        courses=[
            Course(name="高等数学", credit=4, grade=92, semester="大一上"),
            Course(name="Python程序设计", credit=3, grade=88, semester="大一下"),
        ],
        experiences=[
            Experience(title="课程项目", exp_type="项目", role="组长"),
        ],
        achievements=[
            Achievement(title="程序设计竞赛三等奖", ach_type="奖项"),
        ],
        roles=[
            Role(title="班级学习委员", role_type="班级代表"),
        ],
    )

    assert insight.score > 0
    assert insight.level
    assert "课程积累" in insight.category_scores
    assert insight.suggestions


def test_insight_analyzer_handles_empty_data():
    insight = InsightAnalyzer().analyze([], [], [], [])

    assert insight.level == "起步记录型"
    assert insight.score == 0
    assert insight.highlights
    assert insight.risks
