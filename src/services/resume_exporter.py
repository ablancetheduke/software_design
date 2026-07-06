"""Resume export engine: HTML, Markdown, JSON, and PDF generation.

This module provides the pure-logic layer for resume generation.  It does not
depend on any Qt GUI classes except QPrinter/QTextDocument (for PDF export).
"""

from __future__ import annotations

import html as _html
import json as _json
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
        # education
        "school": "",
        "major": "",
        "degree": "本科",
        "education_body": "",
        "summary": "",
        "age": "",
        # skills
        "skills_body": "",
        # sections
        "academic_body": "",
        "research_body": "",
        "internship": "",
        "competition_body": "",
        "other_body": "",
        "awards": "",
        # section titles
        "section_title_intent": "求职意向",
        "section_title_education": "教育背景",
        "section_title_skills": "技能特长",
        "section_title_academic": "学术经历",
        "section_title_research": "研究经历",
        "section_title_internship": "实习经历",
        "section_title_competition": "竞赛经历",
        "section_title_other": "其它经历",
        "section_title_awards": "荣誉奖项",
        # visibility toggles
        "show_intent": True,
        "show_education": True,
        "show_skills": True,
        "show_academic": True,
        "show_research": True,
        "show_internship": True,
        "show_competition": True,
        "show_other": True,
        "show_awards": True,
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

    # academic body from experiences with type "学术经历"
    if experiences and not options.get("academic_body"):
        acad_exps = [e for e in experiences if e.exp_type == "学术经历"]
        if acad_exps:
            lines = []
            for ae in acad_exps:
                dates = f"{ae.start_date} - {ae.end_date}".strip(" -")
                lines.append(f"• {ae.title} ｜ {ae.organization or '成果'} ｜ {dates}")
                if ae.description:
                    lines.append(f"  {ae.description}")
            options["academic_body"] = "\n".join(lines)

    # research body from experiences with type "研究经历"
    if experiences and not options.get("research_body"):
        research_exps = [e for e in experiences if e.exp_type == "研究经历"]
        if research_exps:
            lines = []
            for re_exp in research_exps:
                dates = f"{re_exp.start_date} - {re_exp.end_date}".strip(" -")
                lines.append(f"• {re_exp.title} ｜ {re_exp.organization or ''} ｜ {dates}")
                if re_exp.description:
                    lines.append(f"  {re_exp.description}")
            options["research_body"] = "\n".join(lines)

    # internship from experiences with type "实习经历"
    if experiences and not options.get("internship"):
        internship_exps = [e for e in experiences if e.exp_type == "实习经历"]
        if internship_exps:
            lines = []
            for ie in internship_exps:
                dates = f"{ie.start_date} - {ie.end_date}".strip(" -")
                lines.append(f"• {ie.title} @ {ie.organization} ｜ {dates}")
                if ie.description:
                    lines.append(f"  {ie.description}")
            options["internship"] = "\n".join(lines)

    # other body from experiences with type "其它"
    if experiences and not options.get("other_body"):
        other_exps = [e for e in experiences if e.exp_type == "其它"]
        if other_exps:
            lines = []
            for oe in other_exps:
                dates = f"{oe.start_date} - {oe.end_date}".strip(" -")
                lines.append(f"• {oe.title} ｜ {oe.organization or ''} ｜ {dates}")
                if oe.description:
                    lines.append(f"  {oe.description}")
            options["other_body"] = "\n".join(lines)

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
    background: #e8e4dd;
    color: #1a1a1a;
    line-height: 1.6;
    padding: 28px 14px;
  }}
  .page {{
    max-width: 780px;
    margin: 0 auto;
    background: #ffffff;
    padding: 48px 56px 44px 56px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.06);
  }}

  /* ── Header ── */
  .header {{
    text-align: center;
    margin-bottom: 18px;
  }}
  .header .name {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 4px;
  }}
  .header .contact {{
    font-size: 11px;
    color: #555;
    letter-spacing: 0.3px;
  }}

  /* ── Section ── */
  .section {{
    margin-top: 16px;
  }}
  .section-title {{
    font-size: 13px;
    font-weight: 700;
    border-bottom: 1px solid #333;
    padding-bottom: 3px;
    margin-bottom: 6px;
    letter-spacing: 1px;
  }}

  /* ── Entry (title + date line) ── */
  .entry {{
    margin-bottom: 4px;
  }}
  .entry-title {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 11.5px;
    font-weight: 700;
    margin-bottom: 1px;
  }}
  .entry-title .title-text {{ }}
  .entry-title .title-date {{
    font-weight: 400;
    color: #555;
    font-size: 11px;
    white-space: nowrap;
    margin-left: 12px;
  }}

  /* ── Bullet ── */
  .bullets {{
    list-style: none;
    padding-left: 0;
  }}
  .bullets li {{
    position: relative;
    padding-left: 14px;
    margin-bottom: 2px;
    font-size: 11px;
    line-height: 1.65;
    text-align: justify;
  }}
  .bullets li::before {{
    content: "•";
    position: absolute;
    left: 0;
    color: #555;
    font-weight: bold;
  }}

  /* ── Bottom info ── */
  .bottom-line {{
    font-size: 10.5px;
    margin-bottom: 1px;
    line-height: 1.55;
  }}
  .bottom-line .lbl {{
    font-weight: 700;
  }}

  @media print {{
    body {{ background: #fff; padding: 0; }}
    .page {{ box-shadow: none; max-width: 100%; padding: 36px 44px; }}
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
    email = _esc(options.get("email") or (student.email if student else ""))
    phone = _esc(options.get("phone") or (student.phone if student else ""))

    contact_bits = []
    if phone:
        contact_bits.append(f"手机：(+86) {phone}")
    if email:
        contact_bits.append(f"邮箱：{email}")
    contact_line = "    ".join(contact_bits) if contact_bits else "联系方式待补充"

    body_parts: List[str] = []

    # header
    body_parts.append('<div class="header">')
    body_parts.append(f'<div class="name">{name}</div>')
    body_parts.append(f'<div class="contact">{contact_line}</div>')
    body_parts.append("</div>")

    # ── section body formatter ──
    def _fmt_section(raw: str) -> str:
        """Turn user text into entry-title + bullets HTML.

        • Title ｜ Sub ｜ Date   → bold entry-title line with date right
        • description line       → bullet <li>
        Other lines             → plain <p>
        """
        if not raw or not raw.strip():
            return ""
        out, lines = [], raw.strip().split("\n")
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                i += 1
                continue

            if s.startswith("• ") and " ｜ " in s:
                parts = s[2:].split(" ｜ ")
                ttl, date = _esc(parts[0].strip()), ""
                mid = ""
                if len(parts) >= 2:
                    date = _esc(parts[-1].strip())
                if len(parts) >= 3:
                    mid = " ｜ " + _esc(" ｜ ".join(parts[1:-1]))
                out.append('<div class="entry">')
                out.append('<div class="entry-title">')
                out.append(f'<span class="title-text">{ttl}{mid}</span>')
                if date:
                    out.append(f'<span class="title-date">{date}</span>')
                out.append('</div></div>')
                out.append('<ul class="bullets">')
                i += 1
                while i < len(lines):
                    sub = lines[i].strip()
                    if not sub:
                        i += 1; continue
                    if sub.startswith("• ") and " ｜ " not in sub:
                        out.append(f"<li>{_esc(sub[2:])}</li>")
                        i += 1
                    else:
                        break
                out.append('</ul>')
                continue

            elif s.startswith("• "):
                out.append('<ul class="bullets">')
                out.append(f"<li>{_esc(s[2:])}</li>")
                i += 1
                while i < len(lines):
                    sub = lines[i].strip()
                    if sub.startswith("• ") and " ｜ " not in sub:
                        out.append(f"<li>{_esc(sub[2:])}</li>")
                        i += 1
                    elif not sub:
                        i += 1
                    else:
                        break
                out.append('</ul>')
                continue

            else:
                out.append(f"<p>{_esc(s)}</p>")
                i += 1

        return "\n".join(out)

    def _section(key: str, title_key: str, body_raw: str) -> None:
        if not options.get(f"show_{key}", True):
            return
        html = _fmt_section(body_raw)
        if not html:
            return
        body_parts.append('<div class="section">')
        body_parts.append(f'<div class="section-title">{_esc(options.get(title_key, ""))}</div>')
        body_parts.append(html)
        body_parts.append("</div>")

    # education
    edu = options.get("education_body") or ""
    if not edu and student:
        lb: List[str] = []
        if student.college or student.major:
            yrs = f" {student.enrollment_year}.09 - {int(student.enrollment_year)+4}.06" if student.enrollment_year else ""
            lb.append(f"• {_esc(student.college)} ｜ {_esc(student.major)} {_esc(options.get('degree','本科'))} ｜{yrs}")
        if courses:
            ct = "、".join(f"{_esc(c.name)}（{_esc(c.grade)}）" if c.grade else _esc(c.name) for c in courses[:10])
            lb.append(f"• 核心课程：{ct}")
        if overview:
            lb.append(f"• GPA：{overview.get('weighted_average', 0):.2f}/100 ｜ 绩点：{overview.get('gpa', 0):.2f}")
        edu = "\n".join(lb)
    _section("education", "section_title_education", edu)

    # academic / research / internship / awards
    _section("academic", "section_title_academic", options.get("academic_body") or "")
    _section("research", "section_title_research", options.get("research_body") or "")
    _section("internship", "section_title_internship", options.get("internship") or "")
    _section("awards", "section_title_awards", options.get("awards") or "")

    # other — bottom-line format
    other_raw = options.get("other_body") or ""
    if options.get("show_other", True) and other_raw.strip():
        body_parts.append('<div class="section">')
        body_parts.append(f'<div class="section-title">{_esc(options.get("section_title_other", "其它"))}</div>')
        for line in other_raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            clean = line.removeprefix("• ").strip()
            if "：" in clean:
                lbl, val = clean.split("：", 1)
                body_parts.append(f'<div class="bottom-line"><span class="lbl">{_esc(lbl.strip())}：</span>{_esc(val.strip())}</div>')
            elif ":" in clean:
                lbl, val = clean.split(":", 1)
                body_parts.append(f'<div class="bottom-line"><span class="lbl">{_esc(lbl.strip())}：</span>{_esc(val.strip())}</div>')
            else:
                body_parts.append(f'<div class="bottom-line">{_esc(clean)}</div>')
        body_parts.append("</div>")

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

    # academic
    _md_section("academic", "section_title_academic", options.get("academic_body") or "")
    # research
    _md_section("research", "section_title_research", options.get("research_body") or "")
    # internship
    _md_section("internship", "section_title_internship", options.get("internship") or "")
    # awards
    _md_section("awards", "section_title_awards", options.get("awards") or "")
    # other
    _md_section("other", "section_title_other", options.get("other_body") or "")

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

    _add_section("academic", "section_title_academic",
                 options.get("academic_body") or "")

    _add_section("research", "section_title_research",
                 options.get("research_body") or "")

    _add_section("internship", "section_title_internship",
                 options.get("internship") or "")

    _add_section("awards", "section_title_awards",
                 options.get("awards") or "")

    _add_section("other", "section_title_other",
                 options.get("other_body") or "")

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
