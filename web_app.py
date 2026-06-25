"""PDPTool Web 入口 — FastAPI + Jinja2 服务端渲染。

一份核心逻辑（src/），两个入口：
  python main.py        → PySide6 桌面版
  python web_app.py     → 浏览器 Web 版  http://localhost:8000

API Key 通过环境变量 DEEPSEEK_API_KEY 注入，绝不硬编码在代码里。
"""

from __future__ import annotations

import os
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.database.connection import DatabaseConnection
from src.database.migrations import init_database
from src.database.repositories.course_repo import CourseRepository
from src.database.repositories.experience_repo import ExperienceRepository
from src.database.repositories.achievement_repo import AchievementRepository
from src.database.repositories.role_repo import RoleRepository
from src.database.repositories.student_repo import StudentRepository
from src.database.repositories.internship_application_repo import InternshipApplicationRepository
from src.services.gpa_calculator import calculate_grade_overview, calculate_semester_trend
from src.services.insight_analyzer import InsightAnalyzer
from src.services.resume_exporter import (
    build_resume_html, build_resume_markdown, build_resume_json,
    compute_default_options, export_html_to_pdf,
)
from src.services.ai_assistant import get_api_key

# ── Startup: init database ────────────────────────────────────────────────

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the database exists and is migrated on startup."""
    init_database()
    yield


# ── App init ───────────────────────────────────────────────────────────────

app = FastAPI(title="PDPTool", version="1.1.0", lifespan=lifespan)

# Static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_ROOT, "web", "static")), name="static")

# Templates
from jinja2 import Environment, FileSystemLoader
templates_dir = os.path.join(PROJECT_ROOT, "web", "templates")
jinja_env = Environment(loader=FileSystemLoader(templates_dir))


def render(template_name: str, **context) -> str:
    """Render a Jinja2 template with common context."""
    template = jinja_env.get_template(template_name)

    # Compute global nav context
    student = None
    try:
        repo = StudentRepository()
        student = repo.get()
    except Exception:
        pass

    default_context = {
        "app_name": "PDPTool",
        "student_name": (student.name if student and student.name and student.name != "未设置" else "同学"),
        "api_configured": bool(get_api_key()),
    }
    default_context.update(context)
    return template.render(**default_context)


# ── Helper: get shared data ────────────────────────────────────────────────

def _get_shared_data() -> dict:
    """Load all repositories data needed by most pages."""
    try:
        course_repo = CourseRepository()
        exp_repo = ExperienceRepository()
        ach_repo = AchievementRepository()
        role_repo = RoleRepository()
        student_repo = StudentRepository()
        internship_repo = InternshipApplicationRepository()

        all_courses = course_repo.get_all()
        overview = calculate_grade_overview(all_courses)

        return {
            "courses": all_courses,
            "overview": overview,
            "semester_trend": calculate_semester_trend(all_courses),
            "experiences": exp_repo.get_all(),
            "achievements": ach_repo.get_all(),
            "roles": role_repo.get_all(),
            "student": student_repo.get(),
            "internships": internship_repo.get_all(),
            "course_count": len(all_courses),
            "exp_count": exp_repo.count(),
            "ach_count": ach_repo.count(),
            "role_count": role_repo.count(),
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════════


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Dashboard — overview of everything."""
    data = _get_shared_data()
    student = data.get("student")
    courses = data.get("courses", [])
    overview = data.get("overview", {})
    experiences = data.get("experiences", [])
    achievements = data.get("achievements", [])
    roles = data.get("roles", [])
    internships = data.get("internships", [])

    # Insight
    analyzer = InsightAnalyzer()
    try:
        insight = analyzer.analyze(courses, experiences, achievements, roles)
    except Exception:
        insight = None

    return HTMLResponse(render(
        "dashboard.html",
        overview=overview,
        courses=courses,
        experiences=experiences,
        achievements=achievements,
        roles=roles,
        internships=internships,
        insight=insight,
        course_count=len(courses),
        exp_count=len(experiences),
        ach_count=len(achievements),
        role_count=len(roles),
        internship_count=len(internships),
        semester_trend=data.get("semester_trend", []),
        nav_page="dashboard",
    ))


