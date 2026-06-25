"""CategoryDetailDialog — show course details for a curriculum category."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class CategoryDetailDialog(QDialog):
    """Dialog showing detailed courses for a curriculum category."""

    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{result.name} - 课程明细")
        self.setMinimumSize(760, 520)
        layout = QVBoxLayout(self)

        required_text = (
            "-"
            if result.required_credits <= 0
            else f"{result.required_credits:g}"
        )
        summary = QLabel(
            f"<h2>{result.name}</h2>"
            f"目标学分：<b>{required_text}</b>　"
            f"已完成：<b>{result.earned_credits:g}</b>　"
            f"还差：<b>{result.remaining_credits:g}</b><br>"
            f"<span style='color:#77716a'>{result.note}</span>"
        )
        summary.setTextFormat(Qt.TextFormat.RichText)
        summary.setWordWrap(True)
        layout.addWidget(summary)

        if result.missing_codes:
            missing = QLabel(
                "待核对/补修课程：" + "、".join(result.missing_codes[:18])
            )
            missing.setWordWrap(True)
            missing.setStyleSheet(
                "background-color: #fff7e8; border: 1px solid #ead7ad; "
                "border-radius: 6px; padding: 8px; color: #756047;"
            )
            layout.addWidget(missing)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["课程名", "代码", "学分", "学期", "成绩", "类别"]
        )
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        table.setRowCount(len(result.courses))
        for row, course in enumerate(result.courses):
            values = [
                course.name,
                course.code,
                f"{course.credit:g}",
                course.semester,
                f"{course.grade:g}",
                course.category,
            ]
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(str(value)))
        layout.addWidget(table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
