"""Main window — sidebar, content stack, AI panel, floating pet."""

import os
import sys

from PySide6.QtCore import QEasingCurve, QVariantAnimation, Qt


def _resource_path(*segments: str) -> str:
    """Resolve a resource path that works both from source and from a
    PyInstaller ``--onefile`` bundle.

    In a PyInstaller bundle the tree of ``--add-data`` files is extracted
    into :data:`sys._MEIPASS`, not next to the .exe.  So we look there
    first; if the path does not exist we fall back to a CWD-relative path
    (normal development mode).
    """
    if getattr(sys, "frozen", False):
        # Running inside a PyInstaller bundle
        bundled = os.path.join(sys._MEIPASS, *segments)
        if os.path.exists(bundled):
            return bundled
    return os.path.join(*segments)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..database.migrations import init_database
from ..utils.constants import APP_NAME, APP_VERSION
from .achievement_view import AchievementView
from .ai_assistant_panel import AiAssistantPanel
from .coding_practice_view import CodingPracticeView
from .course_view import CourseView
from .dashboard_view import DashboardView
from .experience_view import ExperienceView
from .gpa_view import GpaView
from .graduate_view import GraduateView
from .internship_view import InternshipView
from .resume_view import ResumeView
from .settings_view import SettingsView
from .widgets.assistant_pet_widget import AssistantPetWidget

# ═══════════════════════════════════════════════════════════════════════
#  Layout constants
# ═══════════════════════════════════════════════════════════════════════
SIDEBAR_FULL  = 220   # expanded sidebar
SIDEBAR_THIN  = 36    # collapsed sidebar
PANEL_WIDTH   = 360
PANEL_MIN     = 260
PANEL_MAX     = 600
PET_MARGIN    = 18

# ═══════════════════════════════════════════════════════════════════════
#  Page registry
# ═══════════════════════════════════════════════════════════════════════
PAGES = [
    ("dashboard",    "情况总览",   DashboardView),
    ("courses",      "课程管理",   CourseView),
    ("experiences",  "经历管理",   ExperienceView),
    ("internship",   "实习追踪",   InternshipView),
    ("achievements", "荣誉奖项",   AchievementView),
    ("gpa",          "成绩分析",   GpaView),
    ("resume",       "简历工作台", ResumeView),
]

OTHER_FEATURES = [
    ("coding_practice", "面试备战", CodingPracticeView),
    ("graduate",       "升学规划", GraduateView),
]

SETTINGS_KEY   = "settings"
SETTINGS_LABEL = "个人设置"


# ═══════════════════════════════════════════════════════════════════════
#  NavButton
# ═══════════════════════════════════════════════════════════════════════

