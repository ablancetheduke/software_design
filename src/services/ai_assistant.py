"""DeepSeek-backed AI assistant service."""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import List

from ..database.repositories.achievement_repo import AchievementRepository
from ..database.repositories.course_repo import CourseRepository
from ..database.repositories.experience_repo import ExperienceRepository
from ..database.repositories.internship_application_repo import InternshipApplicationRepository
from ..database.repositories.role_repo import RoleRepository
from ..database.repositories.student_repo import StudentRepository
from .curriculum_auditor import CurriculumAuditor
from .curriculum_plan_store import CurriculumPlanStore
from .gpa_calculator import calculate_grade_overview


CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "pdptool_config.json"


def _read_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_api_key(key: str) -> None:
    cfg = _read_config()
    cfg["deepseek_api_key"] = key.strip()
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)


def get_api_key() -> str:
    env_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if env_key:
        return env_key
    return _read_config().get("deepseek_api_key", "").strip()


SYSTEM_PROMPT = """
你是 PDPTool 内置的「大学生个人发展规划顾问」AI，不是死板的学分审计机器人。

## 你的角色
你的工作是像一个靠谱的学长/学姐一样，结合用户的实际数据，给出具体、可执行的建议。
你可以讨论的话题非常广泛——课程修读、成绩趋势、简历优化、实习投递策略、技能提升路径
等等，但**只在用户主动问到时才展开**，不要把所有回答都引向学分。

## 你可用的数据
每条请求里你会收到两部分信息：
1. **培养方案知识库**：按专业和年级切分的结构化培养方案片段（模块、学分要求、可选课程代码）
2. **学生数据摘要**：用户的个人信息、全部已修课程（含成绩和学分）、GPA、经历（竞赛/项目/实习/
   科研）、荣誉证书、组织角色、实习投递记录

## 各领域的回答原则

### 学分 / 培养方案（用户主动问"还差什么""学分够吗"时才用）
- 逐模块对比已修课程与方案要求。
- 必修课：优先用课程代码判断是否已修，代码缺失时可参考课程名但要注明不确定。
- 选修课：只判断学分是否补足，不要强制推荐具体课程。
- 不要每次回答都扯到这里——除非用户的问题本身就关于毕业/学分/选课。

### GPA / 成绩分析（用户问成绩、排名、趋势时用）
- 引用 GPA 数据和加权/算术平均。
- 指出高分/低分课程的类型特征（如"数学类成绩偏低"），据此给选课或补弱建议。
- 不要把成绩分析硬转为"你还差XX学分"。

### 简历 / 经历优化（用户问简历、经历怎么写时用）
- 根据经历摘要（类型-标题-角色-成果），挑出最能体现能力的条目。
- 建议 STAR 法则改写、量化成果、突出与目标岗位相关的经历。
- 如果学生的技能字段为空或经历描述太简略，直接指出需要补充什么。

### 实习投递（用户问投递策略、时间规划时用）
- 根据实习投递记录（公司-岗位-状态-截止日期）分析当前进度。
- 提醒临近截止的岗位，建议投递节奏。
- 如果简历/项目还没准备好（resume_ready/project_ready），提醒优先补齐。

### 技能提升 / 学习路径（用户问学什么、怎么提升时用）
- 结合已修课程和技能标签，发现技能盲区。
- 推荐具体的学习方向或项目思路，但不要凭空捏造课程代码。

## 行为准则
- **问什么答什么**：用户问简历就聊简历，问实习就聊实习，不要强行拐到学分。
- **用数据说话**：引用具体的课程名、分数、经历标题，而不是泛泛而谈。
- **数据不足时直说**：比如用户问简历优化但还没录入经历，就直接建议先去「经历管理」页补充。
- **简洁但具体**：不要写长篇大论，给出 3-5 条最关键的要点即可。
- **中文回答**，语气自然亲切但不过分随意。

## 严禁行为
- 不要在用户问 GPA 或简历时扯到培养方案学分。
- 不要编造不存在的数据或课程。
- 不要用"首先...其次...最后...综上所述"的八股模板。
""".strip()


