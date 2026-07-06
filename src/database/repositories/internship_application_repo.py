"""Repository for internship applications."""

from typing import List, Optional, Dict

from .base_repo import BaseRepository
from ...models.internship_application import InternshipApplication


class InternshipApplicationRepository(BaseRepository):
    """CRUD operations for internship application records."""

    TABLE = "internship_applications"

    def add(self, app: InternshipApplication) -> int:
        cursor = self.db.execute(
            f"INSERT INTO {self.TABLE} (company, position, direction, apply_date, "
            "deadline, status, link, note, resume_ready, project_ready, reviewed, "
            "interview_date, interview_notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            app.to_row(),
        )
        return cursor.lastrowid

    def update(self, app: InternshipApplication) -> bool:
        self.db.execute(
            f"UPDATE {self.TABLE} SET company=?, position=?, direction=?, "
            "apply_date=?, deadline=?, status=?, link=?, note=?, resume_ready=?, "
            "project_ready=?, reviewed=?, interview_date=?, interview_notes=? "
            "WHERE id=?",
            (*app.to_row(), app.app_id),
        )
        return True

    def delete(self, app_id: int) -> bool:
        self.db.execute(f"DELETE FROM {self.TABLE} WHERE id=?", (app_id,))
        return True

    def get_by_id(self, app_id: int) -> Optional[InternshipApplication]:
        row = self.db.fetch_one(f"SELECT * FROM {self.TABLE} WHERE id=?", (app_id,))
        return InternshipApplication.from_row(row) if row else None

    def get_all(self) -> List[InternshipApplication]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} ORDER BY deadline, apply_date DESC, company"
        )
        return [InternshipApplication.from_row(row) for row in rows]

    def get_by_status(self, status: str) -> List[InternshipApplication]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE status=? ORDER BY deadline, company",
            (status,),
        )
        return [InternshipApplication.from_row(row) for row in rows]

    def count(self) -> int:
        row = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        return row[0] if row else 0

    def status_summary(self) -> Dict[str, int]:
        rows = self.db.fetch_all(
            f"SELECT status, COUNT(*) FROM {self.TABLE} GROUP BY status"
        )
        return {row[0]: row[1] for row in rows}
