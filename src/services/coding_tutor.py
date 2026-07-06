"""DeepSeek-backed coding tutor for the Coding Practice feature."""

import json
import os
import urllib.error
import urllib.request

from PySide6.QtCore import QThread, Signal

from .ai_assistant import get_api_key

# ── Per-method system prompts ─────────────────────────────────────

EXPLAIN_PROMPT = """你是算法编程导师。学生面对一道编程题，请你用中文讲解解题思路。
要求：
- 先分析题目关键点和约束条件
- 介绍 2-3 种可能的解法，比较它们的时间/空间复杂度
- 给出推荐的解法，解释为什么推荐它
- 不要直接给出完整代码，只给出核心思路和伪代码
- 如果题目有多种经典解法（如迭代vs递归），都简要介绍
- 语气亲切、条理清晰，适合学习者阅读"""

REVIEW_PROMPT = """你是严格的代码评审员。学生提交了一段代码来解决一道编程题。
请进行代码审查，用中文反馈：
- **正确性**：代码逻辑是否正确？能处理所有示例和边界情况吗？
- **复杂度**：时间复杂度和空间复杂度分析
- **代码风格**：变量命名是否清晰？结构是否合理？注释是否充分？
- **改进建议**：有没有更优的写法？有没有潜在 bug？
- **总体评分**：给出 1-10 分的评分，并给一句鼓励
请具体引用代码中的逻辑或片段来支撑你的评价，而不是泛泛而谈。"""

HINT_PROMPT = """你是算法编程导师。学生正在做一道编程题但卡住了，请你给出循序渐进的提示。
要求：
- 先分析学生已经写了什么代码，理解他们当前的思路
- 如果代码为空，从最基础的方向开始引导
- 从模糊提示开始（如"考虑使用哈希表来优化查找"），不要直接给答案
- 逐步细化，但每次只给一条提示
- 绝不直接写出完整解法或关键代码
- 如果学生已经接近正确，给最后一步的鼓励性提示"""

GENERATE_PROMPT = """你是算法编程题库生成器。根据指定的难度和主题，生成一道对标 LeetCode 质量的编程题。

输出格式（严格遵守，用 markdown）：
## 题目描述
（用中文写清楚题目要求，包含输入输出说明）

## 示例
（2-3 个示例，每个包含"输入："和"输出："，可加简短解释）

## 约束
（用列表列出数据范围、限制条件）

## 进阶（可选）
（如果题目有更高难度的变体，简要提及）

要求：
- 难度准确：简单=常规思路直接解，中等=需要特定算法技巧，困难=需要综合多个知识点
- 题目不能是原样照抄 LeetCode，要有自己的表述
- 输入输出描述清晰无歧义
- 只输出题目本身，绝对不要贴解法或答案
- 不要用 ``` 包裹整个输出"""


class CodingTutor:
    """Coding practice tutor backed by DeepSeek API."""

    def __init__(self):
        self.api_key = get_api_key()
        self.base_url = os.getenv(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
        ).rstrip("/")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()

    # ── internal API call ─────────────────────────────────────────

    def _call(
        self, system_prompt: str, user_content: str, temperature: float = 0.4,
        retries: int = 2,
    ) -> str:
        if not self.api_key:
            return (
                "尚未配置 DeepSeek API Key。\n"
                "请在 AI 助手面板或 pdptool_config.json 中配置。"
            )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "stream": False,
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        last_error = ""
        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/chat/completions",
                    data=data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=90) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                    choices = body.get("choices") or []
                    if not choices:
                        return "DeepSeek 没有返回可用回答。"
                    return (
                        choices[0].get("message", {}).get("content", "").strip()
                        or "DeepSeek 返回了空内容。"
                    )
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = f"DeepSeek 请求失败：HTTP {exc.code}\n{detail}"
            except Exception as exc:
                last_error = f"DeepSeek 请求失败：{exc}"
                if attempt < retries:
                    import time
                    time.sleep(1.5)

        return last_error

    # ── public methods ────────────────────────────────────────────

    def explain_problem(self, problem_md: str) -> str:
        return self._call(
            EXPLAIN_PROMPT,
            f"请讲解以下编程题的解题思路：\n\n{problem_md}",
            temperature=0.4,
        )

    def review_code(
        self, problem_md: str, user_code: str, language: str = "python"
    ) -> str:
        return self._call(
            REVIEW_PROMPT,
            (
                f"【题目】\n{problem_md}\n\n"
                f"【学生代码 ({language})】\n```{language}\n{user_code}\n```\n\n"
                f"请审查这段代码。"
            ),
            temperature=0.3,
        )

    def give_hint(self, problem_md: str, user_code: str) -> str:
        return self._call(
            HINT_PROMPT,
            (
                f"【题目】\n{problem_md}\n\n"
                f"【学生目前写的代码】\n"
                f"{user_code if user_code.strip() else '（还没开始写）'}\n\n"
                f"请给出一条循序渐进的提示。"
            ),
            temperature=0.5,
        )

    def generate_problem(self, difficulty: str, topic: str) -> str:
        return self._call(
            GENERATE_PROMPT,
            f"请生成一道难度为「{difficulty}」、主题为「{topic}」的编程练习题。",
            temperature=0.7,
        )


class TutorWorker(QThread):
    """Run a CodingTutor method in a background thread."""

    finished = Signal(str)

    def __init__(self, method_name: str, *args, parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.args = args

    def run(self):
        try:
            tutor = CodingTutor()
            method = getattr(tutor, self.method_name)
            result = method(*self.args)
        except Exception as exc:
            result = f"调用失败：{exc}"
        self.finished.emit(result)
