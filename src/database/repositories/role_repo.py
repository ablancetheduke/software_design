"""Role repository — data access for roles table."""

from typing import List, Optional
from .base_repo import BaseRepository
from ...models.role import Role


class RoleRepository(BaseRepository):
    """CRUD operations for Role records."""

    TABLE = "roles"

    def add(self, role: Role) -> int:
        cursor = self.db.execute(
            f"INSERT INTO {self.TABLE} (title, role_type, organization, "
            "start_date, end_date, description) VALUES (?, ?, ?, ?, ?, ?)",
            role.to_row()
        )
        return cursor.lastrowid

    def update(self, role: Role) -> bool:
        self.db.execute(
            f"UPDATE {self.TABLE} SET title=?, role_type=?, organization=?, "
            "start_date=?, end_date=?, description=? WHERE id=?",
            (*role.to_row(), role.role_id)
        )
        return True

    def delete(self, role_id: int) -> bool:
        self.db.execute(f"DELETE FROM {self.TABLE} WHERE id=?", (role_id,))
        return True

    def get_by_id(self, role_id: int) -> Optional[Role]:
        row = self.db.fetch_one(f"SELECT * FROM {self.TABLE} WHERE id=?", (role_id,))
        return Role.from_row(row) if row else None

    def get_all(self) -> List[Role]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} ORDER BY start_date DESC"
        )
        return [Role.from_row(r) for r in rows]

    def get_by_type(self, role_type: str) -> List[Role]:
        rows = self.db.fetch_all(
            f"SELECT * FROM {self.TABLE} WHERE role_type=? ORDER BY start_date DESC",
            (role_type,)
        )
        return [Role.from_row(r) for r in rows]

    def import_batch(self, roles: List[Role]) -> int:
        data = [r.to_row() for r in roles]
        self.db.execute_many(
            f"INSERT INTO {self.TABLE} (title, role_type, organization, "
            "start_date, end_date, description) VALUES (?, ?, ?, ?, ?, ?)",
            data
        )
        return len(data)

    def count(self) -> int:
        row = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        return row[0] if row else 0
