"""VS Code Light+ inspired colour palette for PDPTool.

Usage::

    from src.utils.theme import theme

    bg = theme.bg               # "#ffffff"
    accent = theme.accent       # "#007acc"

    # QSS snippets – dynamic (call them, don't store as strings)
    btn.setStyleSheet(theme.primary_btn_style())
    table.setStyleSheet(theme.table_style())
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════
#  Palette  (VS Code Light+)
# ═══════════════════════════════════════════════════════════════════════

_PALETTE = {
    "bg":            "#ffffff",
    "bg_sidebar":    "#f3f3f3",
    "bg_card":       "#ffffff",
    "bg_input":      "#ffffff",
    "bg_hover":      "#e8e8e8",
    "bg_active":     "#d6ebff",
    "bg_code":       "#fafafa",
    "bg_badge":      "#e4e4e4",
    "bg_alt_row":    "#faf6ef",

    "fg":            "#1f1f1f",
    "fg_muted":      "#616161",
    "fg_faint":      "#9e9e9e",
    "fg_accent":     "#005fb8",

    "border":        "#e0e0e0",
    "border_input":  "#d9cfc1",
    "border_focus":  "#007acc",

    "accent":        "#007acc",
    "accent_hover":  "#0062a3",

    "green":         "#388a34",
    "orange":        "#d18616",
    "purple":        "#8250df",
    "gold":          "#b08800",

    "ai_bubble":     "#f0f6ff",
    "user_bubble":   "#fff8ec",
    "warn_bg":       "#fff7e8",
    "warn_border":   "#ead7ad",

    "diff_easy":     "#388a34",
    "diff_medium":   "#d18616",
    "diff_hard":     "#cd3131",

    "nav_bg":        "#f3f3f3",
    "nav_hover_bg":  "#e8e8e8",
    "nav_active_bg": "#d6ebff",
    "nav_fg":        "#5b6470",
    "nav_fg_active": "#33423d",
}


# ═══════════════════════════════════════════════════════════════════════
#  Theme namespace
# ═══════════════════════════════════════════════════════════════════════

class _Theme:
    """Attribute access → palette value.  ``theme.bg`` → ``"#ffffff"``."""

    def __getattr__(self, name: str) -> str:
        if name in _PALETTE:
            return _PALETTE[name]
        raise AttributeError(f"Theme has no key {name!r}")

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
        return f"""\
