"""Achievement repository — data access for achievements table."""

from typing import List, Optional
from .base_repo import BaseRepository
from ...models.achievement import Achievement


class AchievementRepository(BaseRepository):
    """CRUD operations for Achievement records."""

    TABLE = "achievements"

    def add(self, ach: Achievement) -> int:
        cursor = self.db.execute(
            f"INSERT INTO {self.TABLE} (title, ach_type, issuer, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            ach.to_row()
        )
        return cursor.lastrowid

    def update(self, ach: Achievement) -> bool:
        self.db.execute(
            f"UPDATE {self.TABLE} SET title=?, ach_type=?, issuer=?, "
            "date=?, description=? WHERE id=?",
            (*ach.to_row(), ach.ach_id)
        )
        return True

    def delete(self, ach_id: int) -> bool:
        self.db.execute(f"DELETE FROM {self.TABLE} WHERE id=?", (ach_id,))
        return True

    def get_by_id(self, ach_id: int) -> Optional[Achievement]:
        row = self.db.fetch_one(f"SELECT * FROM {self.TABLE} WHERE id=?", (ach_id,))
        return Achievement.from_row(row) if row else None

    def get_all(self) -> List[Achievement]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} ORDER BY date DESC"
        )
        return [Achievement.from_row(r) for r in rows]

    def get_by_type(self, ach_type: str) -> List[Achievement]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE ach_type=? ORDER BY date DESC",
            (ach_type,)
        )
        return [Achievement.from_row(r) for r in rows]

    def import_batch(self, achievements: List[Achievement]) -> int:
        data = [a.to_row() for a in achievements]
        self.db.execute_many(
            f"INSERT INTO {self.TABLE} (title, ach_type, issuer, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            data
        )
        return len(data)

    def count(self) -> int:
        row = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        return row[0] if row else 0
