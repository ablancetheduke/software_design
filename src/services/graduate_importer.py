"""Import graduate applications from Excel spreadsheet."""

import re
from datetime import datetime
from typing import Dict

import pandas as pd

from ..database.repositories.graduate_application_repo import (
    GraduateApplicationRepository,
)
from ..models.graduate_application import GraduateApplication

# ── Excel column mapping (try multiple possible names) ──
COLUMN_ALIASES = {
    "school": ["学校", "院校", "大学", "school", "university"],
    "college": ["学院/项目", "学院", "院系", "项目", "college", "department"],
    "deadline": ["截止日期（推算）", "截止日期", "截止时间(推算)", "deadline", "截止"],
    "deadline_time": ["截止时间", "时间"],
    "status": ["状态", "status", "进度"],
    "note": ["备注", "note", "说明", "注释"],
    "raw_countdown": ["原始倒计时/信息", "倒计时"],
}

DEADLINE_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _find_column(df_columns: list[str], aliases: list[str]) -> str | None:
    """Find the first matching column name from aliases."""
    for alias in aliases:
        for col in df_columns:
            if alias.lower() in col.lower():
                return col
    return None


def _parse_date(val) -> str:
    """Extract YYYY-MM-DD from various formats."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    m = DEADLINE_DATE_RE.search(s)
    return m.group(1) if m else ""


def _map_status(raw: str) -> str:
    """Map Excel status to app status."""
    if not raw or pd.isna(raw):
        return "了解中"
    s = str(raw).strip()
    if "截止" in s and "未" not in s and "已" in s:
        return "已投递"
    if "未截止" in s or "未" in s:
        return "了解中"
    if "暂无" in s or "不明确" in s:
        return "了解中"
    return s


def import_from_excel(filepath: str) -> dict:
    """Import graduate applications from Excel.

    Returns:
        {added: int, updated: int, skipped: int, errors: list[str]}
    """
    repo = GraduateApplicationRepository()
    result = {"added": 0, "updated": 0, "skipped": 0, "errors": []}

    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        result["errors"].append(f"读取 Excel 失败: {e}")
        return result

    if df.empty:
        result["errors"].append("Excel 文件为空")
        return result

    cols = [str(c) for c in df.columns]

    school_col = _find_column(cols, COLUMN_ALIASES["school"])
    college_col = _find_column(cols, COLUMN_ALIASES["college"])
    deadline_col = _find_column(cols, COLUMN_ALIASES["deadline"])
    status_col = _find_column(cols, COLUMN_ALIASES["status"])
    note_col = _find_column(cols, COLUMN_ALIASES["note"])

    if not school_col:
        result["errors"].append(
            f"未找到学校列，可用列: {', '.join(cols)}"
        )
        return result

    for idx, row in df.iterrows():
        try:
            school = str(row[school_col]).strip() if pd.notna(row[school_col]) else ""
            if not school:
                result["skipped"] += 1
                continue

            college = ""
            if college_col:
                college = str(row[college_col]).strip() if pd.notna(row[college_col]) else ""

            deadline = ""
            if deadline_col:
                deadline = _parse_date(row[deadline_col])

            status = "了解中"
            if status_col:
                status = _map_status(row[status_col])

            note = ""
            if note_col:
                note = str(row[note_col]).strip() if pd.notna(row[note_col]) else ""

            # Check if already exists (match by school + college)
            existing = repo.get_by_school_college(school, college)

            if existing:
                # Update: only overwrite deadline & status, preserve manual edits
                existing.deadline = deadline or existing.deadline
                existing.status = status
                existing.note = note or existing.note
                repo.update(existing)
                result["updated"] += 1
            else:
                app = GraduateApplication(
                    school=school,
                    college=college,
                    major="",
                    degree_type="硕士",
                    batch="夏令营",
                    status=status,
                    deadline=deadline,
                    note=note,
                    sort_order=idx,  # preserve Excel row order
                )
                repo.add(app)
                result["added"] += 1

        except Exception as e:
            result["errors"].append(f"第 {idx + 2} 行处理失败: {e}")

    return result
