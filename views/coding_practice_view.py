"""Interview preparation page — LeetCode problems organised by target company.

Ties into the internship tracker: when the user has active applications,
the toolbar shows contextual recommendations (e.g. "备战字节跳动 后端").
AI is used only for review, hints, and explanation — problem generation
is removed in favour of a hand-curated, LeetCode-sourced problem set.
"""

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..database.repositories.internship_application_repo import (
    InternshipApplicationRepository,
)
from ..services.coding_tutor import TutorWorker
from ..utils.markdown_renderer import render_markdown
from ..utils.theme import theme

_PROBLEMS_DIR = Path(__file__).resolve().parent.parent.parent / "coding_problems"
SUPPORTED_LANGUAGES = ["Python", "C++", "Java"]

# ── Company ↔ LeetCode problem mapping ────────────────────────────
# Based on public interview-experience reports for Chinese tech
# companies.  Values are LeetCode problem numbers (strings to match
# the `lc` field in each problem's YAML frontmatter).
COMPANY_PROBLEMS: dict[str, list[str]] = {
    "字节跳动": ["3", "15", "206", "21", "20", "53", "1", "215",
                  "11", "33", "46", "78", "102", "104", "141", "155"],
    "阿里巴巴": ["1", "15", "206", "21", "20", "53", "215",
                  "104", "70", "11", "3", "155"],
    "腾讯":     ["206", "21", "20", "53", "1", "15", "215",
                  "104", "102", "70", "141", "46"],
    "美团":     ["206", "53", "1", "15", "21", "215", "141",
                  "102", "20", "155", "70"],
    "华为":     ["1", "15", "53", "206", "21", "20", "70",
                  "3", "55", "198"],
    "京东":     ["1", "206", "53", "20", "21", "15", "215",
                  "104", "70"],
    "拼多多":   ["1", "53", "206", "15", "20", "21", "215",
                  "33", "55", "78"],
    "百度":     ["206", "53", "1", "15", "3", "20", "21",
                  "46", "78", "33"],
    "快手":     ["206", "1", "15", "53", "21", "20", "3",
                  "11", "102"],
    "网易":     ["1", "206", "15", "53", "20", "21", "70", "102"],
}


