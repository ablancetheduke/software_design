"""Role data model (class rep, volunteer, etc.)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Role:
    """A role or position held by the student."""

    role_id: Optional[int] = None
    title: str = ""
    role_type: str = "志愿者"   # 班级代表/模块代表/志愿者/社团干部/学生会/其他
    organization: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""

    def to_row(self) -> tuple:
        return (
            self.title, self.role_type, self.organization,
            self.start_date, self.end_date, self.description
        )

    @classmethod
    def from_row(cls, row: tuple) -> "Role":
        return cls(
            role_id=row[0],
            title=row[1],
            role_type=row[2],
            organization=row[3],
            start_date=row[4],
            end_date=row[5],
            description=row[6] if len(row) > 6 else "",
        )

    def to_dict(self) -> dict:
        return {
            "type": "role",
            "role_id": self.role_id,
            "title": self.title,
            "role_type": self.role_type,
            "organization": self.organization,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Role":
        return cls(
            role_id=d.get("role_id"),
            title=d.get("title", ""),
            role_type=d.get("role_type", "志愿者"),
            organization=d.get("organization", ""),
            start_date=d.get("start_date", ""),
            end_date=d.get("end_date", ""),
            description=d.get("description", ""),
        )
