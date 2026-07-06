"""Fitness Dashboard theme for PDPTool — neumorphism + warm tones.

Usage::

    from src.utils.theme import theme

    bg = theme.bg               # "#f5f0e8"
    accent = theme.primary      # "#f59e0b"

    # QSS snippets — dynamic (call them, don't store as strings)
    btn.setStyleSheet(theme.primary_btn_style())
    table.setStyleSheet(theme.table_style())
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════
#  Palette — warm beige fitness / neumorphism
# ═══════════════════════════════════════════════════════════════════════

_PALETTE = {
    # ── Background ─────────────────────────────────
    "bg":            "#f5f0e8",
    "bg_sidebar":    "#1c1c24",
    "bg_card":       "#ffffff",
    "bg_glass":      "rgba(255,255,255,0.65)",
    "bg_input":      "#fafaf9",
    "bg_hover":      "#ede8e0",
    "bg_active":     "#fef3c7",
    "bg_code":       "#faf8f5",
    "bg_badge":      "#f0ebe2",
    "bg_alt_row":    "#faf7f2",

    # ── Foreground / Text ────────────────────────
    "fg":            "#1c1c24",
    "fg_muted":      "#8b8b9e",
    "fg_faint":      "#b0b0bb",
    "fg_accent":     "#d97706",
    "fg_sidebar":    "#9898a8",
    "fg_sidebar_active": "#fbbf24",

    # ── Borders ──────────────────────────────────
    "border":        "#e8e2d8",
    "border_input":  "#d9cfc1",
    "border_focus":  "#f59e0b",

    # ── Primary / Accent ────────────────────────
    "primary":       "#f59e0b",
    "primary_light": "#fbbf24",
    "primary_dark":  "#d97706",
    "primary_glow":  "#fef3c7",

    # ── Semantic ─────────────────────────────────
    "green":         "#10b981",
    "green_light":   "#d1fae5",
    "orange":        "#f97316",
    "orange_light":  "#ffedd5",
    "purple":        "#8b5cf6",
    "purple_light":  "#ede9fe",
    "coral":         "#f87171",
    "coral_light":   "#fef2f2",
    "blue":          "#3b82f6",
    "blue_light":    "#dbeafe",
    "gold":          "#d97706",

    # ── Chat bubbles ─────────────────────────────
    "ai_bubble":     "#f0f4ff",
    "user_bubble":   "#fffdf5",
    "warn_bg":       "#fffdf5",
    "warn_border":   "#fde68a",

    # ── Code / Diff ──────────────────────────────
    "diff_easy":     "#10b981",
    "diff_medium":   "#f59e0b",
    "diff_hard":     "#ef4444",

    # ── Nav / Sidebar ────────────────────────────
    "nav_bg":        "#1c1c24",
    "nav_hover_bg":  "rgba(255,255,255,0.06)",
    "nav_active_bg": "rgba(245,158,11,0.15)",
    "nav_fg":        "#787886",
    "nav_fg_active": "#fbbf24",

    # ── Backward-compatible aliases ─────────────
    "accent":        "#f59e0b",      # → primary
    "accent_hover":  "#d97706",      # → primary_dark
}


# ═══════════════════════════════════════════════════════════════════════
#  Radius constants
# ═══════════════════════════════════════════════════════════════════════

_RADIUS = {
    "sm":  "10px",
    "md":  "14px",
    "lg":  "20px",
    "xl":  "24px",
    "pill": "50px",
}


# ═══════════════════════════════════════════════════════════════════════
#  Theme namespace
# ═══════════════════════════════════════════════════════════════════════

class _Theme:
    """Attribute access → palette value.  ``theme.bg`` → ``"#f5f0e8"``."""

    def __getattr__(self, name: str) -> str:
        if name in _PALETTE:
            return _PALETTE[name]
        raise AttributeError(f"Theme has no key {name!r}")

    @property
    def radius_sm(self) -> str:
        return _RADIUS["sm"]

    @property
    def radius_md(self) -> str:
        return _RADIUS["md"]

    @property
    def radius_lg(self) -> str:
        return _RADIUS["lg"]

    @property
    def radius_xl(self) -> str:
        return _RADIUS["xl"]

    @property
    def radius_pill(self) -> str:
        return _RADIUS["pill"]

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def diff_color(label: str) -> str:
        return {
            "简单": _PALETTE["diff_easy"],
            "中等": _PALETTE["diff_medium"],
            "困难": _PALETTE["diff_hard"],
        }.get(label, _PALETTE["fg_muted"])

    # ── global QSS ──────────────────────────────────────────────────

    @staticmethod
    def stylesheet() -> str:
        p = _PALETTE
        r = _RADIUS
        return f"""\
