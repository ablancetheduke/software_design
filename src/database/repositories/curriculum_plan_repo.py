"""Repository for structured curriculum plan chunks."""

from typing import List, Optional

from .base_repo import BaseRepository


class CurriculumPlanRepository(BaseRepository):
    """Store and retrieve curriculum plan chunks for AI context."""

    TABLE = "curriculum_plan_chunks"

    def replace_chunks(self, chunks: List[dict]) -> int:
        if not chunks:
            return 0

        sources = sorted({chunk.get("source_file", "") for chunk in chunks})
        for source in sources:
            self.db.execute(f"DELETE FROM {self.TABLE} WHERE source_file=?", (source,))

        rows = [
            (
                chunk.get("major", ""),
                chunk.get("cohort_year", ""),
                chunk.get("module", ""),
                chunk.get("section_title", ""),
                float(chunk.get("required_credits", 0) or 0),
                ",".join(chunk.get("course_codes", [])),
                chunk.get("content", ""),
                chunk.get("source_file", ""),
                int(chunk.get("chunk_order", 0) or 0),
            )
            for chunk in chunks
        ]
        self.db.execute_many(
            f"""
            INSERT OR REPLACE INTO {self.TABLE}
            (major, cohort_year, module, section_title, required_credits,
             course_codes, content, source_file, chunk_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        return len(rows)

    def get_chunks(
        self,
        major: str = "",
        cohort_year: str = "",
        limit: Optional[int] = None,
    ) -> List[dict]:
        sql = f"SELECT * FROM {self.TABLE}"
        params = []
        filters = []
        if major:
            filters.append("major LIKE ?")
            params.append(f"%{major}%")
        if cohort_year:
            filters.append("(cohort_year=? OR cohort_year='')")
            params.append(cohort_year)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY major, cohort_year, chunk_order, id"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        rows = self.db.fetch_all(sql, tuple(params))
        return [self._row_to_dict(row) for row in rows]

    def get_all_chunks(self, limit: Optional[int] = None) -> List[dict]:
        return self.get_chunks(limit=limit)

    def count(self) -> int:
        row = self.db.fetch_one(f"SELECT COUNT(*) FROM {self.TABLE}")
        return row[0] if row else 0

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": row["id"],
            "major": row["major"],
            "cohort_year": row["cohort_year"],
            "module": row["module"],
            "section_title": row["section_title"],
            "required_credits": row["required_credits"],
            "course_codes": row["course_codes"].split(",") if row["course_codes"] else [],
            "content": row["content"],
            "source_file": row["source_file"],
            "chunk_order": row["chunk_order"],
        }