@app.get("/courses", response_class=HTMLResponse)
async def courses_page():
    """Course management page."""
    data = _get_shared_data()
    courses = sorted(data.get("courses", []), key=lambda c: c.grade, reverse=True)
    overview = data.get("overview", {})

    # Group by semester
    semesters: dict[str, list] = {}
    for c in courses:
        sem = c.semester or "未知学期"
        semesters.setdefault(sem, []).append(c)
    # Sort semester keys
    semester_order = ["大一上", "大一下", "大二上", "大二下", "大三上", "大三下", "大四上", "大四下"]
    ordered = [(s, semesters[s]) for s in semester_order if s in semesters]
    for s in semesters:
        if s not in semester_order:
            ordered.append((s, semesters[s]))

    return HTMLResponse(render(
        "courses.html",
        courses=courses,
        semester_groups=ordered,
        overview=overview,
        nav_page="courses",
    ))


@app.get("/gpa", response_class=HTMLResponse)
async def gpa_page():
    """GPA analysis page."""
    data = _get_shared_data()
    overview = data.get("overview", {})
    semester_trend = data.get("semester_trend", [])
    courses = data.get("courses", [])

    return HTMLResponse(render(
        "gpa.html",
        overview=overview,
        semester_trend=semester_trend,
        courses=courses,
        nav_page="gpa",
    ))


@app.get("/resume", response_class=HTMLResponse)
async def resume_page():
    """Resume preview page."""
    data = _get_shared_data()
    student = data.get("student")
    courses = data.get("courses", [])
    overview = data.get("overview", {})
    experiences = data.get("experiences", [])
    achievements = data.get("achievements", [])
    roles = data.get("roles", [])

    # Top 8 courses by grade
    top_courses = sorted(courses, key=lambda c: c.grade, reverse=True)[:8]

    options = compute_default_options(
        student=student,
        courses=top_courses,
        overview=overview,
        experiences=experiences,
        achievements=achievements,
        roles=roles,
    )

    html_resume = build_resume_html(
        options=options, student=student, courses=top_courses,
        overview=overview, experiences=experiences,
        achievements=achievements, roles=roles,
    )

    return HTMLResponse(render(
        "resume.html",
        resume_html=html_resume,
        options=options,
        nav_page="resume",
    ))


@app.get("/experiences", response_class=HTMLResponse)
async def experiences_page():
    """Experiences overview."""
    data = _get_shared_data()
    experiences = data.get("experiences", [])
    return HTMLResponse(render(
        "experiences.html",
        experiences=experiences,
        nav_page="experiences",
    ))


@app.get("/internships", response_class=HTMLResponse)
async def internships_page():
    """Internship tracking."""
    data = _get_shared_data()
    internships = data.get("internships", [])
    return HTMLResponse(render(
        "internships.html",
        internships=internships,
        nav_page="internships",
    ))


# ── API: resume download ──────────────────────────────────────────────────

@app.get("/api/resume/html")
async def api_resume_html():
    """Download resume as HTML."""
    data = _get_shared_data()
    options = compute_default_options(
        student=data.get("student"),
        courses=sorted(data.get("courses", []), key=lambda c: c.grade, reverse=True)[:8],
        overview=data.get("overview", {}),
        experiences=data.get("experiences", []),
        achievements=data.get("achievements", []),
        roles=data.get("roles", []),
    )
    html = build_resume_html(
        options=options, student=data.get("student"),
        courses=sorted(data.get("courses", []), key=lambda c: c.grade, reverse=True)[:8],
        overview=data.get("overview", {}),
        experiences=data.get("experiences", []),
        achievements=data.get("achievements", []),
        roles=data.get("roles", []),
    )
    from fastapi.responses import Response
    return Response(content=html, media_type="text/html; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=resume.html"})