* {{ font-family: "Inter", "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif; }}
QMainWindow {{ background: {p['bg']}; }}
QWidget {{ color: {p['fg']}; }}
QTableWidget {{
    background: {p['bg_card']}; color: {p['fg']};
    gridline-color: {p['border']};
    alternate-background-color: {p['bg_alt_row']};
    border: 1px solid {p['border']};
    border-radius: {r['md']};
}}
QTableWidget::item:selected {{ background: {p['bg_active']}; color: {p['fg']}; }}
QHeaderView::section {{
    background: {p['bg_alt_row']}; color: {p['fg_muted']};
    padding: 8px 10px; font-weight: 600; border: none;
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
}}
QComboBox {{
    padding: 8px 12px; border: 1px solid {p['border']};
    border-radius: {r['sm']}; background: {p['bg_input']}; color: {p['fg']};
    font-size: 13px;
}}
QComboBox:disabled {{ color: {p['fg_faint']}; }}
QComboBox QAbstractItemView {{
    background: {p['bg_input']}; color: {p['fg']};
    selection-background-color: {p['bg_active']};
}}
QLineEdit {{
    padding: 8px 12px; border: 1px solid {p['border']};
    border-radius: {r['sm']}; background: {p['bg_input']}; color: {p['fg']};
    font-size: 13px;
}}
QLineEdit:focus {{ border-color: {p['border_focus']}; }}
QTextEdit, QPlainTextEdit, QTextBrowser {{
    border: 1px solid {p['border']}; border-radius: {r['sm']};
    background: {p['bg_input']}; color: {p['fg']};
}}
QTextEdit:focus, QPlainTextEdit:focus {{ border-color: {p['border_focus']}; }}
QPushButton {{
    padding: 8px 16px; border: 1px solid {p['border']};
    border-radius: {r['pill']}; background: {p['bg_input']}; color: {p['fg']};
    font-size: 13px; font-weight: 600;
}}
QPushButton:hover {{ background: {p['bg_hover']}; }}
QPushButton:disabled {{ color: {p['fg_faint']}; background: {p['bg_alt_row']}; }}
QGroupBox {{
    font-weight: bold; border: 1px solid {p['border']};
    border-radius: {r['md']}; margin-top: 12px; padding-top: 18px; color: {p['fg']};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 8px; }}
QSplitter::handle {{ background: {p['border']}; }}
QSplitter::handle:hover {{ background: {p['primary']}; }}
QSplitter::handle:pressed {{ background: {p['primary_dark']}; }}
QLabel {{ color: {p['fg']}; }}
QScrollBar:vertical {{
    background: transparent; width: 6px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(0,0,0,0.08); border-radius: 3px; min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{ background: rgba(0,0,0,0.15); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QProgressBar {{
    border: none; border-radius: {r['pill']}; background: rgba(0,0,0,0.05);
    text-align: center; font-size: 11px; color: {p['fg']}; height: 10px;
}}
QProgressBar::chunk {{
    border-radius: {r['pill']};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {p['primary']}, stop:1 {p['primary_light']});
}}
"""

    # ── QSS snippets ────────────────────────────────────────────────

    @staticmethod
    def primary_btn_style() -> str:
        p = _PALETTE
        r = _RADIUS
        return (
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"    stop:0 {p['primary']}, stop:1 {p['primary_dark']});"
            f"  color: white; padding: 10px 22px;"
            f"  border-radius: {r['pill']}; border: none;"
            f"  font-weight: 700; font-size: 13px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"    stop:0 {p['primary_light']}, stop:1 {p['primary']});"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background: {p['bg_badge']};"
            f"  color: {p['fg_faint']};"
            f"}}"
        )

    @staticmethod
    def danger_btn_style() -> str:
        p = _PALETTE
        r = _RADIUS
        return (
            f"QPushButton {{"
            f"  color: {p['coral']}; border: 1px solid {p['border']};"
            f"  border-radius: {r['pill']}; padding: 6px 14px;"
            f"  background: transparent; font-size: 12px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {p['coral_light']}; border-color: {p['coral']};"
            f"}}"
        )

    @staticmethod
    def subtle_btn_style() -> str:
        p = _PALETTE
        r = _RADIUS
        return (
            f"QPushButton {{"
            f"  background: transparent; border: 1px solid {p['border']};"
            f"  border-radius: {r['pill']}; color: {p['fg_muted']};"
            f"  padding: 8px 18px; font-size: 13px; font-weight: 500;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {p['bg_active']}; color: {p['primary_dark']};"
            f"  border-color: {p['primary']};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background: transparent; color: {p['fg_faint']};"
            f"  border-color: {p['border']};"
            f"}}"
        )

    @staticmethod
    def table_style() -> str:
        p = _PALETTE
        r = _RADIUS
        return (
            f"QTableWidget {{"
            f"  background-color: {p['bg_card']};"
            f"  color: {p['fg']}; gridline-color: {p['border']};"
            f"  border: 1px solid {p['border']};"
            f"  border-radius: {r['md']};"
            f"}}"
            f"QHeaderView::section {{"
            f"  background-color: {p['bg_alt_row']};"
            f"  color: {p['fg_muted']}; padding: 8px 10px;"
            f"  border: none; font-size: 11px;"
            f"  text-transform: uppercase; letter-spacing: 0.5px;"
            f"}}"
            f"QTableWidget::item:selected {{"
            f"  background-color: {p['bg_active']}; color: {p['fg']};"
            f"}}"
        )

    @staticmethod
    def warning_infobar_style() -> str:
        p = _PALETTE
        r = _RADIUS
        return (
            f"color: {p['fg_muted']}; background: {p['warn_bg']}; "
            f"border: 1px solid {p['warn_border']}; border-radius: {r['md']}; "
            f"padding: 12px 16px; font-size: 13px;"
        )

    @staticmethod
    def tab_widget_style() -> str:
        p = _PALETTE
        r = _RADIUS
        return (
            f"QTabWidget::pane {{"
            f"  border: 1px solid {p['border']};"
            f"  border-radius: {r['sm']}; background: {p['bg_card']};"
            f"}}"
            f"QTabBar::tab {{"
            f"  padding: 8px 20px;"
            f"  border: 1px solid transparent; border-bottom: none;"
            f"  border-radius: {r['sm']} {r['sm']} 0 0;"
            f"  background: transparent;"
            f"  color: {p['fg_muted']}; font-size: 13px;"
            f"  font-weight: 500; margin-right: 2px;"
            f"}}"
            f"QTabBar::tab:selected {{"
            f"  background: {p['bg_card']};"
            f"  color: {p['fg']}; font-weight: 700;"
            f"  border-color: {p['border']};"
            f"}}"
            f"QTabBar::tab:hover {{ color: {p['primary_dark']}; }}"
        )

    @staticmethod
    def card_stylesheet(accent=None, hovered: bool = False) -> str:
        p = _PALETTE
        r = _RADIUS
        if hovered and accent:
            return (
                f"background-color: {p['bg_card']};"
                f"border: 2px solid {accent};"
                f"border-radius: {r['lg']};"
            )
        bg = p["bg_hover"] if hovered else p["bg_card"]
        bd = accent if accent else p["border"]
        return (
            f"background-color: {bg};"
            f"border: 1px solid {bd};"
            f"border-radius: {r['lg']};"
        )

    @staticmethod
    def splitter_style() -> str:
        p = _PALETTE
        return (
            f"QSplitter::handle {{ background: {p['border']}; width: 6px; }}"
            f"QSplitter::handle:hover {{ background: {p['primary']}; }}"
            f"QSplitter::handle:pressed {{ background: {p['primary_dark']}; }}"
        )

    @staticmethod
    def section_title_style(font_size: int = 22) -> str:
        return (
            f"font-size:{font_size}px; font-weight:800;"
            f"color:{_PALETTE['fg']}; letter-spacing:-0.5px;"
        )


theme = _Theme()
