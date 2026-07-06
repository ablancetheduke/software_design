"""Tests for graduate planning timeline behavior."""

from datetime import date
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.graduate_application import GraduateApplication
from src.views.graduate_view import reminder_text_for_application


def test_graduate_deadline_reminder_changes_with_current_date():
    app = GraduateApplication(
        school="测试大学",
        college="计算机学院",
        status="了解中",
        deadline="2026-06-26",
    )

    assert reminder_text_for_application(app, date(2026, 6, 25)) == "1 天内截止"
    assert reminder_text_for_application(app, date(2026, 6, 26)) == "0 天内截止"
    assert reminder_text_for_application(app, date(2026, 6, 27)) == "已过截止"
