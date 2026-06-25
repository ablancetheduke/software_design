"""Course data model."""

from dataclasses import dataclass
from typing import Optional

PF_MARKER = "[P/F]"


@dataclass
class Course:
    """A course record in the student's academic history."""

    course_id: Optional[int] = None
    name: str = ""
    code: str = ""           # e.g. "MAT108"
    credit: float = 0.0
    semester: str = ""       # e.g. "大一上"
    grade: float = 0.0       # 百分制分数
    category: str = "必修课"  # 必修课/选修课/通识课
    note: str = ""

    @property
    def is_pass_fail(self) -> bool:
        """True if this is a pass/fail course (grade stored as 60 + [P/F] marker)."""
        return self.grade == 60 and PF_MARKER in (self.note or "")

    @property
    def is_in_progress(self) -> bool:
        """True if this course is still in progress (grade < 0)."""
        return self.grade < 0

    def to_grade_point(self, scale: str = "4.0") -> float:
        """Convert percentage grade to grade point (standard 4.0 scale)."""
        if self.grade >= 90:
            return 4.0
        elif self.grade >= 85:
            return 3.7
        elif self.grade >= 82:
            return 3.3
        elif self.grade >= 78:
            return 3.0
        elif self.grade >= 75:
            return 2.7
        elif self.grade >= 72:
            return 2.3
        elif self.grade >= 68:
            return 2.0
        elif self.grade >= 64:
            return 1.5
        elif self.grade >= 60:
            return 1.0
        else:
            return 0.0

    def to_row(self) -> tuple:
        """Convert to database row tuple."""
        return (
            self.name, self.code, self.credit,
            self.semester, self.grade, self.category, self.note
        )

    @classmethod
    def from_row(cls, row: tuple) -> "Course":
        """Create Course from database row."""
        return cls(
            course_id=row[0],
            name=row[1],
            code=row[2],
            credit=row[3],
            semester=row[4],
            grade=row[5],
            category=row[6],
            note=row[7] if len(row) > 7 else "",
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "type": "course",
            "course_id": self.course_id,
            "name": self.name,
            "code": self.code,
            "credit": self.credit,
            "semester": self.semester,
            "grade": self.grade,
            "category": self.category,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Course":
        """Create Course from dictionary (JSON import)."""
        return cls(
            course_id=d.get("course_id"),
            name=d.get("name", ""),
            code=d.get("code", ""),
            credit=d.get("credit", 0.0),
            semester=d.get("semester", ""),
            grade=d.get("grade", 0.0),
            category=d.get("category", "必修课"),
            note=d.get("note", ""),
        )
