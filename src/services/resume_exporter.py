"""Resume export engine: HTML, Markdown, JSON, and PDF generation.

This module provides the pure-logic layer for resume generation.  It does not
depend on any Qt GUI classes except QPrinter/QTextDocument (for PDF export).
"""

from __future__ import annotations

import html as _html
import json as _json
import os
from typing import Any, Dict, List, Optional

# ── helpers ────────────────────────────────────────────────────────────────


def _esc(val: Any) -> str:
    """Escape a value for safe HTML embedding."""
    if val is None:
        return ""
    return _html.escape(str(val), quote=True)


def _none_str(val: Any, default: str = "") -> str:
    """Return str(val) if not empty/None, else default."""
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


def _join_parts(parts: List[str], sep: str = " ｜ ") -> str:
    """Join non-empty strings with a separator."""
    return sep.join(p for p in parts if p)


# ── default options builder ───────────────────────────────────────────────


def compute_default_options(
    student=None,
    courses=None,
    overview=None,
    experiences=None,
    achievements=None,
    roles=None,
) -> Dict[str, Any]:
    """Build a full options dict auto-filled from student data and computed stats.

    Returns a dict suitable for loading into the resume form editor.
    """
    courses = courses or []
    overview = overview or {}
    experiences = experiences or []
    achievements = achievements or []
    roles = roles or []

    options: Dict[str, Any] = {
        # identity
        "name": "",
        "title": "个人发展简历",
        "email": "",
        "phone": "",
        "city": "",
        "intent": "",
        "avatar_path": "",
        # education
        "school": "",
        "major": "",
        "degree": "本科",
        "education_body": "",
        "summary": "",
        "age": "",
        # skills
        "skills_body": "",
        # project
        "project_name": "",
        "project_body": "",
        # internship / awards
        "internship": "",
        "awards": "",
        # extra
        "custom_content": "",
        # section titles
        "section_title_intent": "求职意向",
        "section_title_education": "教育背景",
        "section_title_skills": "技能特长",
        "section_title_projects": "项目经验",
        "section_title_internship": "实习经历",
        "section_title_awards": "竞赛获奖",
        "section_title_custom": "自我评价",
        # visibility toggles
        "show_intent": True,
        "show_education": True,
        "show_skills": True,
        "show_projects": True,
        "show_internship": True,
        "show_awards": True,
        "show_custom": True,
    }

    if student is not None:
        options["name"] = _none_str(student.name, "姓名")
        options["title"] = _none_str(student.summary, "") or "个人发展简历"
        options["email"] = _none_str(student.email)
        options["phone"] = _none_str(student.phone)
        options["school"] = _none_str(student.college)
        options["major"] = _none_str(student.major)
        options["intent"] = _none_str(student.major)  # default intent = major
        options["skills_body"] = _none_str(student.skills)
        options["summary"] = _none_str(student.summary)
        if student.enrollment_year:
            options["age"] = f"{student.enrollment_year}级"

    # education body = core courses + GPA
    edu_lines: List[str] = []
    if courses:
        course_text = "、".join(
            f"{c.name}（{c.grade:g}）" if c.grade else c.name
            for c in courses[:10]
        )
        edu_lines.append(f"• 核心课程：{course_text}")
    if overview:
        edu_lines.append(
            f"• GPA：{overview.get('weighted_average', 0):.2f}/100"
            f" ｜ 绩点：{overview.get('gpa', 0):.2f}"
            f" ｜ 算术平均分：{overview.get('arithmetic_average', 0):.2f}"
        )
    if edu_lines and not options.get("education_body"):
        options["education_body"] = "\n".join(edu_lines)

    # awards body from achievements
    if achievements and not options.get("awards"):
        lines = []
        for a in achievements[:6]:
            lines.append(f"• {a.title} ｜ {a.ach_type} ｜ {a.issuer} ｜ {a.date}")
            if a.description:
                lines.append(f"  {a.description}")
        options["awards"] = "\n".join(lines)

    # internship from experiences with type "实习"
    if experiences and not options.get("internship"):
        internship_exps = [e for e in experiences if e.exp_type == "实习"]
        if internship_exps:
            lines = []
            for ie in internship_exps:
                dates = f"{ie.start_date} - {ie.end_date}".strip(" -")
                lines.append(f"• {ie.title} @ {ie.organization} ｜ {dates}")
                if ie.description:
                    lines.append(f"  {ie.description}")
            options["internship"] = "\n".join(lines)

    # project body from experiences with type "项目"/"科研"
    if experiences and not options.get("project_body"):
        project_exps = [
            e for e in experiences if e.exp_type in ("项目", "科研")
        ]
        if project_exps:
            first = project_exps[0]
            options["project_name"] = _none_str(first.title)
            lines = []
            for pe in project_exps:
                dates = f"{pe.start_date} - {pe.end_date}".strip(" -")
                lines.append(f"• {pe.title} @ {pe.organization} ｜ {dates}")
                if pe.description:
                    lines.append(f"  {pe.description}")
            options["project_body"] = "\n".join(lines)

    return options