class DeepSeekAssistant:
    """Small wrapper around DeepSeek's OpenAI-compatible chat API."""

    def __init__(self):
        self.api_key = get_api_key()
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

    def ask(self, question: str) -> str:
        if not self.api_key:
            return (
                "还没有配置 DeepSeek API Key。\n\n"
                "请先在系统环境变量里设置 DEEPSEEK_API_KEY，或通过配置文件 pdptool_config.json 保存。"
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"【培养方案知识库】\n{self._build_plan_context(question)}\n\n"
                        f"【学生数据摘要】\n{self._build_student_context()}\n\n"
                        f"【用户问题】\n{question}"
                    ),
                },
            ],
            "temperature": 0.4,
            "stream": False,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return f"DeepSeek 请求失败：HTTP {exc.code}\n{detail}"
        except Exception as exc:
            return f"DeepSeek 请求失败：{exc}"

        choices = body.get("choices") or []
        if not choices:
            return "DeepSeek 没有返回可用回答。"
        return choices[0].get("message", {}).get("content", "").strip() or "DeepSeek 返回了空内容。"

    def _build_plan_context(self, question: str) -> str:
        student = StudentRepository().get()
        major = student.major if student else ""
        cohort_year = student.enrollment_year if student else ""
        return CurriculumPlanStore().context_for_ai(
            major=major,
            cohort_year=cohort_year,
            question=question,
            limit=24,
        )

    def _build_student_context(self) -> str:
        course_repo = CourseRepository()
        exp_repo = ExperienceRepository()
        ach_repo = AchievementRepository()
        role_repo = RoleRepository()
        internship_repo = InternshipApplicationRepository()
        student_repo = StudentRepository()

        courses = course_repo.get_all()
        experiences = exp_repo.get_all()
        achievements = ach_repo.get_all()
        roles = role_repo.get_all()
        internships = internship_repo.get_all()
        student = student_repo.get()

        overview = calculate_grade_overview(courses)
        auditor = CurriculumAuditor()
        total_audit = auditor.audit_total(courses)
        categories = auditor.audit_dashboard_categories(courses)

        lines: List[str] = []
        if student:
            lines.append(
                f"学生：{student.name or '未填写'}；学院：{student.college or '未填写'}；"
                f"专业：{student.major or '未填写'}；入学年份：{student.enrollment_year or '未填写'}"
            )
            if student.skills:
                lines.append(f"技能：{student.skills}")
            if student.summary:
                lines.append(f"个人简介：{student.summary}")

        lines.append(
            f"课程：共 {len(courses)} 门，总学分 {sum(c.credit for c in courses):g}；"
            f"GPA {overview['gpa']:.2f}；加权平均 {overview['weighted_average']:.2f}；"
            f"算术平均 {overview['arithmetic_average']:.2f}"
        )
        lines.append(
            f"当前程序审计结果：目标 145 学分，已匹配 {total_audit.earned_credits:g}，"
            f"还差 {total_audit.remaining_credits:g}，完成度 {total_audit.completion_ratio:.0%}"
        )

        weak_categories = [
            item for item in categories
            if item.required_credits > 0 and item.remaining_credits > 0
        ][:8]
        if weak_categories:
            lines.append(
                "待补齐类别："
                + "；".join(
                    f"{item.name} 已完成 {item.earned_credits:g}/{item.required_credits:g}，还差 {item.remaining_credits:g}"
                    for item in weak_categories
                )
            )

        if courses:
            lines.append(
                "已修课程："
                + "；".join(
                    f"{c.name}({c.code or '无代码'}, {c.credit:g}学分, {c.grade:g}分)"
                    for c in courses
                )
            )

        lines.append(f"经历：{len(experiences)} 条；荣誉/证书：{len(achievements)} 条；组织角色：{len(roles)} 条")
        if experiences:
            lines.append(
                "经历摘要："
                + "；".join(
                    f"{e.exp_type}-{e.title}-{e.role or '未填角色'}-{e.outcome or '未填成果'}"
                    for e in experiences[:8]
                )
            )
        if achievements:
            lines.append(
                "荣誉摘要："
                + "；".join(f"{a.ach_type}-{a.title}-{a.date}" for a in achievements[:8])
            )
        if internships:
            lines.append(
                "实习投递："
                + "；".join(
                    f"{app.company}-{app.position}-{app.direction}-{app.status}-截止{app.deadline or '未填'}"
                    for app in internships[:10]
                )
            )
        else:
            lines.append("实习投递：暂无记录")

        return "\n".join(lines)
