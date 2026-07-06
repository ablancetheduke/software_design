"""Student repository — single student profile (one-record table)."""

from typing import Optional
from .base_repo import BaseRepository
from ...models.student import Student


class StudentRepository(BaseRepository):
    """CRUD for Student profile (single-record pattern)."""

    TABLE = "student"

    def get(self) -> Optional[Student]:
        """Get the student profile (first row)."""
        row = self.db.fetch_one(f"SELECT * FROM {self.TABLE} LIMIT 1")
        return Student.from_row(row) if row else None

    def save(self, student: Student) -> bool:
        """Save (insert or update) the student profile."""
        existing = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        if existing and existing[0] > 0:
            row = self.db.fetch_one(f"SELECT id FROM {self.TABLE} LIMIT 1")
            student.student_id = row[0]
            self.db.execute(
                f"UPDATE {self.TABLE} SET name=?, student_no=?, college=?, major=?, "
                "enrollment_year=?, email=?, phone=?, github=?, linkedin=?, "
                "skills=?, summary=? WHERE id=?",
                (*student.to_row(), student.student_id)
            )
        else:
            self.db.execute(
                f"INSERT INTO {self.TABLE} (name, student_no, college, major, "
                "enrollment_year, email, phone, github, linkedin, skills, summary) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                student.to_row()
            )
        return True