# ── HTML resume ────────────────────────────────────────────────────────────


RESUME_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    background: #f2f3f5;
    color: #1e1e1e;
    line-height: 1.65;
    padding: 32px 16px;
  }}
  .page {{
    max-width: 820px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    padding: 52px 58px 48px 58px;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 2px solid #1f4e79;
    padding-bottom: 22px;
    margin-bottom: 6px;
  }}
  .header-left h1 {{
    font-size: 28px;
    color: #111;
    margin-bottom: 8px;
  }}
  .header-left .subtitle {{
    font-size: 15px;
    color: #4b5563;
    margin-bottom: 4px;
  }}
  .header-left .contact {{
    font-size: 13px;
    color: #6b7280;
    margin-top: 6px;
  }}
  .header-right img {{
    width: 96px;
    height: 118px;
    object-fit: cover;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
  }}
  .header-right .avatar-placeholder {{
    width: 96px;
    height: 118px;
    border: 1px dashed #d1d5db;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #9ca3af;
    font-size: 12px;
    text-align: center;
  }}
  .section {{
    margin-top: 20px;
  }}
  .section-title {{
    font-size: 17px;
    font-weight: 700;
    color: #1f4e79;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 6px;
    margin-bottom: 10px;
  }}
  .section-body {{
    font-size: 14px;
    color: #333;
    line-height: 1.75;
  }}
  .section-body ul {{
    list-style: none;
    padding-left: 0;
  }}
  .section-body li {{
    margin-bottom: 10px;
    padding-left: 16px;
    position: relative;
  }}
  .section-body li::before {{
    content: "•";
    position: absolute;
    left: 0;
    color: #1f4e79;
    font-weight: bold;
  }}
  .section-body .item-title {{
    font-weight: 600;
    color: #111;
  }}
  .section-body .item-meta {{
    font-size: 13px;
    color: #6b7280;
  }}
  @media print {{
    body {{ background: #fff; padding: 0; }}
    .page {{ box-shadow: none; border-radius: 0; max-width: 100%; }}
  }}
</style>
</head>
<body>
<div class="page">
{body}
</div>
</body>
</html>"""


def build_resume_html(
    options: Dict[str, Any],
    student=None,
    courses=None,
    overview=None,
    experiences=None,
    achievements=None,
    roles=None,
) -> str:
    """Build a clean, modern HTML resume string from structured options and data.

    Parameters
    ----------
    options : dict
        Form field values with keys like name, title, email, phone, city,
        intent, school, major, degree, summary, education_body, skills_body,
        project_name, project_body, internship, awards, custom_content,
        section_title_*, show_*, avatar_path.
    student, courses, overview, experiences, achievements, roles :
        Data models (used as fallback when options keys are empty).
    """
    experiences = experiences or []
    courses = courses or []

    # ── header ──
    name = _esc(options.get("name") or (student.name if student else "姓名"))
    title = _esc(options.get("title") or "个人发展简历")
    email = _esc(options.get("email") or (student.email if student else ""))
    phone = _esc(options.get("phone") or (student.phone if student else ""))
    city = _esc(options.get("city") or "")
    intent = _esc(options.get("intent") or "")
    summary_text = _esc(options.get("summary") or (student.summary if student else ""))
    avatar_path = options.get("avatar_path") or ""

    contact_parts = [p for p in [city, phone, email] if p]
    if not contact_parts:
        contact_parts = ["联系方式待补充"]

    body_parts: List[str] = []

    # header block
    body_parts.append('<div class="header">')
    body_parts.append('<div class="header-left">')
    body_parts.append(f"<h1>{name}</h1>")
    if intent:
        body_parts.append(
            f'<div class="subtitle">求职意向：{intent} ｜ {title}</div>'
        )
    else:
        body_parts.append(f'<div class="subtitle">{title}</div>')
    body_parts.append(
        f'<div class="contact">{" ｜ ".join(contact_parts)}</div>'
    )
    if summary_text:
        body_parts.append(
            f'<div style="margin-top:10px; color:#4b5563; font-size:14px;">'
            f"{summary_text}</div>"
        )
    body_parts.append("</div>")  # .header-left

    # avatar
    body_parts.append('<div class="header-right">')
    if avatar_path and os.path.isfile(avatar_path):
        body_parts.append(
            f'<img src="file:///{avatar_path.replace(chr(92), "/")}" '
            f'alt="证件照">'
        )
    else:
        body_parts.append(
            '<div class="avatar-placeholder">点击<br>选择<br>照片</div>'
        )
    body_parts.append("</div>")  # .header-right
    body_parts.append("</div>")  # .header

    # ── sections ──

    def _section(key: str, title_key: str, body: str) -> None:
        """Append a section if visible."""
        if not options.get(f"show_{key}", True):
            return
        if not body.strip():
            return
        sec_title = _esc(options.get(title_key, ""))
        body_parts.append('<div class="section">')
        if sec_title:
            body_parts.append(
                f'<div class="section-title">{sec_title}</div>'
            )
        body_parts.append(f'<div class="section-body">{body}</div>')
        body_parts.append("</div>")

    # intent section
    if options.get("show_intent", True):
        intent_body = f"<p>职位方向：{intent or '待补充'} ｜ 城市：{city or '待补充'}</p>"
        _section("intent", "section_title_intent", intent_body)

    # education
    edu_body = _esc(options.get("education_body") or "")
    if not edu_body and student:
        # build fallback
        lines = []
        if student.college or student.major:
            lines.append(f"<p><b>{_esc(student.college)}</b> ｜ {_esc(student.major)}"
                         f"{' ｜ ' + _esc(student.enrollment_year) + '级' if student.enrollment_year else ''}</p>")
        if courses:
            ct = "、".join(
                f"{_esc(c.name)}（{_esc(c.grade)}）" if c.grade else _esc(c.name)
                for c in courses[:10]
            )
            lines.append(f"<p>核心课程：{ct}</p>")
        if overview:
            lines.append(
                f"<p>GPA：{overview.get('weighted_average', 0):.2f}/100"
                f" ｜ 绩点：{overview.get('gpa', 0):.2f}</p>"
            )
        edu_body = "\n".join(lines)
    _section("education", "section_title_education",
             edu_body.replace("\n", "<br>") if edu_body else "")

    # skills
    skills_body = _esc(options.get("skills_body") or (student.skills if student else ""))
    _section("skills", "section_title_skills",
             f"<p>{skills_body.replace(chr(10), '<br>')}</p>" if skills_body else "")

    # projects
    proj_name = _esc(options.get("project_name") or "")
    proj_body = _esc(options.get("project_body") or "")
    if proj_name and proj_body:
        proj_html = f"<p><b>{proj_name}</b></p><p>{proj_body.replace(chr(10), '<br>')}</p>"
    elif proj_body:
        proj_html = f"<p>{proj_body.replace(chr(10), '<br>')}</p>"
    else:
        proj_html = ""
    _section("projects", "section_title_projects", proj_html)

    # internship
    intern_body = _esc(options.get("internship") or "")
    _section("internship", "section_title_internship",
             f"<p>{intern_body.replace(chr(10), '<br>')}</p>" if intern_body else "")

    # awards
    awards_body = _esc(options.get("awards") or "")
    _section("awards", "section_title_awards",
             f"<p>{awards_body.replace(chr(10), '<br>')}</p>" if awards_body else "")

    # custom / self-evaluation
    custom_body = _esc(options.get("custom_content") or "")
    _section("custom", "section_title_custom",
             f"<p>{custom_body.replace(chr(10), '<br>')}</p>" if custom_body else "")

    body_html = "\n".join(body_parts)
    return RESUME_HTML_TEMPLATE.format(title=name, body=body_html)


# ── Markdown resume ────────────────────────────────────────────────────────


def build_resume_markdown(
    options: Dict[str, Any],
    student=None,
    courses=None,
    overview=None,
    experiences=None,
    achievements=None,
    roles=None,
) -> str:
    """Build a structured Markdown resume string."""
    experiences = experiences or []
    courses = courses or []
    overview = overview or {}

    lines: List[str] = []

    name = options.get("name") or (student.name if student else "姓名")
    title = options.get("title") or "个人发展简历"
    lines.append(f"# {name}")
    lines.append(f"*{title}*")
    lines.append("")

    contact_parts = []
    phone = options.get("phone") or (student.phone if student else "")
    email = options.get("email") or (student.email if student else "")
    city = options.get("city") or ""
    if phone:
        contact_parts.append(f"📱 {phone}")
    if email:
        contact_parts.append(f"📧 {email}")
    if city:
        contact_parts.append(f"📍 {city}")
    if contact_parts:
        lines.append(" | ".join(contact_parts))
        lines.append("")

    summary_text = options.get("summary") or (student.summary if student else "")
    if summary_text:
        lines.append("## 个人简介")
        lines.append(summary_text)
        lines.append("")

    def _md_section(key: str, title_key: str, body: str) -> None:
        if not options.get(f"show_{key}", True):
            return
        if not body.strip():
            return
        sec_title = options.get(title_key, "")
        if sec_title:
            lines.append(f"## {sec_title}")
        lines.append(body)
        lines.append("")

    # education
    edu_body = options.get("education_body") or ""
    if not edu_body and (student or courses or overview):
        edu_lines = []
        if student and (student.college or student.major):
            edu_lines.append(
                f"- **{student.college}** · {student.major}"
                f"{' · ' + student.enrollment_year + '级' if student.enrollment_year else ''}"
            )
        if overview:
            edu_lines.append(
                f"- GPA：{overview.get('weighted_average', 0):.2f}/100"
                f" · 绩点：{overview.get('gpa', 0):.2f}"
            )
        if courses:
            ct = "、".join(
                f"{c.name}（{c.grade:g}）" if c.grade else c.name
                for c in courses[:10]
            )
            edu_lines.append(f"- 核心课程：{ct}")
        edu_body = "\n".join(edu_lines)
    _md_section("education", "section_title_education", edu_body)

    # skills
    skills_body = options.get("skills_body") or (student.skills if student else "")
    _md_section("skills", "section_title_skills", skills_body)

    # projects
    proj_name = options.get("project_name") or ""
    proj_body = options.get("project_body") or ""
    if proj_name:
        _md_section("projects", "section_title_projects",
                    f"### {proj_name}\n{proj_body}")
    else:
        _md_section("projects", "section_title_projects", proj_body)

    # internship
    intern_body = options.get("internship") or ""
    _md_section("internship", "section_title_internship", intern_body)

    # awards
    awards_body = options.get("awards") or ""
    _md_section("awards", "section_title_awards", awards_body)

    # custom
    custom_body = options.get("custom_content") or ""
    _md_section("custom", "section_title_custom", custom_body)

    return "\n".join(lines)


# ── JSON resume ────────────────────────────────────────────────────────────


def build_resume_json(
    options: Dict[str, Any],
    student=None,
    courses=None,
    overview=None,
    experiences=None,
    achievements=None,
    roles=None,
) -> Dict[str, Any]:
    """Build a structured JSON resume.

    Sections are included/excluded based on options show_* flags.
    """
    courses = courses or []
    overview = overview or {}

    resume: Dict[str, Any] = {
        "basics": {
            "name": options.get("name") or (student.name if student else ""),
            "title": options.get("title") or "",
            "email": options.get("email") or (student.email if student else ""),
            "phone": options.get("phone") or (student.phone if student else ""),
            "city": options.get("city") or "",
            "summary": options.get("summary") or (student.summary if student else ""),
            "avatar_path": options.get("avatar_path") or "",
        },
        "sections": [],
    }

    def _add_section(key: str, title_key: str, body: str) -> None:
        if not options.get(f"show_{key}", True):
            return
        if not body.strip():
            return
        resume["sections"].append({
            "key": key,
            "title": options.get(title_key, ""),
            "body": body,
        })

    # education
    edu_body = options.get("education_body") or ""
    if not edu_body:
        parts = []
        if student:
            parts.append(
                f"{student.college} ｜ {student.major}"
                f"{' ｜ ' + student.enrollment_year + '级' if student.enrollment_year else ''}"
            )
        if overview:
            parts.append(
                f"GPA: {overview.get('weighted_average', 0):.2f}"
            )
        edu_body = "\n".join(parts)
    _add_section("education", "section_title_education", edu_body)

    _add_section("skills", "section_title_skills",
                 options.get("skills_body") or (student.skills if student else ""))

    proj_body = options.get("project_body") or ""
    proj_name = options.get("project_name") or ""
    _add_section("projects", "section_title_projects",
                 f"{proj_name}\n{proj_body}".strip())

    _add_section("internship", "section_title_internship",
                 options.get("internship") or "")

    _add_section("awards", "section_title_awards",
                 options.get("awards") or "")

    _add_section("custom", "section_title_custom",
                 options.get("custom_content") or "")

    return resume


# ── PDF export ─────────────────────────────────────────────────────────────


def export_html_to_pdf(html_content: str, pdf_path: str) -> bool:
    """Export an HTML string to a PDF file using QPrinter + QTextDocument.

    Requires a running QApplication instance (always true in PDPTool).

    Returns True on success, False if PySide6 print support is unavailable.
    """
    try:
        from PySide6.QtPrintSupport import QPrinter  # type: ignore[import-untyped]
        from PySide6.QtGui import QTextDocument, QPageSize  # type: ignore[import-untyped]
    except ImportError:
        return False

    doc = QTextDocument()
    doc.setHtml(html_content)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(pdf_path)
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

    # margins — use simple call without unit arg (defaults to Millimeter)
    try:
        printer.setPageMargins(20, 20, 20, 20)
    except Exception:
        pass  # margins are non-essential; use printer defaults

    doc.print_(printer)
    return True
