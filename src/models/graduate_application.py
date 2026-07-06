"""Graduate school application tracking model."""

from dataclasses import dataclass
from typing import Optional


STATUS_ALIASES: dict[str, str] = {}

GRADUATE_STATUSES = [
    "了解中", "已联系导师", "材料准备中", "已投递",
    "入营通知", "复试/面试", "拟录取", "拒绝", "放弃",
]

DEGREE_TYPES = ["学硕", "专硕", "直博", "硕士", "博士"]

APPLICATION_BATCHES = [
    "夏令营", "预推免", "九月推免", "统考", "申请考核", "出国申请",
]

ADVISOR_STATUSES = ["未联系", "已发邮件", "已回复", "已面谈", "已确认"]


@dataclass
class GraduateApplication:
    """A single graduate-school application record."""

    app_id: Optional[int] = None
    school: str = ""
    college: str = ""                     # 学院/系所/项目名
    major: str = ""
    degree_type: str = "硕士"
    batch: str = "夏令营"
    status: str = "了解中"
    apply_date: str = ""
    deadline: str = ""
    advisor: str = ""
    advisor_status: str = "未联系"
    link: str = ""
    note: str = ""
    sort_order: int = 0                   # 排序（拖拽排序 + Excel 导入保留顺序）
    # 材料准备 checklist
    ps_ready: bool = False
    recommendation_ready: bool = False
    cv_ready: bool = False
    transcript_ready: bool = False
    ranking_ready: bool = False
    english_ready: bool = False
    # 复试记录
    interview_date: str = ""
    interview_notes: str = ""

    def to_row(self) -> tuple:
        # IMPORTANT: column order must match the DB schema.
        # v5 CREATE TABLE order: school, major, degree_type, batch, status,
        #   apply_date, deadline, advisor, advisor_status, link, note,
        #   ps_ready, recommendation_ready, cv_ready, transcript_ready,
        #   ranking_ready, english_ready, interview_date, interview_notes
        # v6 ALTER TABLE added at END: college, sort_order
        return (
            self.school, self.major, self.degree_type, self.batch,
            self.status, self.apply_date, self.deadline,
            self.advisor, self.advisor_status,
            self.link, self.note,
            int(self.ps_ready), int(self.recommendation_ready),
            int(self.cv_ready), int(self.transcript_ready),
            int(self.ranking_ready), int(self.english_ready),
            self.interview_date, self.interview_notes,
            self.college, self.sort_order,
        )

    @classmethod
    def from_row(cls, row) -> "GraduateApplication":
        return cls(
            app_id=row[0],
            school=row[1], major=row[2], degree_type=row[3],
            batch=row[4], status=row[5],
            apply_date=row[6] or "", deadline=row[7] or "",
            advisor=row[8] or "", advisor_status=row[9] or "未联系",
            link=row[10] or "", note=row[11] or "",
            ps_ready=bool(row[12]) if len(row) > 12 else False,
            recommendation_ready=bool(row[13]) if len(row) > 13 else False,
            cv_ready=bool(row[14]) if len(row) > 14 else False,
            transcript_ready=bool(row[15]) if len(row) > 15 else False,
            ranking_ready=bool(row[16]) if len(row) > 16 else False,
            english_ready=bool(row[17]) if len(row) > 17 else False,
            interview_date=row[18] if len(row) > 18 else "",
            interview_notes=row[19] if len(row) > 19 else "",
            college=row[20] if len(row) > 20 else "",
            sort_order=row[21] if len(row) > 21 else 0,
        )

    @property
    def has_interview_notes(self) -> bool:
        return bool((self.interview_notes or "").strip())

    @property
    def material_count(self) -> int:
        items = [
            self.ps_ready, self.recommendation_ready,
            self.cv_ready, self.transcript_ready,
            self.ranking_ready, self.english_ready,
        ]
        return sum(1 for x in items if x)

    @property
    def material_text(self) -> str:
        items = []
        if self.ps_ready:
            items.append("个人陈述")
        if self.recommendation_ready:
            items.append("推荐信")
        if self.cv_ready:
            items.append("简历")
        if self.transcript_ready:
            items.append("成绩单")
        if self.ranking_ready:
            items.append("排名证明")
        if self.english_ready:
            items.append("英语成绩")
        return "、".join(items) if items else "未准备"
