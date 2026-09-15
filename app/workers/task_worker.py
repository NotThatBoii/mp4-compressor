import logging
from PySide6.QtCore import QThread, Signal


class TaskWorker(QThread):
    result = Signal(object)
    error = Signal(str)

    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function = function

    def run(self):
        try:
            self.result.emit(self.function())
        except Exception as error:
            logging.exception("Background operation failed")
            self.error.emit(str(error) if isinstance(error, (ValueError, FileNotFoundError)) else "The video tools could not complete this operation. Check that the video is valid and FFmpeg is installed. Details are in logs/compressly.log.")
