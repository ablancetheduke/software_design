"""Resume enhancement: STAR rewrites, HTML/Markdown generation."""

import html
import json
import os
import urllib.error
import urllib.request

from PySide6.QtCore import QThread, Signal

from .ai_assistant import get_api_key

STAR_PROMPT = """你是技术岗简历优化专家。请将用户提供的经历描述改写为 STAR 法则格式
（Situation-Task-Action-Result），每条经历输出 2-3 句精炼描述。

要求：
- 突出技术细节和量化成果（如"性能提升 30%""处理 10 万条数据"）
- 用主动动词开头（设计、实现、优化、主导、构建）
- 去掉空泛描述（如"学习了""了解了"）
- 每条输出控制在 80 字以内
- 中文输出，保持专业但不生硬"""


class ResumeTutor:
    """Lightweight resume AI — STAR rewrites and Markdown generation."""

    def __init__(self):
        self.api_key = get_api_key()
        self.base_url = os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        ).rstrip("/")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

    def _call(self, system_prompt: str, user_content: str) -> str:
        if not self.api_key:
            return "尚未配置 DeepSeek API Key。"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.5,
            "stream": False,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return f"请求失败：{exc}"
        choices = body.get("choices") or []
        if not choices:
            return "AI 没有返回内容。"
        return choices[0].get("message", {}).get("content", "").strip()

    def rewrite_star(self, exp_title: str, exp_desc: str,
                     exp_role: str = "", exp_outcome: str = "") -> str:
        parts = [f"经历：{exp_title}"]
        if exp_role:
            parts.append(f"角色：{exp_role}")
        if exp_desc:
            parts.append(f"原始描述：{exp_desc}")
        if exp_outcome:
            parts.append(f"成果：{exp_outcome}")
        parts.append("\n请用 STAR 法则改写这段经历。")
        return self._call(STAR_PROMPT, "\n".join(parts))

    def rewrite_all_experiences(self, experiences: list) -> str:
        """Rewrite multiple experiences at once — returns structured result."""
        if not experiences:
            return ""
        lines = ["请逐条改写以下经历，每条用 --- 分隔：\n"]
        for e in experiences:
            lines.append(
                f"【{e.exp_type}】{e.title}\n"
                f"角色：{e.role or '未填'}\n"
                f"描述：{e.description or '无'}\n"
                f"成果：{e.outcome or '无'}\n"
            )
        return self._call(STAR_PROMPT, "\n".join(lines))


class ResumeWorker(QThread):
    finished = Signal(str)
    def __init__(self, method: str, *args, parent=None):
        super().__init__(parent)
        self._method = method
        self._args = args
    def run(self):
        try:
            tutor = ResumeTutor()
            result = getattr(tutor, self._method)(*self._args)
        except Exception as e:
            result = f"错误：{e}"
        self.finished.emit(result)


# ── HTML resume builder ───────────────────────────────────────────

def _esc(val) -> str:
    """Escape a value for safe HTML embedding."""
    if val is None:
        return ""
    return html.escape(str(val), quote=True)


def _section_html(title: str, body: str) -> str:
    return (
        f"<h2 style='font-size:18px; border-bottom:1px solid #333; "
        f"padding-bottom:4px; margin:18px 0 8px 0;'>{title}</h2>{body}"
    )


def _experience_section_html(title: str, experiences: list) -> str:
    if not experiences:
        return _section_html(
            title,
            "<p style='color:#888;'>暂无，可在经历管理中添加或粘贴导入。</p>",
        )
    items = ""
    for exp in experiences:
        date_range = f"{exp.start_date} - {exp.end_date}".strip(" -")
        meta = " ｜ ".join(
            p for p in [exp.organization, date_range, exp.role] if p
        )
        desc = html.escape(str(exp.description), quote=True) if exp.description else ""
        outcome = html.escape(str(exp.outcome), quote=True) if exp.outcome else ""
        items += (
            f"<li><b>{html.escape(exp.title, quote=True)}</b>"
            f"{' ｜ ' + html.escape(meta, quote=True) if meta else ''}<br>"
            f"{desc}"
            f"{'<br>成果：' + outcome if outcome else ''}</li>"
        )
    return _section_html(title, f"<ul>{items}</ul>")