class NavButton(QPushButton):
    """Sidebar navigation button — fitness dark sidebar style."""

    def __init__(self, text: str, indent: bool = False, parent=None):
        super().__init__(text, parent)
        self._indent = indent
        self.setCheckable(True)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(42)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        pad_left = 28 if self._indent else 14
        # use theme palette directly for dark sidebar
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 8px 14px 8px {pad_left}px;
                border: none;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 500;
                color: #9898a8;
                background: transparent;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.06);
                color: #e0e0e8;
            }}
            QPushButton:checked {{
                background: rgba(245,158,11,0.15);
                color: #fbbf24;
                font-weight: 700;
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════
#  MainWindow
# ═══════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)

        # animation refs (prevent GC)
        self._panel_anim: QVariantAnimation | None = None
        self._pet_anim: QVariantAnimation | None = None
        self._sidebar_anim: QVariantAnimation | None = None
        self._sidebar_collapsed = False

        self.nav_buttons   = {}
        self.other_buttons = {}
        self._page_views   = {}
        self._page_index: dict[str, int] = {}
        self._sidebar_widgets: list[QWidget] = []  # widgets to hide when collapsed

        init_database()
        self._setup_ui()
        self._connect_signals()

    # ─────────────────────────────────────────────────────────────────
    #  UI construction
    # ─────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._build_sidebar(root)
        self._build_content(root)

        self._navigate("dashboard")
        self._setup_pet()

    # ── sidebar ────────────────────────────────────────────────────

    def _build_sidebar(self, root: QHBoxLayout):
        sb = QFrame()
        sb.setObjectName("SidebarFrame")
        sb.setFixedWidth(SIDEBAR_FULL)
        sb.setStyleSheet(
            "QFrame#SidebarFrame { background: #1c1c24; "
            "border-right: 1px solid rgba(255,255,255,0.06); }"
        )
        self._sidebar = sb
        self._sidebar_layout = QVBoxLayout(sb)
        self._sidebar_layout.setContentsMargins(12, 16, 12, 16)
        self._sidebar_layout.setSpacing(4)

        # header row: logo  +  collapse toggle
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)

        self._logo = QLabel("PDP<span style='color:#f59e0b;'>Tool</span>")
        self._logo.setTextFormat(Qt.TextFormat.RichText)
        self._logo.setObjectName("SidebarLogo")
        self._logo.setStyleSheet(
            "font-size: 18px; font-weight: 800; padding: 8px 8px 16px 8px;"
            "color: #ffffff; letter-spacing: -0.5px;"
        )
        hdr.addWidget(self._logo)
        hdr.addStretch()

        self._collapse_btn = QPushButton("☰")
        self._collapse_btn.setFixedSize(32, 32)
        self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_btn.setToolTip("折叠侧边栏")
        self._collapse_btn.setStyleSheet(
            "QPushButton { font-size: 16px; color: #787886; "
            "border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; "
            "background: transparent; }"
            "QPushButton:hover { color: #fbbf24; background: rgba(255,255,255,0.06); "
            "border-color: rgba(245,158,11,0.3); }"
        )
        self._collapse_btn.clicked.connect(self._toggle_sidebar)
        hdr.addWidget(self._collapse_btn)
        self._sidebar_layout.addLayout(hdr)

        # primary nav buttons
        for key, label, _ in PAGES:
            btn = NavButton(label)
            self.nav_buttons[key] = btn
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            self._sidebar_layout.addWidget(btn)
            self._sidebar_widgets.append(btn)

        # ── "其他功能" section ──────────────────────────────────
        if OTHER_FEATURES:
            self._sidebar_layout.addSpacing(8)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFixedHeight(1)
            self._sidebar_layout.addWidget(sep)
            self._sidebar_widgets.append(sep)  # type: ignore[attr-defined]

            self._other_header = QPushButton("▼  其他功能")
            self._other_header.setFlat(True)
            self._other_header.setCursor(Qt.CursorShape.PointingHandCursor)
            self._other_header.setStyleSheet(
                "QPushButton { text-align: left; padding: 6px 16px 4px 16px; "
                "border: none; font-size: 10px; font-weight: 600; "
                "color: rgba(255,255,255,0.25); background: transparent;"
                "text-transform: uppercase; letter-spacing: 0.5px; }"
                "QPushButton:hover { color: rgba(255,255,255,0.45); }"
            )
            self._other_header.clicked.connect(self._toggle_other_section)
            self._sidebar_layout.addWidget(self._other_header)
            self._sidebar_widgets.append(self._other_header)  # type: ignore[attr-defined]

            self._other_items = QWidget()
            ol = QVBoxLayout(self._other_items)
            ol.setContentsMargins(0, 0, 0, 4)
            ol.setSpacing(2)
            for key, label, _ in OTHER_FEATURES:
                btn = NavButton(label, indent=True)
                self.other_buttons[key] = btn
                btn.clicked.connect(lambda _, k=key: self._navigate(k))
                ol.addWidget(btn)
            self._sidebar_layout.addWidget(self._other_items)
            self._sidebar_widgets.append(self._other_items)  # type: ignore[attr-defined]

        self._sidebar_layout.addStretch()

        # settings
        self._settings_btn = NavButton(SETTINGS_LABEL)
        self._settings_btn.clicked.connect(lambda: self._navigate(SETTINGS_KEY))
        self._sidebar_layout.addWidget(self._settings_btn)
        self._sidebar_widgets.append(self._settings_btn)  # type: ignore[attr-defined]

        # version
        ver = QLabel(f"v{APP_VERSION}")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: rgba(255,255,255,0.15); font-size: 10px;")
        self._sidebar_layout.addWidget(ver)
        self._sidebar_widgets.append(ver)  # type: ignore[attr-defined]

        root.addWidget(sb)

    # ── content area ───────────────────────────────────────────────

    def _build_content(self, root: QHBoxLayout):
        self._stack = QStackedWidget()

        for idx, (key, _, view_cls) in enumerate(PAGES):
            v = view_cls()
            self._page_views[key] = v
            self._page_index[key] = idx
            self._stack.addWidget(v)

        other_start = len(PAGES)
        for i, (key, _, view_cls) in enumerate(OTHER_FEATURES):
            v = view_cls()
            self._page_views[key] = v
            self._page_index[key] = other_start + i
            self._stack.addWidget(v)

        self._settings_view = SettingsView()
        si = len(PAGES) + len(OTHER_FEATURES)
        self._page_views[SETTINGS_KEY] = self._settings_view
        self._page_index[SETTINGS_KEY] = si
        self._stack.addWidget(self._settings_view)

        # AI panel wrapper
        self._ai_panel = AiAssistantPanel()
        self._ai_panel.close_requested.connect(self._hide_ai_assistant)

        self._ai_wrapper = QWidget()
        self._ai_wrapper.setObjectName("AiPanelWrapper")
        self._ai_wrapper.setMinimumWidth(0)
        self._ai_wrapper.setMaximumWidth(PANEL_MAX)
        self._ai_wrapper.setStyleSheet(
            "#AiPanelWrapper { background: #faf7f2; "
            "border-left: 1px solid #e8e2d8; }"
        )
        wl = QVBoxLayout(self._ai_wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(self._ai_panel)
        self._ai_wrapper.hide()

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(6)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setStyleSheet(
            "QSplitter::handle { background: #e8e2d8; width: 6px; }"
            "QSplitter::handle:hover { background: #f59e0b; }"
            "QSplitter::handle:pressed { background: #d97706; }"
        )
        self._splitter.addWidget(self._stack)
        self._splitter.addWidget(self._ai_wrapper)
        self._splitter.setSizes([1000, 0])

        root.addWidget(self._splitter, 1)

    # ── signals ────────────────────────────────────────────────────

    def _connect_signals(self):
        cv = self._page_views.get("courses")
        ev = self._page_views.get("experiences")
        av = self._page_views.get("achievements")
        iv = self._page_views.get("internship")
        gv = self._page_views.get("gpa")
        dv = self._page_views.get("dashboard")
        rv = self._page_views.get("resume")

        if cv:
            cv.data_changed.connect(gv.refresh)
            cv.data_changed.connect(dv.refresh)
            cv.data_changed.connect(rv.refresh)
        if ev:
            ev.data_changed.connect(dv.refresh)
            ev.data_changed.connect(rv.refresh)
        if av:
            av.data_changed.connect(dv.refresh)
            av.data_changed.connect(rv.refresh)
        if iv:
            iv.data_changed.connect(dv.refresh)
            iv.data_changed.connect(rv.refresh)

        grad_v = self._page_views.get("graduate")
        if grad_v:
            grad_v.data_changed.connect(dv.refresh)

    # ── navigation ─────────────────────────────────────────────────

    def _navigate(self, key: str):
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        for k, btn in self.other_buttons.items():
            btn.setChecked(k == key)
        self._settings_btn.setChecked(key == SETTINGS_KEY)

        idx = self._page_index.get(key, 0)
        self._stack.setCurrentIndex(idx)
        page = self._stack.currentWidget()
        if hasattr(page, "refresh"):
            page.refresh()

    # ── sidebar collapse ───────────────────────────────────────────

    def _toggle_sidebar(self):
        if self._sidebar_collapsed:
            self._expand_sidebar()
        else:
            self._collapse_sidebar()

    def _collapse_sidebar(self):
        self._logo.hide()
        for w in self._sidebar_widgets:
            w.setVisible(False)
        self._sidebar_layout.setContentsMargins(4, 16, 6, 16)
        self._collapse_btn.setText("☰")
        self._collapse_btn.setFixedSize(28, 32)
        self._collapse_btn.setToolTip("展开侧边栏")
        self._animate_sidebar(SIDEBAR_FULL, SIDEBAR_THIN)
        self._sidebar_collapsed = True

    def _expand_sidebar(self):
        self._animate_sidebar(SIDEBAR_THIN, SIDEBAR_FULL)
        self._sidebar_collapsed = False
        self._sidebar_layout.setContentsMargins(12, 16, 12, 16)
        self._logo.show()
        for w in self._sidebar_widgets:
            w.setVisible(True)
        self._collapse_btn.setFixedSize(32, 32)
        self._collapse_btn.setText("☰")
        self._collapse_btn.setToolTip("折叠侧边栏")

    def _animate_sidebar(self, fr: int, to: int):
        anim = QVariantAnimation(self)
        anim.setDuration(180)
        anim.setStartValue(fr)
        anim.setEndValue(to)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(lambda v: self._sidebar.setFixedWidth(int(v)))
        anim.start()
        self._sidebar_anim = anim

    # ── other-features toggle ──────────────────────────────────────

    def _toggle_other_section(self):
        visible = self._other_items.isVisible()
        self._other_items.setVisible(not visible)
        arrow = "▶" if visible else "▼"
        self._other_header.setText(f"{arrow}  其他功能")

    # ── pet ────────────────────────────────────────────────────────

    def _setup_pet(self):
        path = _resource_path("assets", "assistant", "raiden_idle_clean.png")
        self._pet = AssistantPetWidget(path, self)
        self._pet.clicked.connect(self._toggle_ai_assistant)
        self._pet.hovered_changed.connect(self._on_pet_hovered)
        self._pet.raise_()
        self._pet_peeking = True
        self._position_pet_peek()

    def _panel_visible_w(self) -> int:
        if self._ai_wrapper.isVisible():
            return max(self._ai_wrapper.width(), PANEL_MIN)
        return 0

    def _pet_peek_x(self) -> int:
        return self.width() - int(self._pet.width() * 0.28)

    def _pet_visible_x(self) -> int:
        return self.width() - self._pet.width() - PET_MARGIN

    def _pet_panel_x(self) -> int:
        return self.width() - self._pet.width() - PET_MARGIN - self._panel_visible_w()

    def _pet_y(self) -> int:
        return self.height() - self._pet.height() - PET_MARGIN

    def _position_pet_peek(self):
        self._pet.move(self._pet_peek_x(), self._pet_y())
        self._pet.raise_()
        self._pet_peeking = True

    def _position_pet_visible(self):
        self._pet.move(self._pet_visible_x(), self._pet_y())
        self._pet.raise_()
        self._pet_peeking = False

    def _position_pet_panel(self):
        self._pet.move(self._pet_panel_x(), self._pet_y())
        self._pet.raise_()
        self._pet_peeking = False

    def _animate_pet_x(self, target: int):
        cur = self._pet.x()
        if cur == target:
            return
        anim = QVariantAnimation(self)
        anim.setDuration(220)
        anim.setStartValue(cur)
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(lambda v: self._pet.move(v, self._pet.y()))
        anim.valueChanged.connect(lambda _: self._pet.raise_())
        anim.start()
        self._pet_anim = anim

    def _on_pet_hovered(self, hovering: bool):
        if self._ai_wrapper.isVisible():
            return
        if hovering:
            self._pet_peeking = False
            self._animate_pet_x(self._pet_visible_x())
        else:
            self._pet_peeking = True
            self._animate_pet_x(self._pet_peek_x())

    # ── AI panel ───────────────────────────────────────────────────

    def _toggle_ai_assistant(self):
        if self._ai_wrapper.isVisible():
            self._hide_ai_assistant()
        else:
            self._show_ai_assistant()

    def _show_ai_assistant(self):
        self._ai_wrapper.setMinimumWidth(PANEL_MIN)
        self._ai_wrapper.show()
        self._animate_splitter(PANEL_WIDTH)
        self._animate_pet_x(self._pet_panel_x())

    def _hide_ai_assistant(self):
        if not self._ai_wrapper.isVisible():
            return
        self._animate_splitter(0, on_finish=lambda: (
            self._ai_wrapper.setMinimumWidth(0),
            self._ai_wrapper.hide(),
        ))
        self._animate_pet_x(self._pet_peek_x())

    def _animate_splitter(self, target_panel: int, on_finish=None):
        total = self._splitter.width()
        cur = self._ai_wrapper.width() if self._ai_wrapper.isVisible() else 0
        handle = self._splitter.handleWidth()

        anim = QVariantAnimation(self)
        anim.setDuration(220)
        anim.setStartValue(cur)
        anim.setEndValue(target_panel)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _upd(pw: float):
            self._splitter.setSizes([total - int(pw) - handle, int(pw)])

        anim.valueChanged.connect(_upd)
        if on_finish:
            anim.finished.connect(lambda: on_finish())
        anim.start()
        self._panel_anim = anim

    # ── resize ─────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "_pet"):
            return

        base = max(110, min(150, int(self.centralWidget().width() * 0.11)))
        if self._pet.base_width != base:
            self._pet.update_size(base)

        if self._ai_wrapper.isVisible():
            self._position_pet_panel()
        elif self._pet_peeking:
            self._position_pet_peek()
        else:
            self._position_pet_visible()
