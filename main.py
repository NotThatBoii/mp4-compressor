"""Compressly desktop entry point."""
import sys

from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.utils.logging_utils import setup_logging


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Compressly")
    app.setOrganizationName("Compressly")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
