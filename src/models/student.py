"""Student profile data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Student:
    """Personal information of the student user."""

    student_id: Optional[int] = None
    name: str = ""
    student_no: str = ""       # 学号
    college: str = ""           # 学院
    major: str = ""             # 专业
    enrollment_year: str = ""   # 入学年份
    email: str = ""
    phone: str = ""
    github: str = ""
    linkedin: str = ""
    skills: str = ""            # 技能，逗号分隔
    summary: str = ""           # 个人简介

    def to_row(self) -> tuple:
        return (
            self.name, self.student_no, self.college, self.major,
            self.enrollment_year, self.email, self.phone,
            self.github, self.linkedin, self.skills, self.summary
        )

    @classmethod
    def from_row(cls, row: tuple) -> "Student":
        return cls(
            student_id=row[0],
            name=row[1],
            student_no=row[2],
            college=row[3],
            major=row[4],
            enrollment_year=row[5],
            email=row[6],
            phone=row[7],
            github=row[8] if len(row) > 8 else "",
            linkedin=row[9] if len(row) > 9 else "",
            skills=row[10] if len(row) > 10 else "",
            summary=row[11] if len(row) > 11 else "",
        )

    def to_dict(self) -> dict:
        return {
            "type": "student",
            "student_id": self.student_id,
            "name": self.name,
            "student_no": self.student_no,
            "college": self.college,
            "major": self.major,
            "enrollment_year": self.enrollment_year,
            "email": self.email,
            "phone": self.phone,
            "github": self.github,
            "linkedin": self.linkedin,
            "skills": self.skills,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Student":
        return cls(
            student_id=d.get("student_id"),
            name=d.get("name", ""),
            student_no=d.get("student_no", ""),
            college=d.get("college", ""),
            major=d.get("major", ""),
            enrollment_year=d.get("enrollment_year", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            github=d.get("github", ""),
            linkedin=d.get("linkedin", ""),
            skills=d.get("skills", ""),
            summary=d.get("summary", ""),
        )
