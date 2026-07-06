"""Tests for internship application tracking."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database.connection import DatabaseConnection
from src.database.migrations import init_database
from src.database.repositories.internship_application_repo import InternshipApplicationRepository
from src.models.internship_application import InternshipApplication


def test_internship_application_crud_and_summary():
    db_path = os.path.join(tempfile.gettempdir(), "pdptool_test_internship.db")
    DatabaseConnection.reset_instance()
    init_database(db_path)
    repo = InternshipApplicationRepository()

    try:
        app_id = repo.add(InternshipApplication(
            company="测试公司",
            position="数据分析实习生",
            direction="数据分析",
            apply_date="2026-06-01",
            deadline="2026-06-30",
            status="已投递",
            resume_ready=True,
        ))
        app = repo.get_by_id(app_id)
        assert app.company == "测试公司"
        assert app.prep_text == "简历"

        app.status = "一面"
        app.project_ready = True
        repo.update(app)
        assert repo.status_summary()["一面"] == 1
        assert repo.count() == 1

        repo.delete(app_id)
        assert repo.count() == 0
    finally:
        DatabaseConnection.reset_instance()
        if os.path.exists(db_path):
            os.unlink(db_path)