def build_html_resume(
    student, courses, overview, achievements,
    research, competitions, internships,
    hobbies="", extra="",
) -> str:
    """Build a clean HTML resume string from structured data."""
    name = "姓名"
    if student and student.name and student.name != "未设置":
        name = student.name

    college = _esc(student.college if student else "")
    major = _esc(student.major if student else "")
    phone = _esc(student.phone if student else "")
    email = _esc(student.email if student else "")
    summary = _esc(student.summary if student else "")
    enrollment = _esc(student.enrollment_year if student else "")

    contact = " ｜ ".join(p for p in [phone, email, college, major] if p)

    parts = [
        f"""<div style="font-family: Microsoft YaHei, SimSun, sans-serif; color:#222; line-height:1.55;">
  <h1 style="text-align:center; margin:0; font-size:28px;">{_esc(name)}</h1>
  <p style="text-align:center; color:#555; margin:6px 0 18px 0;">{contact}</p>
"""
    ]

    if student and student.summary:
        parts.append(_section_html("个人简介", f"<p>{summary}</p>"))

    course_text = "、".join(
        f"{_esc(c.name)}（{_esc(c.grade)}）" if c.grade else _esc(c.name)
        for c in courses
    )
    education_body = (
        f"<p><b>{college or '学校'}</b> ｜ {major or '专业'}"
        f"{' ｜ ' + enrollment + '级' if enrollment else ''}</p>"
        f"<ul>"
        f"<li><b>核心课程：</b>{course_text or '请在左侧勾选要展示的课程'}</li>"
        f"<li><b>GPA：</b>{overview['weighted_average']:.2f}/100"
        f" ｜ 绩点：{overview['gpa']:.2f}"
        f" ｜ 算术平均分：{overview['arithmetic_average']:.2f}</li>"
        f"</ul>"
    )
    parts.append(_section_html("教育背景", education_body))

    parts.append(_experience_section_html("科研/项目经历", research))
    parts.append(_experience_section_html("比赛经历", competitions))
    parts.append(_experience_section_html("实习经历", internships))

    if achievements:
        items = "".join(
            f"<li><b>{_esc(a.title)}</b> ｜ {_esc(a.ach_type)} ｜ "
            f"{_esc(a.issuer)} ｜ {_esc(a.date)}<br>{_esc(a.description)}</li>"
            for a in achievements
        )
        parts.append(_section_html("荣誉奖项", f"<ul>{items}</ul>"))

    if hobbies:
        parts.append(_section_html("个人爱好", f"<p>{_esc(hobbies)}</p>"))
    if extra:
        parts.append(_section_html("补充说明", f"<p>{_esc(extra)}</p>"))

    parts.append("</div>")
    return "".join(parts)


HTML_DOCUMENT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>个人简历</title>
<style>
body {{
    max-width: 860px;
    margin: 36px auto;
    padding: 32px;
    font-family: "Microsoft YaHei", "SimSun", sans-serif;
    color: #222;
}}
table {{ border-collapse: collapse; }}
th {{ background: #f3f4f6; }}
td, th {{ border: 1px solid #d1d5db; }}
li {{ margin-bottom: 8px; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ── Markdown template ─────────────────────────────────────────────

def build_markdown_resume(
    student, courses, overview, experiences,
    achievements, hobbies="", extra=""
) -> str:
    """Build a clean tech-interview Markdown resume string."""
    name = (student.name if student and student.name
            and student.name != "未设置" else "姓名")
    lines = [
        f"# {name}",
        "",
    ]
    contact_parts = []
    if student:
        if student.phone:
            contact_parts.append(f"📱 {student.phone}")
        if student.email:
            contact_parts.append(f"📧 {student.email}")
        if student.github:
            contact_parts.append(f"[GitHub]({student.github})")
    if contact_parts:
        lines.append(" | ".join(contact_parts))
        lines.append("")

    if student and student.summary:
        lines.append("## 个人简介")
        lines.append("")
        lines.append(student.summary)
        lines.append("")

    # education
    lines.append("## 教育背景")
    lines.append("")
    college = student.college if student else ""
    major = student.major if student else ""
    year = f" {student.enrollment_year}级" if student and student.enrollment_year else ""
    lines.append(f"- **{college}** · {major}{year}")
    lines.append(f"- GPA：{overview['weighted_average']:.2f}/100 · "
                 f"绩点：{overview['gpa']:.2f}")
    if courses:
        course_text = "、".join(
            f"{c.name}（{c.grade:g}）" if c.grade else c.name
            for c in courses[:10]
        )
        lines.append(f"- 核心课程：{course_text}")
    lines.append("")

    # experiences by type
    for section_title, key, emoji in [
        ("项目 / 科研经历", ["科研", "项目"], "🔬"),
        ("竞赛经历", ["竞赛"], "🏆"),
        ("实习经历", ["实习"], "💼"),
        ("其他经历", ["其他"], "📌"),
    ]:
        items = [e for e in experiences if e.exp_type in key]
        if not items:
            continue
        lines.append(f"## {section_title}")
        lines.append("")
        for e in items:
            date = f"{e.start_date} - {e.end_date}".strip(" -")
            lines.append(f"### {e.title}")
            lines.append("")
            if e.organization or date or e.role:
                meta = " | ".join(
                    p for p in [e.organization, date, e.role] if p
                )
                lines.append(f"*{meta}*")
                lines.append("")
            if e.description:
                lines.append(e.description)
                lines.append("")
            if e.outcome:
                lines.append(f"- 成果：{e.outcome}")
                lines.append("")
            lines.append("")

    # achievements
    if achievements:
        lines.append("## 荣誉奖项")
        lines.append("")
        for a in achievements:
            lines.append(f"- **{a.title}** · {a.ach_type} · {a.issuer} · {a.date}")
        lines.append("")

    # skills
    if student and student.skills:
        lines.append("## 技能")
        lines.append("")
        lines.append(student.skills)
        lines.append("")

    if hobbies:
        lines.append("## 个人爱好")
        lines.append("")
        lines.append(hobbies)
        lines.append("")

    if extra:
        lines.append("## 补充说明")
        lines.append("")
        lines.append(extra)
        lines.append("")

    return "\n".join(lines)
