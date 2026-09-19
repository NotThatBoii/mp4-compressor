from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QFileDialog

SUPPORTED = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv", ".flv", ".mpg", ".mpeg", ".ts", ".mts", ".m2ts", ".3gp", ".3g2", ".vob", ".ogv", ".mxf", ".f4v", ".asf"}


class DropZone(QFrame):
    selected = Signal(str)
    rejected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        title = QLabel("Drop your video here")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignCenter)
        hint = QLabel("MP4, MOV, MKV, AVI, WebM and more  •  One video at a time")
        hint.setAlignment(Qt.AlignCenter)
        hint.setObjectName("muted")
        button = QPushButton("Select Video")
        button.clicked.connect(self.choose)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(button, alignment=Qt.AlignCenter)

    def choose(self):
        patterns = " ".join("*" + extension for extension in sorted(SUPPORTED))
        name, _ = QFileDialog.getOpenFileName(self, "Select video", "", f"Videos ({patterns});;All files (*)")
        if name:
            self.accept_path(name)

    def accept_path(self, name):
        path = Path(name)
        if not path.is_file():
            self.rejected.emit("Choose a video file on your computer.")
            return
        self.selected.emit(str(path.resolve()))

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if self.isEnabled() and len(urls) == 1 and urls[0].isLocalFile():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if self.isEnabled() and len(urls) == 1 and urls[0].isLocalFile():
            self.accept_path(urls[0].toLocalFile())
