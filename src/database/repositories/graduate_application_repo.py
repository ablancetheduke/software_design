"""Repository for graduate school applications."""

from typing import Dict, List, Optional

from .base_repo import BaseRepository
from ...models.graduate_application import GraduateApplication


class GraduateApplicationRepository(BaseRepository):
    """CRUD operations for graduate school application records."""

    TABLE = "graduate_applications"

    def add(self, app: GraduateApplication) -> int:
        cursor = self.db.execute(
            f"INSERT INTO {self.TABLE} (school, major, degree_type, "
            "batch, status, apply_date, deadline, advisor, advisor_status, "
            "link, note, ps_ready, recommendation_ready, cv_ready, "
            "transcript_ready, ranking_ready, english_ready, "
            "interview_date, interview_notes, college, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            app.to_row(),
        )
        return cursor.lastrowid

    def update(self, app: GraduateApplication) -> bool:
        self.db.execute(
            f"UPDATE {self.TABLE} SET school=?, major=?, degree_type=?, "
            "batch=?, status=?, apply_date=?, deadline=?, advisor=?, "
            "advisor_status=?, link=?, note=?, ps_ready=?, "
            "recommendation_ready=?, cv_ready=?, transcript_ready=?, "
            "ranking_ready=?, english_ready=?, interview_date=?, "
            "interview_notes=?, college=?, sort_order=? WHERE id=?",
            (*app.to_row(), app.app_id),
        )
        return True

    def delete(self, app_id: int) -> bool:
        self.db.execute(f"DELETE FROM {self.TABLE} WHERE id=?", (app_id,))
        return True

    def get_by_id(self, app_id: int) -> Optional[GraduateApplication]:
        row = self.db.fetch_one(
            f"SELECT * FROM {self.TABLE} WHERE id=?", (app_id,)
        )
        return GraduateApplication.from_row(row) if row else None

    def get_all(self) -> List[GraduateApplication]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} ORDER BY sort_order, deadline, school, college"
        )
        return [GraduateApplication.from_row(row) for row in rows]

    def get_by_school_college(
        self, school: str, college: str
    ) -> Optional[GraduateApplication]:
        """Find record by school + college for import matching."""
        row = self.db.fetch_one(
            f"SELECT * FROM {self.TABLE} WHERE school=? AND college=?",
            (school, college),
        )
        return GraduateApplication.from_row(row) if row else None

    def get_by_status(self, status: str) -> List[GraduateApplication]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE status=? ORDER BY sort_order, deadline, school",
            (status,),
        )
        return [GraduateApplication.from_row(row) for row in rows]

    def get_all_sorted(self) -> List[GraduateApplication]:
        """Get all records sorted for Gantt chart display."""
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} ORDER BY sort_order, deadline, school, college"
        )
        return [GraduateApplication.from_row(row) for row in rows]

    def update_sort_order(self, app_id: int, sort_order: int) -> bool:
        self.db.execute(
            f"UPDATE {self.TABLE} SET sort_order=? WHERE id=?",
            (sort_order, app_id),
        )
        return True

    def count(self) -> int:
        row = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        return row[0] if row else 0

    def status_summary(self) -> Dict[str, int]:
        rows = self.db.fetch_all(
            f"SELECT status, COUNT(*) FROM {self.TABLE} GROUP BY status"
        )
        return {row[0]: row[1] for row in rows}

    def get_schools(self) -> List[str]:
        """Get distinct school names for grouping."""
        rows = self.db.fetch_all(
            f"SELECT DISTINCT school FROM {self.TABLE} ORDER BY school"
        )
        return [row[0] for row in rows]

    def get_by_school(self, school: str) -> List[GraduateApplication]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE school=? ORDER BY sort_order, deadline, college",
            (school,),
        )
        return [GraduateApplication.from_row(row) for row in rows]
