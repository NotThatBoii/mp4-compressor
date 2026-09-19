import logging
from PySide6.QtCore import QThread, Signal
from app.core.compression_engine import CompressionEngine, Cancelled


class CompressionWorker(QThread):
    progress = Signal(object)
    status = Signal(str)
    result = Signal(object)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, manager, media, options, folder, parent=None):
        super().__init__(parent)
        self.engine = CompressionEngine(manager)
        self.media, self.options, self.folder = media, options, folder

    def cancel(self):
        self.engine.cancel()

    def run(self):
        try:
            result = self.engine.run(self.media, self.options, self.folder, self.progress.emit, self.status.emit)
            self.result.emit(result)
        except Cancelled:
            self.cancelled.emit()
        except Exception as error:
            logging.exception("Video processing failed")
            self.error.emit(str(error) if isinstance(error, ValueError) else "Video processing failed. Check output folder permissions and free disk space. Details are in logs/compressly.log.")
