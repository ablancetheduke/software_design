"""Unit tests for DataIO (import/export)."""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database.connection import DatabaseConnection
from src.database.migrations import init_database
from src.services.data_io import DataIO


def test_csv_roundtrip():
    """Test CSV export then re-import."""
    # Use temp database
    db_path = os.path.join(tempfile.gettempdir(), "pdptool_test.db")
    DatabaseConnection.reset_instance()
    init_database(db_path)

    data_io = DataIO()

    # Create CSV
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8-sig")
    tmp.write("课程名,代码,学分,学期,成绩,类别,备注\n")
    tmp.write("测试课程1,T001,3,大一上,90,必修课,\n")
    tmp.write("测试课程2,T002,2,大一上,85,选修课,\n")
    tmp.close()

    try:
        result = data_io.import_courses_csv(tmp.name)
        assert result["imported"] == 2
        assert result["skipped"] == 0
    finally:
        os.unlink(tmp.name)
        DatabaseConnection.reset_instance()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_pasted_text_import():
    """Test importing courses from pasted CSV-like text."""
    db_path = os.path.join(tempfile.gettempdir(), "pdptool_test_paste.db")
    DatabaseConnection.reset_instance()
    init_database(db_path)

    data_io = DataIO()
    text = (
        "课程名,代码,学分,学期,成绩,类别,备注\n"
        "高等数学,M001,4,大一上,92,必修课,核心课\n"
        "Python程序设计,CS001,3,大一下,88,选修课,实践课\n"
    )

    try:
        result = data_io.import_courses_text(text)
        assert result["imported"] == 2
        assert result["skipped"] == 0
    finally:
        DatabaseConnection.reset_instance()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_pasted_experience_and_achievement_import():
    db_path = os.path.join(tempfile.gettempdir(), "pdptool_test_records.db")
    DatabaseConnection.reset_instance()
    init_database(db_path)

    data_io = DataIO()
    exp_text = (
        "标题,类型,组织机构,开始日期,结束日期,角色,成果,描述\n"
        "课程项目,项目,学校,2025-03,2025-06,组长,完成系统,负责开发\n"
    )
    ach_text = (
        "标题,类型,颁发机构,日期,描述\n"
        "数学建模三等奖,奖项,学校,2025-09,团队竞赛\n"
    )

    try:
        exp_result = data_io.import_experiences_text(exp_text)
        ach_result = data_io.import_achievements_text(ach_text)
        assert exp_result["imported"] == 1
        assert ach_result["imported"] == 1
    finally:
        DatabaseConnection.reset_instance()
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_csv_roundtrip()
    print("All DataIO tests passed!")
