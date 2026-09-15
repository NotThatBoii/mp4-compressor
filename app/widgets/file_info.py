from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout


class FileInfo(QGroupBox):
    def __init__(self):
        super().__init__("VIDEO DETAILS")
        layout = QVBoxLayout(self)
        self.name = QLabel("No video selected")
        self.name.setWordWrap(True)
        self.details = QLabel("Your video information will appear here.")
        self.details.setWordWrap(True)
        self.details.setObjectName("muted")
        layout.addWidget(self.name)
        layout.addWidget(self.details)
