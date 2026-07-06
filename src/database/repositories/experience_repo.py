"""Experience repository — data access for experiences table."""

from typing import List, Optional
from .base_repo import BaseRepository
from ...models.experience import Experience


class ExperienceRepository(BaseRepository):
    """CRUD operations for Experience records."""

    TABLE = "experiences"

    def add(self, exp: Experience) -> int:
        cursor = self.db.execute(
            f"INSERT INTO {self.TABLE} (title, exp_type, organization, "
            "start_date, end_date, description, role, outcome) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            exp.to_row()
        )
        return cursor.lastrowid

    def update(self, exp: Experience) -> bool:
        self.db.execute(
            f"UPDATE {self.TABLE} SET title=?, exp_type=?, organization=?, "
            "start_date=?, end_date=?, description=?, role=?, outcome=? WHERE id=?",
            (*exp.to_row(), exp.exp_id)
        )
        return True

    def delete(self, exp_id: int) -> bool:
        self.db.execute(f"DELETE FROM {self.TABLE} WHERE id=?", (exp_id,))
        return True

    def get_by_id(self, exp_id: int) -> Optional[Experience]:
        row = self.db.fetch_one(f"SELECT * FROM {self.TABLE} WHERE id=?", (exp_id,))
        return Experience.from_row(row) if row else None

    def get_all(self) -> List[Experience]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} ORDER BY start_date DESC"
        )
        return [Experience.from_row(r) for r in rows]

    def get_by_type(self, exp_type: str) -> List[Experience]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE exp_type=? ORDER BY start_date DESC",
            (exp_type,)
        )
        return [Experience.from_row(r) for r in rows]

    def import_batch(self, experiences: List[Experience]) -> int:
        data = [e.to_row() for e in experiences]
        self.db.execute_many(
            f"INSERT INTO {self.TABLE} (title, exp_type, organization, "
            "start_date, end_date, description, role, outcome) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            data
        )
        return len(data)

    def count(self) -> int:
        row = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        return row[0] if row else 0
