"""Course repository — data access for courses table."""

from typing import List, Optional
from .base_repo import BaseRepository
from ...models.course import Course
from ..connection import DatabaseConnection


class CourseRepository(BaseRepository):
    """CRUD operations for Course records."""

    TABLE = "courses"

    def add(self, course: Course) -> int:
        """Insert a new course. Returns the new ID."""
        cursor = self.db.execute(
            f"INSERT INTO {self.TABLE} (name, code, credit, semester, grade, category, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (course.name, course.code, course.credit, course.semester,
             course.grade, course.category, course.note)
        )
        return cursor.lastrowid

    def update(self, course: Course) -> bool:
        """Update an existing course."""
        self.db.execute(
            f"UPDATE {self.TABLE} SET name=?, code=?, credit=?, semester=?, "
            "grade=?, category=?, note=? WHERE id=?",
            (course.name, course.code, course.credit, course.semester,
             course.grade, course.category, course.note, course.course_id)
        )
        return True

    def delete(self, course_id: int) -> bool:
        """Delete a course by ID."""
        self.db.execute(
            f"DELETE FROM {self.TABLE} WHERE id=?",
            (course_id,)
        )
        return True

    def get_by_id(self, course_id: int) -> Optional[Course]:
        """Get a course by ID."""
        row = self.db.fetch_one(
            f"SELECT * FROM {self.TABLE} WHERE id=?",
            (course_id,)
        )
        return Course.from_row(row) if row else None

    def get_all(self) -> List[Course]:
        """Get all courses."""
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} ORDER BY semester, name"
        )
        return [Course.from_row(r) for r in rows]

    def get_by_semester(self, semester: str) -> List[Course]:
        """Get courses filtered by semester."""
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE semester=? ORDER BY name",
            (semester,)
        )
        return [Course.from_row(r) for r in rows]

    def get_by_category(self, category: str) -> List[Course]:
        """Get courses filtered by category."""
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE category=? ORDER BY semester, name",
            (category,)
        )
        return [Course.from_row(r) for r in rows]

    def search(self, keyword: str) -> List[Course]:
        """Search courses by name or code."""
        pattern = f"%{keyword}%"
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE name LIKE ? OR code LIKE ? "
            "ORDER BY semester, name",
            (pattern, pattern)
        )
        return [Course.from_row(r) for r in rows]

    def import_batch(self, courses: List[Course]) -> int:
        """Batch insert courses. Returns count inserted."""
        data = [c.to_row() for c in courses]
        self.db.execute_many(
            f"INSERT INTO {self.TABLE} (name, code, credit, semester, grade, category, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            data
        )
        return len(data)

    def count(self) -> int:
        """Get total course count."""
        row = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        return row[0] if row else 0

    def get_semesters(self) -> List[str]:
        """Get distinct semesters that have courses."""
        rows = self.db.fetch_all(
            f"SELECT DISTINCT semester FROM {self.TABLE} ORDER BY semester"
        )
        return [r[0] for r in rows if r[0]]
