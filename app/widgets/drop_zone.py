from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QFileDialog

SUPPORTED = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


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
        hint = QLabel("MP4, MKV, MOV, AVI, WebM or M4V  •  One video at a time")
        hint.setAlignment(Qt.AlignCenter)
        hint.setObjectName("muted")
        button = QPushButton("Select Video")
        button.clicked.connect(self.choose)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(button, alignment=Qt.AlignCenter)

    def choose(self):
        name, _ = QFileDialog.getOpenFileName(self, "Select video", "", "Videos (*.mp4 *.mkv *.mov *.avi *.webm *.m4v)")
        if name:
            self.accept_path(name)

    def accept_path(self, name):
        path = Path(name)
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            self.rejected.emit("Choose a supported video file on your computer.")
            return
        self.selected.emit(str(path.resolve()))

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if self.isEnabled() and len(urls) == 1 and urls[0].isLocalFile():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.isEnabled():
            self.accept_path(event.mimeData().urls()[0].toLocalFile())
