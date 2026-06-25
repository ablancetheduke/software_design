"""Achievement data model (awards, scholarships, honors)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Achievement:
    """An achievement or award record."""

    ach_id: Optional[int] = None
    title: str = ""
    ach_type: str = "奖项"     # 奖学金/奖项/荣誉/证书/其他
    issuer: str = ""           # 颁发机构
    date: str = ""             # "2025-06"
    description: str = ""

    def to_row(self) -> tuple:
        return (
            self.title, self.ach_type, self.issuer,
            self.date, self.description
        )

    @classmethod
    def from_row(cls, row: tuple) -> "Achievement":
        return cls(
            ach_id=row[0],
            title=row[1],
            ach_type=row[2],
            issuer=row[3],
            date=row[4],
            description=row[5] if len(row) > 5 else "",
        )

    def to_dict(self) -> dict:
        return {
            "type": "achievement",
            "ach_id": self.ach_id,
            "title": self.title,
            "ach_type": self.ach_type,
            "issuer": self.issuer,
            "date": self.date,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Achievement":
        return cls(
            ach_id=d.get("ach_id"),
            title=d.get("title", ""),
            ach_type=d.get("ach_type", "奖项"),
            issuer=d.get("issuer", ""),
            date=d.get("date", ""),
            description=d.get("description", ""),
        )
