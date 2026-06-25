"""Internship application tracking model."""

from dataclasses import dataclass
from typing import Optional


STATUS_ALIASES = {
    "寰呮姇閫?": "待投递",
    "宸叉姇閫?": "已投递",
    "绗旇瘯": "笔试",
    "涓€闈?": "一面",
    "浜岄潰": "二面",
    "鎷掔粷": "拒绝",
    "鏀惧純": "放弃",
}


@dataclass
class InternshipApplication:
    """A single internship/job application record."""

    app_id: Optional[int] = None
    company: str = ""
    position: str = ""
    direction: str = ""
    apply_date: str = ""
    deadline: str = ""
    status: str = "待投递"
    link: str = ""
    note: str = ""
    resume_ready: bool = False
    project_ready: bool = False
    reviewed: bool = False
    interview_date: str = ""        # v4 — when the interview happened
    interview_notes: str = ""       # v4 — what questions were asked

    def to_row(self) -> tuple:
        return (
            self.company, self.position, self.direction,
            self.apply_date, self.deadline, self.status,
            self.link, self.note,
            int(self.resume_ready), int(self.project_ready),
            int(self.reviewed),
            self.interview_date, self.interview_notes,
        )

    @classmethod
    def from_row(cls, row) -> "InternshipApplication":
        return cls(
            app_id=row[0],
            company=row[1], position=row[2], direction=row[3],
            apply_date=row[4], deadline=row[5],
            status=STATUS_ALIASES.get(row[6], row[6]),
            link=row[7], note=row[8],
            resume_ready=bool(row[9]) if len(row) > 9 else False,
            project_ready=bool(row[10]) if len(row) > 10 else False,
            reviewed=bool(row[11]) if len(row) > 11 else False,
            interview_date=row[12] if len(row) > 12 else "",
            interview_notes=row[13] if len(row) > 13 else "",
        )

    @property
    def has_interview_notes(self) -> bool:
        return bool((self.interview_notes or "").strip())

    @property
    def prep_count(self) -> int:
        items = [self.resume_ready, self.project_ready,
                 self.reviewed, self.has_interview_notes]
        return sum(1 for x in items if x)

    @property
    def prep_text(self) -> str:
        items = []
        if self.resume_ready:   items.append("简历")
        if self.project_ready:  items.append("项目")
        if self.reviewed:       items.append("复盘")
        if self.has_interview_notes: items.append("面经")
        return "、".join(items) if items else "未完成"
