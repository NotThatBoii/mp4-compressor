from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel,
    QScrollArea, QHBoxLayout, QLineEdit, QPushButton, QFileDialog)
from app.theme import STYLE
from app.widgets.drop_zone import DropZone
from app.widgets.file_info import FileInfo
from app.widgets.compression_settings import CompressionSettings
from app.widgets.progress_widget import ProgressWidget


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

    def choose_folder(self):
        name = QFileDialog.getExistingDirectory(self, "Output folder", self.folder.text())
        if name:
            self.folder.setText(name)
