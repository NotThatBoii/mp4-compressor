from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
    QScrollArea, QHBoxLayout, QLineEdit, QPushButton, QFileDialog)
from app.theme import STYLE
from app.widgets.drop_zone import DropZone
from app.widgets.file_info import FileInfo
from app.widgets.compression_settings import CompressionSettings
from app.widgets.progress_widget import ProgressWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QMessageBox
from app.core.ffmpeg_manager import FFmpegManager
from app.core.media_probe import probe_media
from app.workers.task_worker import TaskWorker
from app.utils.file_utils import format_size, format_time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compressly — Video Compression")
        self.resize(820, 900)
        self.setMinimumSize(660, 600)
        self.setStyleSheet(STYLE)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        logo = QLabel("COMPRESSLY")
        logo.setObjectName("logo")
        layout.addWidget(logo)
        tagline = QLabel("Less space. More possibilities.")
        tagline.setObjectName("muted")
        layout.addWidget(tagline)
        self.drop = DropZone()
        self.info = FileInfo()
        self.settings = CompressionSettings()
        for widget in [self.drop, self.info, self.settings]:
            layout.addWidget(widget)
        output = QHBoxLayout()
        self.folder = QLineEdit(str(Path.home() / "Videos"))
        self.folder.setAccessibleName("Output folder")
        self.browse = QPushButton("Output Folder…")
        self.browse.clicked.connect(self.choose_folder)
        output.addWidget(self.folder, 1)
        output.addWidget(self.browse)
        layout.addLayout(output)
        actions = QHBoxLayout()
        self.start = QPushButton("Compress Video")
        self.start.setObjectName("primary")
        self.start.setEnabled(False)
        self.cancel = QPushButton("Cancel")
        self.cancel.setEnabled(False)
        actions.addWidget(self.start, 1)
        actions.addWidget(self.cancel)
        layout.addLayout(actions)
        self.progress = ProgressWidget()
        layout.addWidget(self.progress)
        layout.addStretch()
        scroll.setWidget(body)
        self.setCentralWidget(scroll)
        self.manager = None
        self.media = None
        self.task = None
        self.drop.selected.connect(self.load_video)
        self.drop.rejected.connect(self.show_error)
        self.info.name.setTextFormat(Qt.PlainText)
        self.drop.setEnabled(False)
        self.progress.status.setText("Checking FFmpeg…")
        QTimer.singleShot(0, self.initialize)

    def initialize(self):
        self.run_task(FFmpegManager, self.tools_ready)

    def run_task(self, function, callback):
        self.task = TaskWorker(function, self)
        self.task.result.connect(callback)
        self.task.error.connect(self.show_error)
        self.task.finished.connect(self.task_finished)
        self.task.start()

    def task_finished(self):
        self.drop.setEnabled(self.manager is not None)

    def tools_ready(self, manager):
        self.manager = manager
        self.progress.status.setText("Ready — select a video to begin")

    def load_video(self, name):
        if self.task and self.task.isRunning():
            return
        self.media = None
        self.drop.setEnabled(False)
        self.start.setEnabled(False)
        self.info.name.setText(Path(name).name)
        self.info.details.setText("Reading video information…")
        self.progress.status.setText("Analyzing video…")
        self.run_task(lambda: probe_media(self.manager, name), self.video_ready)

    def video_ready(self, media):
        self.media = media
        self.folder.setText(str(media.path.parent))
        self.info.name.setText(media.path.name)
        self.info.details.setText(f"{format_size(media.size)}  •  {media.width} × {media.height}  •  {media.fps:.2f} FPS  •  {format_time(media.duration)}\nVideo: {media.video_codec}  •  Audio: {media.audio_codec}  •  {media.bitrate / 1000:,.0f} kbps")
        self.progress.status.setText("Video analyzed successfully")

    def show_error(self, message):
        self.progress.status.setText(message)
        QMessageBox.warning(self, "Compressly", message)

    def closeEvent(self, event):
        if self.task and self.task.isRunning():
            self.progress.status.setText("Please wait for video analysis to finish before closing.")
            event.ignore()
            return
        event.accept()

    def choose_folder(self):
        name = QFileDialog.getExistingDirectory(self, "Output folder", self.folder.text())
        if name:
            self.folder.setText(name)
