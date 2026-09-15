from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
    QScrollArea, QHBoxLayout, QLineEdit, QPushButton, QFileDialog)
from app.theme import STYLE
from app.widgets.drop_zone import DropZone
from app.widgets.file_info import FileInfo
from app.widgets.compression_settings import CompressionSettings
from app.widgets.progress_widget import ProgressWidget
from PySide6.QtCore import QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox
from app.core.ffmpeg_manager import FFmpegManager
from app.core.media_probe import probe_media
from app.workers.task_worker import TaskWorker
from app.utils.file_utils import format_size, format_time
from app.workers.compression_worker import CompressionWorker
from app.core.bitrate_calculator import budget_for


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compressly — Video Compression")
        screen_height = self.screen().availableGeometry().height()
        self.resize(820, min(900, screen_height - 80))
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
        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(28, 12, 28, 20)
        footer_layout.setSpacing(12)
        output = QHBoxLayout()
        self.folder = QLineEdit(str(Path.home() / "Videos"))
        self.folder.setAccessibleName("Output folder")
        self.browse = QPushButton("Output Folder…")
        self.browse.clicked.connect(self.choose_folder)
        output.addWidget(self.folder, 1)
        output.addWidget(self.browse)
        footer_layout.addLayout(output)
        actions = QHBoxLayout()
        self.start = QPushButton("Compress Video")
        self.start.setObjectName("primary")
        self.start.setEnabled(False)
        self.cancel = QPushButton("Cancel")
        self.cancel.setEnabled(False)
        self.open_output = QPushButton("Open Output Folder")
        self.open_output.setVisible(False)
        self.open_output.clicked.connect(self.reveal_output)
        actions.addWidget(self.start, 1)
        actions.addWidget(self.cancel)
        footer_layout.addLayout(actions)
        self.progress = ProgressWidget()
        footer_layout.addWidget(self.progress)
        footer_layout.addWidget(self.open_output)
        layout.addStretch()
        scroll.setWidget(body)
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(scroll, 1)
        central_layout.addWidget(footer)
        self.setCentralWidget(central)
        self.manager = None
        self.media = None
        self.task = None
        self.job = None
        self.last_output = None
        self.close_requested = False
        self.start.clicked.connect(self.compress)
        self.cancel.clicked.connect(self.cancel_job)
        for box in (self.settings.mode, self.settings.codec, self.settings.audio,
                    self.settings.resolution, self.settings.fps, self.settings.subtitles):
            box.currentIndexChanged.connect(self.update_estimate)
        for box in (self.settings.target, self.settings.width, self.settings.height):
            box.valueChanged.connect(self.update_estimate)
        self.drop.selected.connect(self.load_video)
        self.drop.rejected.connect(self.show_error)
        self.info.name.setTextFormat(Qt.PlainText)
        self.progress.status.setTextFormat(Qt.PlainText)
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
        task, self.task = self.task, None
        if task:
            task.deleteLater()
        self.drop.setEnabled(self.manager is not None)
        self.start.setEnabled(self.media is not None)
        if self.close_requested:
            self.close()

    def tools_ready(self, manager):
        self.manager = manager
        self.progress.status.setText("Ready — select a video to begin")

    def load_video(self, name):
        if not self.manager or (self.task and self.task.isRunning()) or (self.job and self.job.isRunning()):
            return
        self.media = None
        self.drop.setEnabled(False)
        self.start.setEnabled(False)
        self.info.name.setText(Path(name).name)
        self.info.details.setText("Reading video information…")
        self.progress.status.setText("Analyzing video…")
        self.progress.bar.setValue(0)
        self.progress.stats.setText("Speed: —   •   Elapsed: —   •   ETA: —")
        self.update_estimate()
        self.run_task(lambda: probe_media(self.manager, name), self.video_ready)

    def video_ready(self, media):
        self.media = media
        self.folder.setText(str(media.path.parent))
        self.info.name.setText(media.path.name)
        self.info.details.setText(f"{format_size(media.size)}  •  {media.width} × {media.height}  •  {media.fps:.2f} FPS  •  {format_time(media.duration)}\nVideo: {media.video_codec}  •  Audio: {media.audio_codec}  •  {media.bitrate / 1000:,.0f} kbps")
        self.progress.status.setText("Video analyzed successfully")
        self.start.setEnabled(True)
        self.update_estimate()

    def update_estimate(self):
        if not self.media:
            self.settings.estimate.setText("Estimated Size: select a video first")
            return
        try:
            options = self.settings.options()
            if options.mode == "Target File Size":
                budget = budget_for(self.media, options)
                note = " Quality warning: very low video bitrate." if budget.warning else ""
                self.settings.estimate.setText(f"Estimated Size: approximately {options.target_mb:,.2f} MB • Video: {budget.video_bps / 1000:,.0f} kbps.{note}\nCPU H.264/H.265 use two passes. Hardware and AV1 use single-pass bitrate control; size can vary.")
            else:
                self.settings.estimate.setText("Estimated Size: cannot be predicted reliably for quality-based encoding. Content and encoder determine the result; output can be larger than the source.")
        except ValueError as error:
            self.settings.estimate.setText(str(error))

    def compress(self):
        if not self.media or (self.job and self.job.isRunning()):
            return
        try:
            options = self.settings.options()
            if options.mode == "Target File Size":
                budget = budget_for(self.media, options)
                if budget.warning and QMessageBox.question(self, "Low quality target", budget.warning,
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                    return
        except ValueError as error:
            self.show_error(str(error))
            return
        self.job = CompressionWorker(self.manager, self.media, options, self.folder.text(), self)
        self.job.progress.connect(self.update_progress)
        self.job.status.connect(self.progress.status.setText)
        self.job.result.connect(self.completed)
        self.job.error.connect(self.show_error)
        self.job.cancelled.connect(lambda: self.progress.status.setText("Compression cancelled. Incomplete output removed."))
        self.job.finished.connect(self.job_finished)
        self.set_busy(True)
        self.progress.bar.setValue(0)
        self.progress.stats.setText("Speed: —   •   Elapsed: 00:00   •   ETA: —")
        self.progress.status.setText("Preparing compression…")
        self.open_output.hide()
        self.job.start()

    def job_finished(self):
        job, self.job = self.job, None
        if job:
            job.deleteLater()
        self.set_busy(False)
        if self.close_requested:
            self.close()

    def set_busy(self, busy):
        for widget in (self.drop, self.settings, self.folder, self.browse):
            widget.setEnabled(not busy)
        self.start.setEnabled(not busy and self.media is not None)
        self.cancel.setEnabled(busy)

    def cancel_job(self):
        if self.job and self.job.isRunning():
            self.job.cancel()
            self.cancel.setEnabled(False)
            self.progress.status.setText("Cancelling and cleaning up…")

    def update_progress(self, data):
        self.progress.bar.setValue(int(data["percent"]))
        self.progress.stats.setText(f"FPS: {data['fps']}  •  Speed: {data['speed']}  •  Elapsed: {format_time(data['elapsed'])}  •  ETA: {format_time(data['eta'])}\nEncoded size: {format_size(data['size'])}")

    def completed(self, result):
        self.last_output = result.path
        self.open_output.show()
        self.progress.bar.setValue(100)
        saved = (1 - result.size / result.original_size) * 100
        saving = f"Space saved: {saved:.1f}%" if saved >= 0 else f"Output is {-saved:.1f}% larger. Try Small File or Target File Size."
        self.progress.status.setText(f"Complete — {result.path.name}\nOriginal: {format_size(result.original_size)}  •  Compressed: {format_size(result.size)}\n{saving}\nSaved to: {result.path}")
        self.progress.stats.setText(f"Encoding time: {format_time(result.elapsed)}  •  Encoder: {result.encoder}")

    def reveal_output(self):
        if self.last_output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output.parent)))

    def show_error(self, message):
        self.progress.status.setText(message)
        QMessageBox.warning(self, "Compressly", message)

    def closeEvent(self, event):
        if self.job and self.job.isRunning():
            self.close_requested = True
            self.cancel_job()
            self.progress.status.setText("Cancelling safely. Compressly will close after cleanup.")
            event.ignore()
            return
        if self.task and self.task.isRunning():
            self.close_requested = True
            self.progress.status.setText("Finishing video analysis before closing…")
            event.ignore()
            return
        event.accept()

    def choose_folder(self):
        name = QFileDialog.getExistingDirectory(self, "Output folder", self.folder.text())
        if name:
            self.folder.setText(name)