@app.get("/api/resume/pdf")
async def api_resume_pdf():
    """Download resume as PDF."""
    import tempfile
    data = _get_shared_data()
    options = compute_default_options(
        student=data.get("student"),
        courses=sorted(data.get("courses", []), key=lambda c: c.grade, reverse=True)[:8],
        overview=data.get("overview", {}),
        experiences=data.get("experiences", []),
        achievements=data.get("achievements", []),
        roles=data.get("roles", []),
    )
    html = build_resume_html(
        options=options, student=data.get("student"),
        courses=sorted(data.get("courses", []), key=lambda c: c.grade, reverse=True)[:8],
        overview=data.get("overview", {}),
        experiences=data.get("experiences", []),
        achievements=data.get("achievements", []),
        roles=data.get("roles", []),
    )

    # PDF via QPrinter needs QApplication — use a fallback for headless servers
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        pdf_path = os.path.join(tempfile.gettempdir(), "pdptool_resume.pdf")
        export_html_to_pdf(html, pdf_path)
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        from fastapi.responses import Response
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": "attachment; filename=resume.pdf"})
    except Exception:
        from fastapi.responses import HTMLResponse as HR
        return HR(content=html, media_type="text/html; charset=utf-8",
                  headers={"Content-Disposition": "attachment; filename=resume.html"})


# ── CRUD: Courses ──────────────────────────────────────────────────────────

@app.post("/courses/add")
async def courses_add(request: Request):
    """Handle course add/edit form submission."""
    form = await request.form()
    repo = CourseRepository()

    from src.models.course import Course
    course_id = form.get("course_id", "").strip()
    try:
        name = form.get("name", "").strip()
        credit = float(form.get("credit", "0"))
        grade = float(form.get("grade", "0"))
        semester = form.get("semester", "").strip()
        category = form.get("category", "必修课").strip()
        code = form.get("code", "").strip()
        note = form.get("note", "").strip()

        if not name:
            from fastapi.responses import RedirectResponse
            return RedirectResponse("/courses?error=课程名称不能为空", status_code=303)

        if course_id:
            c = repo.get_by_id(int(course_id))
            if c:
                c.name = name; c.credit = credit; c.grade = grade
                c.semester = semester; c.category = category
                c.code = code; c.note = note
                repo.update(c)
        else:
            c = Course(name=name, code=code, credit=credit, semester=semester,
                       grade=grade, category=category, note=note)
            repo.add(c)
    except ValueError:
        pass  # form validation failed, just redirect

    from fastapi.responses import RedirectResponse
    return RedirectResponse("/courses", status_code=303)


@app.get("/courses/delete/{course_id}")
async def courses_delete(course_id: int):
    """Delete a course."""
    repo = CourseRepository()
    repo.delete(course_id)
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/courses", status_code=303)


# ── CRUD: Experiences ──────────────────────────────────────────────────────

@app.post("/experiences/add")
async def experiences_add(request: Request):
    """Handle experience add/edit."""
    form = await request.form()
    repo = ExperienceRepository()
    from src.models.experience import Experience

    exp_id = form.get("exp_id", "").strip()
    title = form.get("title", "").strip()
    exp_type = form.get("exp_type", "项目").strip()
    organization = form.get("organization", "").strip()
    start_date = form.get("start_date", "").strip()
    end_date = form.get("end_date", "").strip()
    description = form.get("description", "").strip()
    role = form.get("role", "").strip()
    outcome = form.get("outcome", "").strip()

    if not title:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/experiences?error=标题不能为空", status_code=303)

    if exp_id:
        e = repo.get_by_id(int(exp_id))
        if e:
            e.title = title; e.exp_type = exp_type; e.organization = organization
            e.start_date = start_date; e.end_date = end_date
            e.description = description; e.role = role; e.outcome = outcome
            repo.update(e)
    else:
        e = Experience(title=title, exp_type=exp_type, organization=organization,
                       start_date=start_date, end_date=end_date,
                       description=description, role=role, outcome=outcome)
        repo.add(e)

    from fastapi.responses import RedirectResponse
    return RedirectResponse("/experiences", status_code=303)


@app.get("/experiences/delete/{exp_id}")
async def experiences_delete(exp_id: int):
    ExperienceRepository().delete(exp_id)
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/experiences", status_code=303)


# ── CRUD: Achievements ─────────────────────────────────────────────────────

