"""PDPTool - Personal Development Planning Tool.

Entry point for the application.

Usage:
    python main.py
"""

import sys
import os

# Ensure src is on the path
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from src.views.main_window import MainWindow
from src.utils.theme import theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDPTool")
    app.setStyleSheet(theme.stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