* {{ font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif; }}
QMainWindow {{ background: {p['bg']}; }}
QWidget {{ color: {p['fg']}; }}
QTableWidget {{
    background: {p['bg_card']}; color: {p['fg']};
    gridline-color: {p['border']};
    alternate-background-color: {p['bg_sidebar']};
}}
QTableWidget::item:selected {{ background: {p['bg_active']}; color: {p['fg']}; }}
QHeaderView::section {{
    background: {p['bg_sidebar']}; color: {p['fg']};
    padding: 6px; font-weight: bold; border: 1px solid {p['border']};
}}
QComboBox {{
    padding: 4px 8px; border: 1px solid {p['border']};
    border-radius: 4px; background: {p['bg_input']}; color: {p['fg']};
}}
QComboBox:disabled {{ color: {p['fg_faint']}; }}
QComboBox QAbstractItemView {{
    background: {p['bg_input']}; color: {p['fg']};
    selection-background-color: {p['bg_active']};
}}
QLineEdit {{
    padding: 6px 8px; border: 1px solid {p['border']};
    border-radius: 4px; background: {p['bg_input']}; color: {p['fg']};
}}
QLineEdit:focus {{ border-color: {p['border_focus']}; }}
QTextEdit, QPlainTextEdit, QTextBrowser {{
    border: 1px solid {p['border']}; border-radius: 4px;
    background: {p['bg_input']}; color: {p['fg']};
}}
QTextEdit:focus, QPlainTextEdit:focus {{ border-color: {p['border_focus']}; }}
QPushButton {{
    padding: 6px 14px; border: 1px solid {p['border']};
    border-radius: 4px; background: {p['bg_input']}; color: {p['fg']};
}}
QPushButton:hover {{ background: {p['bg_hover']}; }}
QPushButton:disabled {{ color: {p['fg_faint']}; background: {p['bg_sidebar']}; }}
QGroupBox {{
    font-weight: bold; border: 1px solid {p['border']};
    border-radius: 6px; margin-top: 10px; padding-top: 16px; color: {p['fg']};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
QSplitter::handle {{ background: {p['border']}; }}
QSplitter::handle:hover {{ background: {p['accent']}; }}
QSplitter::handle:pressed {{ background: {p['accent_hover']}; }}
QLabel {{ color: {p['fg']}; }}
"""

    # ── QSS snippets ────────────────────────────────────────────────

    @staticmethod
    def primary_btn_style() -> str:
        p = _PALETTE
        return (
            f"QPushButton {{ background: {p['accent']}; color: white; "
            f"padding: 8px 18px; border-radius: 4px; "
            f"border: 1px solid {p['accent_hover']}; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {p['accent_hover']}; }}"
            f"QPushButton:disabled {{ background: {p['bg_badge']}; "
            f"border-color: {p['border']}; color: {p['fg_faint']}; }}"
        )

    @staticmethod
    def danger_btn_style() -> str:
        p = _PALETTE
        return (
            f"QPushButton {{ color: {p['orange']}; "
            f"border: 1px solid {p['border']}; border-radius: 4px; "
            f"padding: 4px 12px; }}"
            f"QPushButton:hover {{ background: {p['bg_hover']}; "
            f"color: #cd3131; border-color: {p['orange']}; }}"
        )

    @staticmethod
    def subtle_btn_style() -> str:
        p = _PALETTE
        return (
            f"QPushButton {{ background: {p['bg_sidebar']}; "
            f"border: 1px solid {p['border']}; border-radius: 4px; "
            f"color: {p['fg']}; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background: {p['bg_hover']}; "
            f"border-color: {p['accent']}; }}"
            f"QPushButton:disabled {{ background: {p['bg_sidebar']}; "
            f"color: {p['fg_faint']}; border-color: {p['border']}; }}"
        )

    @staticmethod
    def table_style() -> str:
        p = _PALETTE
        return (
            f"QTableWidget {{ background-color: {p['bg_card']}; "
            f"color: {p['fg']}; gridline-color: {p['border']}; "
            f"border: 1px solid {p['border']}; border-radius: 8px; }}"
            f"QHeaderView::section {{ background-color: {p['bg_sidebar']}; "
            f"color: {p['fg']}; padding: 7px; border: none; }}"
            f"QTableWidget::item:selected {{ "
            f"background-color: {p['bg_active']}; color: {p['fg']}; }}"
        )

    @staticmethod
    def warning_infobar_style() -> str:
        p = _PALETTE
        return (
            f"color: {p['fg_muted']}; background: {p['warn_bg']}; "
            f"border: 1px solid {p['warn_border']}; border-radius: 8px; "
            f"padding: 10px 12px; font-size: 13px;"
        )

    @staticmethod
    def tab_widget_style() -> str:
        p = _PALETTE
        return (
            f"QTabWidget::pane {{ border: 1px solid {p['border']}; "
            f"border-radius: 4px; background: {p['bg_card']}; }}"
            f"QTabBar::tab {{ padding: 6px 18px; "
            f"border: 1px solid {p['border']}; border-bottom: none; "
            f"border-radius: 4px 4px 0 0; background: {p['bg_sidebar']}; "
            f"color: {p['fg_muted']}; font-size: 13px; }}"
            f"QTabBar::tab:selected {{ background: {p['bg_card']}; "
            f"color: {p['fg']}; font-weight: bold; }}"
        )

    @staticmethod
    def card_stylesheet(accent=None, hovered: bool = False) -> str:
        p = _PALETTE
        bg = p["bg_hover"] if hovered else p["bg_card"]
        bd = accent if hovered and accent else p["border"]
        return f"background-color: {bg}; border: 1px solid {bd}; border-radius: 8px;"

    @staticmethod
    def splitter_style() -> str:
        p = _PALETTE
        return (
            f"QSplitter::handle {{ background: {p['border']}; width: 6px; }}"
            f"QSplitter::handle:hover {{ background: {p['accent']}; }}"
            f"QSplitter::handle:pressed {{ background: {p['accent_hover']}; }}"
        )

    @staticmethod
    def section_title_style(font_size: int = 22) -> str:
        return f"font-size:{font_size}px; font-weight:bold; color:{_PALETTE['fg']};"


theme = _Theme()