class CodingPracticeView(QWidget):
    """Interview preparation — company-aware LeetCode practice.

    Two-column layout: problem description on the left, AI feedback
    and a code editor on the right.  A company filter (driven by
    COMPANY_PROBLEMS) lets students focus on the questions their
    target companies actually ask.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: TutorWorker | None = None
        self._problems: list[dict] = []
        self._current_md: str = ""
        self._setup_ui()
        self._load_problems()

    # ── problem loading ────────────────────────────────────────────

    def _load_problems(self):
        self._problems.clear()
        if not _PROBLEMS_DIR.exists():
            return
        failed: list[str] = []
        for md_file in sorted(_PROBLEMS_DIR.glob("*.md")):
            try:
                p = self._parse_file(md_file)
                if p:
                    self._problems.append(p)
                else:
                    failed.append(md_file.name)
            except Exception as exc:
                failed.append(f"{md_file.name} ({exc})")
        if failed:
            self.feedback_view.setHtml(
                f"<div style='background:{theme.warn_bg}; border:1px solid "
                f"{theme.warn_border}; border-radius:6px; padding:8px 12px; "
                f"color:{theme.fg_muted}; font-size:12px;'>"
                f"⚠ 部分题目加载失败: {', '.join(failed[:5])}</div>"
            )
        self._rebuild_combo()
        if self._problems:
            self._select_index(0)

    @staticmethod
    def _parse_file(filepath: Path) -> dict | None:
        text = filepath.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
        if not m:
            return None
        fm, body = m.group(1), m.group(2).strip()
        meta: dict = {}
        for line in fm.split("\n"):
            line = line.strip()
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip()
            if val.startswith("[") and val.endswith("]"):
                val = [
                    v.strip().strip("'\"")
                    for v in val[1:-1].split(",")
                ]
            meta[key] = val
        lc = str(meta.get("lc", ""))
        companies = [
            c for c, ids in COMPANY_PROBLEMS.items() if lc in ids
        ]
        return {
            "id": meta.get("id", "?"),
            "lc": lc,
            "title": meta.get("title", filepath.stem),
            "difficulty": meta.get("difficulty", "未知"),
            "category": meta.get("category", "其他"),
            "tags": meta.get("tags", []),
            "companies": companies,
            "body": body,
        }

    # ── UI ─────────────────────────────────────────────────────────

    def _setup_ui(self):
        T = theme
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── toolbar ─────────────────────────────────────────────
        tb = QFrame()
        tb.setStyleSheet(
            f"QFrame {{ background: {T.bg_sidebar}; "
            f"border-bottom: 1px solid {T.border}; }}"
        )
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(16, 10, 16, 10)
        tl.setSpacing(10)

        title = QLabel("面试备战")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {T.fg};")
        tl.addWidget(title)

        self.company_combo = QComboBox()
        self.company_combo.setFixedWidth(110)
        self.company_combo.setStyleSheet(self._combo_style())
        self.company_combo.currentTextChanged.connect(self._on_company_changed)
        tl.addWidget(self.company_combo)

        self.cat_combo = QComboBox()
        self.cat_combo.setFixedWidth(100)
        self.cat_combo.setStyleSheet(self._combo_style())
        self.cat_combo.currentTextChanged.connect(self._on_cat_changed)
        tl.addWidget(self.cat_combo)

        self.problem_combo = QComboBox()
        self.problem_combo.setMinimumWidth(280)
        self.problem_combo.setStyleSheet(self._combo_style())
        self.problem_combo.currentIndexChanged.connect(self._on_combo)
        tl.addWidget(self.problem_combo)

        tl.addStretch()

        tl.addWidget(QLabel("语言:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(SUPPORTED_LANGUAGES)
        self.lang_combo.setFixedWidth(90)
        self.lang_combo.setStyleSheet(self._combo_style())
        tl.addWidget(self.lang_combo)

        outer.addWidget(tb)

        # ── internship context banner ───────────────────────────
        self.context_bar = QLabel()
        self.context_bar.setWordWrap(True)
        self.context_bar.setVisible(False)
        self.context_bar.setStyleSheet(
            f"background: {T.warn_bg}; color: {theme.fg_muted}; "
            f"border-bottom: 1px solid {T.warn_border}; "
            f"padding: 8px 16px; font-size: 13px;"
        )
        outer.addWidget(self.context_bar)

        # ── splitter ────────────────────────────────────────────
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(6)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setStyleSheet(T.splitter_style())

        # Left: problem description
        left = QFrame()
        left.setStyleSheet(f"QFrame {{ background: {T.bg_sidebar}; }}")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(10)
        lh = QLabel("题目描述")
        lh.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {T.fg};")
        ll.addWidget(lh)
        self.problem_view = QTextBrowser()
        self.problem_view.setOpenExternalLinks(True)
        self.problem_view.setStyleSheet(
            f"QTextBrowser {{ background: {T.bg_card}; "
            f"border: 1px solid {T.border}; border-radius: 10px; "
            f"padding: 14px; color: {T.fg}; font-size: 13px; }}"
        )
        ll.addWidget(self.problem_view, 1)
        self.splitter.addWidget(left)

        # Right: AI feedback + code editor
        right = QFrame()
        right.setStyleSheet(f"QFrame {{ background: {T.bg_sidebar}; }}")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)

        fh = QLabel("AI 反馈")
        fh.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {T.fg};")
        rl.addWidget(fh)
        self.feedback_view = QTextBrowser()
        self.feedback_view.setOpenExternalLinks(True)
        self.feedback_view.setMinimumHeight(120)
        self.feedback_view.setMaximumHeight(320)
        self.feedback_view.setStyleSheet(
            f"QTextBrowser {{ background: {T.bg_card}; "
            f"border: 1px solid {T.border}; border-radius: 10px; "
            f"padding: 12px; color: {T.fg}; font-size: 13px; }}"
        )
        self._reset_feedback()
        rl.addWidget(self.feedback_view)

        ch = QLabel("你的代码")
        ch.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {T.fg};")
        rl.addWidget(ch)
        self.code_edit = QPlainTextEdit()
        self.code_edit.setPlaceholderText(
            "# 在这里编写你的代码...\n# 支持 Python、C++、Java\n"
        )
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPixelSize(16)
        self.code_edit.setFont(font)
        self.code_edit.setTabStopDistance(32)
        self.code_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.code_edit.setStyleSheet(
            f"QPlainTextEdit {{ background: {T.bg_code}; "
            f"border: 1px solid {T.border}; border-radius: 8px; "
            f"padding: 12px; color: {T.fg}; font-size: 13px; }}"
            f"QPlainTextEdit:focus {{ border-color: {T.accent}; "
            f"background: {T.bg_input}; }}"
        )
        rl.addWidget(self.code_edit, 1)

        # action buttons
        ar = QHBoxLayout()
        ar.setSpacing(8)
        self.explain_btn = self._btn("AI 讲解", self._on_explain)
        ar.addWidget(self.explain_btn)
        self.hint_btn = self._btn("提示", self._on_hint)
        ar.addWidget(self.hint_btn)
        ar.addStretch()
        self.review_btn = self._primary_btn("提交评审", self._on_review)
        ar.addWidget(self.review_btn)
        self.switch_btn = self._btn("换一题", self._on_switch)
        ar.addWidget(self.switch_btn)
        rl.addLayout(ar)

        self.splitter.addWidget(right)
        self.splitter.setSizes([450, 550])
        outer.addWidget(self.splitter, 1)

    def _combo_style(self) -> str:
        T = theme
        return (
            f"padding: 4px 8px; border: 1px solid {T.border}; "
            f"border-radius: 4px; background: {T.bg_input}; "
            f"color: {T.fg}; font-size: 13px;"
        )

    def _btn(self, text: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(theme.subtle_btn_style())
        btn.clicked.connect(slot)
        return btn

    def _primary_btn(self, text: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(theme.primary_btn_style())
        btn.clicked.connect(slot)
        return btn

    # ── combo management ──────────────────────────────────────────

    def _rebuild_combo(self):
        self.company_combo.blockSignals(True)
        old_company = self.company_combo.currentText()
        companies = sorted(COMPANY_PROBLEMS.keys())
        self.company_combo.clear()
        self.company_combo.addItem("全部公司")
        self.company_combo.addItems(companies)
        if old_company and self.company_combo.findText(old_company) >= 0:
            self.company_combo.setCurrentText(old_company)
        else:
            self.company_combo.setCurrentIndex(0)
        self.company_combo.blockSignals(False)

        self.cat_combo.blockSignals(True)
        old_cat = self.cat_combo.currentText()
        cats = sorted({p.get("category", "其他") for p in self._problems})
        self.cat_combo.clear()
        self.cat_combo.addItem("全部分类")
        for c in cats:
            self.cat_combo.addItem(c)
        if old_cat and self.cat_combo.findText(old_cat) >= 0:
            self.cat_combo.setCurrentText(old_cat)
        else:
            self.cat_combo.setCurrentIndex(0)
        self.cat_combo.blockSignals(False)

        self._rebuild_problem_combo()

    def _rebuild_problem_combo(self):
        company = self.company_combo.currentText()
        cat = self.cat_combo.currentText()
        self.problem_combo.blockSignals(True)
        self.problem_combo.clear()
        for p in self._problems:
            if cat != "全部分类" and p.get("category", "其他") != cat:
                continue
            if company != "全部公司" and company not in p.get("companies", []):
                continue
            lc = p.get("lc", "")
            lc_str = f" LC{lc}" if lc else ""
            label = f"[{p['difficulty']}]{lc_str}  {p['title']}"
            self.problem_combo.addItem(label, p)
        self.problem_combo.blockSignals(False)
        if self.problem_combo.count() > 0:
            self.problem_combo.setCurrentIndex(0)

    def _on_company_changed(self, _text: str):
        self._rebuild_problem_combo()

    def _on_cat_changed(self, _text: str):
        self._rebuild_problem_combo()

    def _select_index(self, idx: int):
        if 0 <= idx < self.problem_combo.count():
            self.problem_combo.setCurrentIndex(idx)

    def _on_combo(self, idx: int):
        if idx < 0:
            return
        problem = self.problem_combo.itemData(idx)
        if problem:
            self._show_problem(problem)

    # ── problem display ───────────────────────────────────────────

    def _show_problem(self, p: dict):
        T = theme
        self._current_md = p["body"]

        diff_color = T.diff_color(p.get("difficulty", ""))
        lc = p.get("lc", "")
        lc_badge = ""
        if lc:
            lc_badge = (
                f"<span style='margin-left:10px; font-size:12px; "
                f"background:{T.accent}; color:white; padding:1px 8px; "
                f"border-radius:3px; font-weight:bold;'>LC {lc}</span>"
            )

        companies = p.get("companies", [])
        company_html = ""
        if companies:
            chips = "".join(
                f"<span style='background:{T.bg_badge}; padding:2px 7px; "
                f"border-radius:3px; font-size:11px; color:{T.fg_muted}; "
                f"margin-right:4px;'>{c}</span>"
                for c in companies[:6]
            )
            company_html = f"<div style='margin-top:6px;'>{chips}</div>"

        tags_html = ""
        if p.get("tags"):
            tags_html = "　".join(
                f"<span style='background:{T.bg_sidebar}; padding:2px 8px; "
                f"border-radius:3px; font-size:11px; color:{T.fg_muted};'>"
                f"#{t}</span>"
                for t in p["tags"]
            )

        header = (
            f"<div style='margin-bottom:16px;'>"
            f"<span style='font-size:18px; font-weight:bold; "
            f"color:{T.fg};'>{p['title']}</span>"
            f"<span style='margin-left:12px; font-size:13px; "
            f"color:{diff_color}; font-weight:bold;'>"
            f"[{p.get('difficulty', '')}]</span>"
            f"{lc_badge}"
            f"<br><span style='font-size:12px;'>{tags_html}</span>"
            f"{company_html}</div>"
        )

        body_html = render_markdown(p["body"])
        self.problem_view.setHtml(f"{header}{body_html}")
        self._reset_feedback()

    # ── internship context ────────────────────────────────────────

    def _update_context_bar(self):
        try:
            repo = InternshipApplicationRepository()
            apps = repo.get_all()
        except Exception:
            apps = []

        active = [a for a in apps if a.status in (
            "待投递", "已投递", "笔试", "一面", "二面"
        )]
        if not active:
            self.context_bar.setVisible(False)
            return

        companies_seen: set[str] = set()
        directions_seen: set[str] = set()
        for a in active[:8]:
            if a.company:
                companies_seen.add(a.company)
            if a.direction:
                directions_seen.add(a.direction)

        parts: list[str] = []
        if companies_seen:
            parts.append("、".join(sorted(companies_seen)[:4]))
        if directions_seen:
            parts.append("、".join(sorted(directions_seen)[:3]))
        target = " · ".join(parts) if parts else "实习备战"

        direction_categories: dict[str, str] = {
            "算法": "数组、动态规划、树",
            "开发": "链表、栈、堆、双指针",
            "数据": "数组、滑动窗口、二分查找",
        }
        suggestions: list[str] = []
        for d in directions_seen:
            sug = direction_categories.get(d)
            if sug and sug not in suggestions:
                suggestions.append(sug)
        suggestion_text = (
            f"—— 推荐练习：{'、'.join(suggestions)}"
            if suggestions else ""
        )

        self.context_bar.setText(
            f"🎯 当前备战：{target} {suggestion_text}"
        )
        self.context_bar.setVisible(True)

    # ── AI actions ─────────────────────────────────────────────────

    def _on_explain(self):
        if not self._current_md:
            return
        self._run("explain_problem", self._current_md,
                  loading="AI 正在分析题目思路...")

    def _on_review(self):
        if not self._current_md:
            QMessageBox.information(self, "提示", "请先选择一道题目。")
            return
        code = self.code_edit.toPlainText().strip()
        if not code:
            QMessageBox.information(self, "提示", "请先在右侧编辑器中编写代码。")
            return
        language = self.lang_combo.currentText().lower()
        self._run("review_code", self._current_md, code, language,
                  loading="AI 正在评审代码...")

    def _on_hint(self):
        if not self._current_md:
            return
        self._run("give_hint", self._current_md, self.code_edit.toPlainText(),
                  loading="AI 正在思考提示...")

    def _on_switch(self):
        n = self.problem_combo.count()
        if n > 1:
            self.problem_combo.setCurrentIndex(
                (self.problem_combo.currentIndex() + 1) % n
            )

    # ── worker ─────────────────────────────────────────────────────

    def _run(self, method: str, *args, loading: str = "请稍候..."):
        if self._worker is not None and self._worker.isRunning():
            return
        self._set_btns(False)
        self.feedback_view.setHtml(
            f"<div style='color:{theme.fg_muted}; font-style:italic; "
            f"padding:8px;'>{loading}</div>"
        )
        self._start_worker(method, *args)

    def _start_worker(self, method: str, *args, on_done=None):
        self._worker = TutorWorker(method, *args, parent=self)
        self._worker.finished.connect(on_done or self._show_result)
        self._worker.finished.connect(lambda: setattr(self, "_worker", None))
        self._worker.finished.connect(lambda: self._set_btns(True))
        self._worker.start()

    def _show_result(self, text: str):
        html_body = render_markdown(text)
        self.feedback_view.setHtml(
            f"<div style='background:{theme.ai_bubble}; border-radius:8px; "
            f"padding:12px 16px; line-height:1.6;'>{html_body}</div>"
        )

    def _reset_feedback(self):
        self.feedback_view.setHtml(
            f"<div style='color:{theme.fg_muted}; font-style:italic; "
            f"padding:8px;'>点击 AI 讲解、提示或提交评审按钮开始</div>"
        )

    def _set_btns(self, enabled: bool):
        for b in [self.explain_btn, self.hint_btn,
                  self.review_btn, self.switch_btn]:
            b.setEnabled(enabled)

    # ── public ─────────────────────────────────────────────────────

    def refresh(self):
        self._load_problems()
        self._update_context_bar()
