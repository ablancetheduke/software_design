"""AI assistant side panel — warm paper palette matching the main app."""

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFrame,
    QSizePolicy,
)

from ..services.ai_assistant import DeepSeekAssistant, get_api_key, save_api_key
from ..utils.markdown_renderer import render_markdown
from ..utils.theme import theme


class AiWorker(QThread):
    """Run DeepSeek request without blocking the UI."""

    finished = Signal(str)

    def __init__(self, question: str, parent=None):
        super().__init__(parent)
        self.question = question

    def run(self):
        self.finished.emit(DeepSeekAssistant().ask(self.question))


class AiAssistantPanel(QWidget):
    """Right-side AI chat panel — warm, paper-like style consistent with PDPTool."""

    close_requested = Signal()

    # Palette helper — reads current theme every time it's called
    @staticmethod
    def _t(key: str) -> str:
        return getattr(theme, {
            "BG_PANEL": "bg_sidebar", "BG_CHAT": "bg_card",
            "BORDER": "border", "TEXT_MAIN": "fg",
            "TEXT_SUB": "fg_muted", "ACCENT": "accent",
            "ACCENT_HOV": "accent_hover", "AI_BUBBLE": "ai_bubble",
            "USER_BUBBLE": "user_bubble", "BTN_SUBTLE": "nav_hover_bg",
            "BTN_SUBTLE_BORDER": "border_input", "WARN_BG": "warn_bg",
            "WARN_BORDER": "warn_border",
        }[key])

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._key_configured = bool(get_api_key())
        self._setup_ui()

    # ── UI construction ─────────────────────────────────────────────

    def _setup_ui(self):
        self.setObjectName("AiAssistantPanel")
        self.setStyleSheet(f"""
            #AiAssistantPanel {{
                background: {self._t("BG_PANEL")};
                border-left: 1px solid {self._t("BORDER")};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # ── header ──────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(10)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("🎓 AI 助手")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {self._t("TEXT_MAIN")};"
        )

        subtitle = QLabel("DeepSeek · 发展规划问答")
        subtitle.setStyleSheet(
            f"font-size: 12px; color: {self._t("TEXT_SUB")};"
        )
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setToolTip("关闭 AI 助手")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._t("BTN_SUBTLE")};
                border: 1px solid {self._t("BTN_SUBTLE_BORDER")};
                border-radius: 6px;
                color: {self._t("TEXT_SUB")};
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {theme.bg_hover};
                color: {self._t("TEXT_MAIN")};
            }}
        """)
        self.close_btn.clicked.connect(self.close_requested.emit)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        # ── API key config area ─────────────────────────────────
        self.key_area = QFrame()
        self.key_area.setObjectName("KeyConfigArea")
        self._build_key_area()
        layout.addWidget(self.key_area)

        # ── chat view ───────────────────────────────────────────
        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(True)
        self.chat_view.setStyleSheet(f"""
            QTextBrowser {{
                background: {self._t("BG_CHAT")};
                border: 1px solid {self._t("BORDER")};
                border-radius: 10px;
                padding: 12px;
                color: {self._t("TEXT_MAIN")};
                font-size: 13px;
                selection-background-color: {self._t("ACCENT")};
                selection-color: {theme.bg_card};
            }}
            QScrollBar:vertical {{
                background: {self._t("BG_PANEL")};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self._t("BORDER")};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme.border};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        self._refresh_welcome()
        layout.addWidget(self.chat_view, 1)

        # ── input area ──────────────────────────────────────────
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入你的问题，例如：我现在离毕业要求还差什么？")
        self.input_edit.setMaximumHeight(80)
        self.input_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {self._t("BG_CHAT")};
                border: 1px solid {self._t("BORDER")};
                border-radius: 8px;
                padding: 10px;
                color: {self._t("TEXT_MAIN")};
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border-color: {self._t("ACCENT")};
                background: {theme.bg_card};
            }}
        """)
        layout.addWidget(self.input_edit)

        # ── bottom row (status + send) ──────────────────────────
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            f"font-size: 12px; color: {self._t("TEXT_SUB")}; font-style: italic;"
        )
        button_row.addWidget(self.status_label)
        button_row.addStretch()

        self.send_btn = QPushButton("发 送")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._t("ACCENT")};
                border: 1px solid {self._t("ACCENT_HOV")};
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 22px;
            }}
            QPushButton:hover {{
                background: {self._t("ACCENT_HOV")};
            }}
            QPushButton:disabled {{
                background: {theme.bg_badge};
                border-color: {theme.border};
                color: {theme.fg_faint};
            }}
        """)
        self.send_btn.clicked.connect(self._send)
        button_row.addWidget(self.send_btn)
        layout.addLayout(button_row)

    # ── API key config ──────────────────────────────────────────────

    def _build_key_area(self):
        """Build the compact API-key row inside key_area."""
        # clear any existing content
        for child in self.key_area.children():
            child.deleteLater()

        inner = QHBoxLayout(self.key_area)
        inner.setContentsMargins(10, 8, 10, 8)
        inner.setSpacing(8)

        if self._key_configured:
            # ── configured state: subtle indicator + change button ─
            self.key_area.setStyleSheet(f"""
                #KeyConfigArea {{
                    background: {self._t("AI_BUBBLE")};
                    border: 1px solid {self._t("ACCENT")};
                    border-radius: 6px;
                }}
            """)
            indicator = QLabel("🔑 API Key 已配置")
            indicator.setStyleSheet(
                f"font-size: 12px; color: {self._t("ACCENT")}; font-weight: bold;"
            )
            inner.addWidget(indicator)
            inner.addStretch()

            change_btn = QPushButton("更改")
            change_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            change_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {self._t("BORDER")};
                    border-radius: 4px;
                    color: {self._t("TEXT_SUB")};
                    font-size: 11px;
                    padding: 2px 12px;
                }}
                QPushButton:hover {{
                    background: {self._t("BTN_SUBTLE")};
                    color: {self._t("TEXT_MAIN")};
                }}
            """)
            change_btn.clicked.connect(self._show_key_input)
            inner.addWidget(change_btn)
        else:
            # ── unconfigured state: input + save ────────────────
            self.key_area.setStyleSheet(f"""
                #KeyConfigArea {{
                    background: {self._t("WARN_BG")};
                    border: 1px solid {self._t("WARN_BORDER")};
                    border-radius: 6px;
                }}
            """)

            label = QLabel("🔑 API Key")
            label.setStyleSheet(
                f"font-size: 12px; color: {self._t("TEXT_MAIN")}; font-weight: bold;"
            )
            inner.addWidget(label)

            self.key_input = QLineEdit()
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.key_input.setPlaceholderText("粘贴你的 DeepSeek API Key（sk-...）")
            self.key_input.setStyleSheet(f"""
                QLineEdit {{
                    background: {self._t("BG_CHAT")};
                    border: 1px solid {self._t("BORDER")};
                    border-radius: 4px;
                    padding: 4px 10px;
                    color: {self._t("TEXT_MAIN")};
                    font-size: 12px;
                }}
                QLineEdit:focus {{
                    border-color: {self._t("ACCENT")};
                }}
            """)
            self.key_input.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            inner.addWidget(self.key_input, 1)

            save_btn = QPushButton("保存")
            save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            save_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self._t("ACCENT")};
                    border: 1px solid {self._t("ACCENT_HOV")};
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 4px 14px;
                }}
                QPushButton:hover {{
                    background: {self._t("ACCENT_HOV")};
                }}
            """)
            save_btn.clicked.connect(self._save_key)
            inner.addWidget(save_btn)

    def _save_key(self):
        """Persist the key and refresh the UI."""
        key = self.key_input.text().strip()
        if not key:
            return
        save_api_key(key)
        self._key_configured = True
        self._build_key_area()
        self._refresh_welcome()

    def _show_key_input(self):
        """Switch the key area back to input mode so the user can change it."""
        self._key_configured = False
        self._build_key_area()

    # ── welcome / chat helpers ──────────────────────────────────────

    def _refresh_welcome(self):
        if self._key_configured:
            self.chat_view.setHtml(self._welcome_html())
        else:
            self.chat_view.setHtml(self._welcome_no_key_html())

    def _welcome_html(self) -> str:
        return (
            f"<div style='background:{self._t("AI_BUBBLE")}; border-radius:8px; "
            f"padding:14px 16px; margin:4px 0 12px 0;'>"
            f"<p style='color:{self._t("TEXT_MAIN")}; margin:0; line-height:1.7;'>"
            f"<b style='color:{self._t("ACCENT")};'>你好！👋</b><br>"
            f"我是你的个人发展规划顾问。你问什么我答什么——"
            f"学分、成绩、简历、实习、技能提升，直接说就好。"
            f"</p></div>"
            f"<table style='color:{self._t("TEXT_SUB")}; font-size:12px; margin:4px 0 0 2px; "
            f"border-spacing:0;'>"
            f"<tr><td style='padding:2px 8px 2px 0;'>📚</td>"
            f"<td style='padding:2px 0;'>我还差什么课才能毕业？</td></tr>"
            f"<tr><td style='padding:2px 8px 2px 0;'>📊</td>"
            f"<td style='padding:2px 0;'>我的 GPA 怎么样？哪些课拖了后腿？</td></tr>"
            f"<tr><td style='padding:2px 8px 2px 0;'>📝</td>"
            f"<td style='padding:2px 0;'>帮我看看简历怎么改更好？</td></tr>"
            f"<tr><td style='padding:2px 8px 2px 0;'>💼</td>"
            f"<td style='padding:2px 0;'>我的实习投递进度合理吗？</td></tr>"
            f"<tr><td style='padding:2px 8px 2px 0;'>🎯</td>"
            f"<td style='padding:2px 0;'>以我的背景，大四上学期该做什么？</td></tr>"
            f"</table>"
        )

    def _welcome_no_key_html(self) -> str:
        return (
            f"<div style='background:{self._t("WARN_BG")}; border:1px solid {self._t("WARN_BORDER")}; "
            f"border-radius:8px; padding:14px 16px; margin:4px 0 12px 0;'>"
            f"<p style='color:{self._t("TEXT_MAIN")}; margin:0; line-height:1.7;'>"
            f"<b>⚠️ 尚未配置 API Key</b><br>"
            f"请在上方输入你的 <b>DeepSeek API Key</b>（可在 "
            f"<a href='https://platform.deepseek.com/api_keys' "
            f"style='color:{self._t("ACCENT")};'>platform.deepseek.com</a> 获取），"
            f"然后点击「保存」即可开始使用。"
            f"</p></div>"
        )

    # ── send flow ──────────────────────────────────────────────────

    def _send(self):
        question = self.input_edit.toPlainText().strip()
        if not question or self.worker:
            return

        # refresh key state before each send (user may have changed it)
        self._key_configured = bool(get_api_key())
        if not self._key_configured:
            self._build_key_area()
            self._refresh_welcome()
            self.chat_view.append(
                f"<div style='background:{self._t("WARN_BG")}; border-radius:6px; "
                f"padding:8px 12px; margin:8px 0;'>"
                f"<span style=f'color:{theme.fg_muted}; font-size:12px;'>"
                f"请先配置 DeepSeek API Key 再发送问题。</span></div>"
            )
            return

        self.input_edit.clear()
        self._append_message("You", question)
        self.status_label.setText("思考中…")
        self.send_btn.setEnabled(False)

        self.worker = AiWorker(question, self)
        self.worker.finished.connect(self._on_answer)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _on_answer(self, answer: str):
        self._append_message("AI 助手", answer)
        self.status_label.setText("")
        self.send_btn.setEnabled(True)
        self.worker = None

    # ── message rendering ──────────────────────────────────────────

    def _append_message(self, speaker: str, text: str):
        if speaker == "AI 助手":
            bg = self._t("AI_BUBBLE")
            accent = self._t("ACCENT")
            body = render_markdown(text)
        else:
            bg = self._t("USER_BUBBLE")
            accent = self._t("TEXT_SUB")
            body = (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>")
            )

        self.chat_view.append(
            f"<div style='background:{bg}; border-radius:8px; "
            f"padding:10px 14px; margin:8px 0; line-height:1.55;'>"
            f"<b style='color:{accent}'>{speaker}：</b>"
            f"<span style='color:{self._t("TEXT_MAIN")}'>{body}</span></div>"
        )