@app.post("/achievements/add")
async def achievements_add(request: Request):
    form = await request.form()
    repo = AchievementRepository()
    from src.models.achievement import Achievement

    ach_id = form.get("ach_id", "").strip()
    title = form.get("title", "").strip()
    ach_type = form.get("ach_type", "奖项").strip()
    issuer = form.get("issuer", "").strip()
    date = form.get("date", "").strip()
    description = form.get("description", "").strip()

    if not title:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/experiences?error=标题不能为空", status_code=303)

    if ach_id:
        a = repo.get_by_id(int(ach_id))
        if a:
            a.title = title; a.ach_type = ach_type; a.issuer = issuer
            a.date = date; a.description = description
            repo.update(a)
    else:
        a = Achievement(title=title, ach_type=ach_type, issuer=issuer,
                        date=date, description=description)
        repo.add(a)

    from fastapi.responses import RedirectResponse
    return RedirectResponse("/experiences", status_code=303)


@app.get("/achievements/delete/{ach_id}")
async def achievements_delete(ach_id: int):
    AchievementRepository().delete(ach_id)
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/experiences", status_code=303)


# ── CRUD: Internships ──────────────────────────────────────────────────────

@app.post("/internships/add")
async def internships_add(request: Request):
    form = await request.form()
    repo = InternshipApplicationRepository()
    from src.models.internship_application import InternshipApplication

    app_id = form.get("app_id", "").strip()
    company = form.get("company", "").strip()
    position = form.get("position", "").strip()
    direction = form.get("direction", "").strip()
    apply_date = form.get("apply_date", "").strip()
    deadline = form.get("deadline", "").strip()
    status = form.get("status", "待投递").strip()
    link = form.get("link", "").strip()
    note = form.get("note", "").strip()

    if not company:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/internships?error=公司名不能为空", status_code=303)

    if app_id:
        a = repo.get_by_id(int(app_id))
        if a:
            a.company = company; a.position = position; a.direction = direction
            a.apply_date = apply_date; a.deadline = deadline; a.status = status
            a.link = link; a.note = note
            repo.update(a)
    else:
        a = InternshipApplication(
            company=company, position=position, direction=direction,
            apply_date=apply_date, deadline=deadline, status=status,
            link=link, note=note,
        )
        repo.add(a)

    from fastapi.responses import RedirectResponse
    return RedirectResponse("/internships", status_code=303)


@app.get("/internships/delete/{app_id}")
async def internships_delete(app_id: int):
    InternshipApplicationRepository().delete(app_id)
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/internships", status_code=303)


# ── AI Chat ────────────────────────────────────────────────────────────────

@app.get("/ai", response_class=HTMLResponse)
async def ai_page():
    """AI 对话页面"""
    return HTMLResponse(render("ai.html", nav_page="ai"))


@app.post("/api/ai/chat")
async def api_ai_chat(request: Request):
    """AI 对话 API — DeepSeek 流式或同步返回"""
    form = await request.form()
    message = form.get("message", "").strip()
    if not message:
        from fastapi.responses import JSONResponse
        return JSONResponse({"reply": "请输入问题。"})

    from src.services.ai_assistant import DeepSeekAssistant
    try:
        assistant = DeepSeekAssistant()
        reply = assistant.ask(message)
        from fastapi.responses import JSONResponse
        return JSONResponse({"reply": reply})
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse({"reply": f"AI 请求失败: {str(e)}"})


# ── Coding Practice ────────────────────────────────────────────────────────

@app.get("/coding", response_class=HTMLResponse)
async def coding_page():
    """编程练习页面 — 显示题库列表"""
    import glob
    problems_dir = os.path.join(PROJECT_ROOT, "coding_problems")
    problems = []
    for md_file in glob.glob(os.path.join(problems_dir, "*.md")):
        name = os.path.basename(md_file).replace(".md", "")
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = ""
        problems.append({"name": name, "content": content[:300]})
    return HTMLResponse(render("coding.html", problems=problems, nav_page="coding"))


# ── run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    import socket
    port = int(os.getenv("PORT", "8000"))

    # Check if port is already in use and auto-pick next available
    original_port = port
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        in_use = sock.connect_ex(("127.0.0.1", port)) == 0
        sock.close()
        if not in_use:
            break
        port += 1
        if port > original_port + 10:
            break

    key_status = "OK" if get_api_key() else "NOT SET - please set DEEPSEEK_API_KEY env var"

    print(f"""
  PDPTool Web v1.1.0
  Local:  http://localhost:{port}
  Deploy: push to GitHub + connect Render/Vercel for public URL
  API Key: {key_status}
""")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
