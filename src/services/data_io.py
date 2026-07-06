"""Data import/export service.

Handles CSV and JSON import/export for courses and other records.
"""

import csv
import json
import os
import re
from typing import List, Dict, Any
from ..models.course import Course
from ..models.experience import Experience
from ..models.achievement import Achievement
from ..models.role import Role
from ..database.repositories.course_repo import CourseRepository
from ..database.repositories.experience_repo import ExperienceRepository
from ..database.repositories.achievement_repo import AchievementRepository
from ..database.repositories.role_repo import RoleRepository


class DataIO:
    """Data import/export operations across all record types."""

    def __init__(self):
        self.course_repo = CourseRepository()
        self.exp_repo = ExperienceRepository()
        self.ach_repo = AchievementRepository()
        self.role_repo = RoleRepository()

    # ── CSV Import ──────────────────────────────────────────────────

    def import_courses_csv(self, filepath: str) -> Dict[str, int]:
        """Import courses from a CSV file.

        Expected columns: 课程名, 教师, 学分, 成绩, 学期, 类别
        (Matches sample_courses.csv format, with extras ignored)
        """
        courses = []
        skipped = 0

        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)

            # Detect column mapping
            if not header:
                return {"imported": 0, "skipped": 0}

            # Map columns by name
            col_map = {}
            for i, col_name in enumerate(header):
                col_name = col_name.strip()
                if "课程名" in col_name or "name" in col_name.lower():
                    col_map["name"] = i
                elif "学分" in col_name or "credit" in col_name.lower():
                    col_map["credit"] = i
                elif "成绩" in col_name or "grade" in col_name.lower() or "分数" in col_name:
                    col_map["grade"] = i
                elif "学期" in col_name or "semester" in col_name.lower():
                    col_map["semester"] = i
                elif "类别" in col_name or "category" in col_name.lower() or "模块" in col_name:
                    col_map["category"] = i
                elif "代码" in col_name or "code" in col_name.lower():
                    col_map["code"] = i

            for row in reader:
                if not row or all(c.strip() == "" for c in row):
                    continue
                try:
                    name = row[col_map.get("name", 0)] if "name" in col_map else ""
                    credit = float(row[col_map.get("credit", 2)]) if "credit" in col_map else 0.0
                    grade = float(row[col_map.get("grade", 3)]) if "grade" in col_map else 0.0
                    semester = row[col_map.get("semester", 4)] if "semester" in col_map else ""
                    category = row[col_map.get("category", 5)] if "category" in col_map else "必修课"
                    code = row[col_map.get("code", 1)] if "code" in col_map else ""

                    courses.append(Course(
                        name=name.strip(),
                        code=code.strip(),
                        credit=credit,
                        grade=grade,
                        semester=semester.strip(),
                        category=category.strip(),
                    ))
                except (ValueError, IndexError):
                    skipped += 1

        imported = self.course_repo.import_batch(courses)
        return {"imported": imported, "skipped": skipped}

    def import_courses_text(self, text: str) -> Dict[str, int]:
        """Import courses from pasted table text.

        Supported formats:
        - CSV/TSV copied from Excel/WPS
        - Whitespace separated rows: 课程名 代码 学分 学期 成绩 类别 备注

        Returns counts for imported and skipped rows.
        """
        courses = []
        skipped = 0

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if any(keyword in line for keyword in ("课程名", "课程名称", "学分", "成绩")):
                continue

            row = self._split_pasted_course_line(line)
            if len(row) < 5:
                skipped += 1
                continue

            try:
                name = row[0].strip()
                code = row[1].strip() if len(row) > 1 else ""
                credit = float(row[2]) if len(row) > 2 and row[2] else 0.0
                semester = row[3].strip() if len(row) > 3 else ""
                grade = float(row[4]) if len(row) > 4 and row[4] else 0.0
                category = row[5].strip() if len(row) > 5 and row[5] else "必修课"
                note = row[6].strip() if len(row) > 6 else ""
                if not name:
                    skipped += 1
                    continue
                courses.append(Course(
                    name=name,
                    code=code,
                    credit=credit,
                    semester=semester,
                    grade=grade,
                    category=category,
                    note=note,
                ))
            except (ValueError, IndexError):
                skipped += 1

        imported = self.course_repo.import_batch(courses) if courses else 0
        return {"imported": imported, "skipped": skipped}

    @staticmethod
    def _split_pasted_course_line(line: str) -> List[str]:
        """Split one pasted row using common spreadsheet delimiters."""
        if "\t" in line:
            return [part.strip() for part in line.split("\t")]
        if "," in line or "，" in line:
            normalized = line.replace("，", ",")
            return [part.strip() for part in next(csv.reader([normalized]))]
        return [part.strip() for part in re.split(r"\s+", line) if part.strip()]

    def import_experiences_text(self, text: str, force_exp_type: str = "") -> Dict[str, int]:
        """Import experiences from pasted table text.

        Columns: 标题, 类型, 组织机构, 开始日期, 结束日期, 角色, 成果, 描述
        If force_exp_type is set, ALL imported rows will use that type regardless of CSV.
        """
        experiences = []
        skipped = 0
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if any(keyword in line for keyword in ("标题", "类型", "组织机构", "开始日期")):
                continue
            row = self._split_pasted_course_line(line)
            if len(row) < 2:
                skipped += 1
                continue
            title = row[0].strip()
            if not title:
                skipped += 1
                continue
            exp_type = force_exp_type if force_exp_type else (row[1].strip() if len(row) > 1 else "项目")
            experiences.append(Experience(
                title=title,
                exp_type=exp_type,
                organization=row[2].strip() if len(row) > 2 else "",
                start_date=row[3].strip() if len(row) > 3 else "",
                end_date=row[4].strip() if len(row) > 4 else "",
                role=row[5].strip() if len(row) > 5 else "",
                outcome=row[6].strip() if len(row) > 6 else "",
                description=row[7].strip() if len(row) > 7 else "",
            ))

        imported = self.exp_repo.import_batch(experiences) if experiences else 0
        return {"imported": imported, "skipped": skipped}

    def import_experiences_csv(self, filepath: str, force_exp_type: str = "") -> Dict[str, int]:
        """Import experiences from a CSV file. Same format as import_experiences_text."""
        with open(filepath, "r", encoding="utf-8-sig") as f:
            text = f.read()
        return self.import_experiences_text(text, force_exp_type=force_exp_type)

    def import_achievements_text(self, text: str) -> Dict[str, int]:
        """Import achievements from pasted table text.

        Columns: 标题, 类型, 颁发机构, 日期, 描述
        """
        achievements = []
        skipped = 0
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if any(keyword in line for keyword in ("标题", "类型", "颁发机构", "日期")):
                continue
            row = self._split_pasted_course_line(line)
            if len(row) < 2:
                skipped += 1
                continue
            title = row[0].strip()
            if not title:
                skipped += 1
                continue
            achievements.append(Achievement(
                title=title,
                ach_type=row[1].strip() if len(row) > 1 else "奖项",
                issuer=row[2].strip() if len(row) > 2 else "",
                date=row[3].strip() if len(row) > 3 else "",
                description=row[4].strip() if len(row) > 4 else "",
            ))

        imported = self.ach_repo.import_batch(achievements) if achievements else 0
        return {"imported": imported, "skipped": skipped}

    def import_achievements_csv(self, filepath: str) -> Dict[str, int]:
        """Import achievements from a CSV file."""
        with open(filepath, "r", encoding="utf-8-sig") as f:
            text = f.read()
        return self.import_achievements_text(text)

    # ── JSON Export ─────────────────────────────────────────────────

    def export_all_json(self, filepath: str) -> int:
        """Export all data to a JSON file (full backup). Returns record count."""
        data = {
            "courses": [c.to_dict() for c in self.course_repo.get_all()],
            "experiences": [e.to_dict() for e in self.exp_repo.get_all()],
            "achievements": [a.to_dict() for a in self.ach_repo.get_all()],
            "roles": [r.to_dict() for r in self.role_repo.get_all()],
        }
        total = sum(len(v) for v in data.values())
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return total

    def import_all_json(self, filepath: str) -> Dict[str, int]:
        """Import data from a JSON backup file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        counts = {}
        for record_type, records in data.items():
            if record_type == "courses":
                courses = [Course.from_dict(r) for r in records]
                counts["courses"] = self.course_repo.import_batch(courses)
            elif record_type == "experiences":
                exps = [Experience.from_dict(r) for r in records]
                counts["experiences"] = self.exp_repo.import_batch(exps)
            elif record_type == "achievements":
                achs = [Achievement.from_dict(r) for r in records]
                counts["achievements"] = self.ach_repo.import_batch(achs)
            elif record_type == "roles":
                roles = [Role.from_dict(r) for r in records]
                counts["roles"] = self.role_repo.import_batch(roles)
        return counts

    # ── CSV Export ──────────────────────────────────────────────────

    def export_courses_csv(self, filepath: str) -> int:
        """Export courses to CSV. Returns row count."""
        courses = self.course_repo.get_all()
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["课程名", "代码", "学分", "学期", "成绩", "类别", "备注"])
            for c in courses:
                writer.writerow([c.name, c.code, c.credit, c.semester, c.grade, c.category, c.note])
        return len(courses)
