"""Experience data model (competitions, projects, internships)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Experience:
    """A competition, project, internship, or research experience."""

    exp_id: Optional[int] = None
    title: str = ""
    exp_type: str = "项目"    # 竞赛/项目/实习/科研/其他
    organization: str = ""    # 组织/公司/学校
    start_date: str = ""      # "2024-09"
    end_date: str = ""        # "2025-01"
    description: str = ""
    role: str = ""            # 担任的角色
    outcome: str = ""         # 成果/收获

    def to_row(self) -> tuple:
        return (
            self.title, self.exp_type, self.organization,
            self.start_date, self.end_date, self.description,
            self.role, self.outcome
        )

    @classmethod
    def from_row(cls, row: tuple) -> "Experience":
        return cls(
            exp_id=row[0],
            title=row[1],
            exp_type=row[2],
            organization=row[3],
            start_date=row[4],
            end_date=row[5],
            description=row[6],
            role=row[7],
            outcome=row[8] if len(row) > 8 else "",
        )

    def to_dict(self) -> dict:
        return {
            "type": "experience",
            "exp_id": self.exp_id,
            "title": self.title,
            "exp_type": self.exp_type,
            "organization": self.organization,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
            "role": self.role,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Experience":
        return cls(
            exp_id=d.get("exp_id"),
            title=d.get("title", ""),
            exp_type=d.get("exp_type", "项目"),
            organization=d.get("organization", ""),
            start_date=d.get("start_date", ""),
            end_date=d.get("end_date", ""),
            description=d.get("description", ""),
            role=d.get("role", ""),
            outcome=d.get("outcome", ""),
        )
