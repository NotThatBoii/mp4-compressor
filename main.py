"""Compressly desktop entry point."""
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app.main_window import MainWindow
from app.utils.logging_utils import setup_logging


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("Compressly")
    app.setOrganizationName("Compressly")
    app.setStyle("Fusion")
    window = MainWindow()
    if "--smoke-test" in sys.argv:
        # Exercise the packaged Qt imports and bundled FFmpeg discovery without
        # requiring manual interaction or leaving a background app running.
        errors = []
        window.show_error = errors.append
        timer = QTimer(app)

        def finish_smoke_test():
            if window.task is None and (window.manager is not None or errors):
                window.close()
                app.exit(1 if errors else 0)

        timer.timeout.connect(finish_smoke_test)
        timer.start(50)
    else:
        window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
