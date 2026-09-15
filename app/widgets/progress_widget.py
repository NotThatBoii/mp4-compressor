from PySide6.QtWidgets import QGroupBox, QLabel, QProgressBar, QVBoxLayout


class ProgressWidget(QGroupBox):
    def __init__(self):
        super().__init__("ACTIVITY")
        layout = QVBoxLayout(self)
        self.status = QLabel("Ready when you are")
        self.status.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.setValue(0)
        self.stats = QLabel("Speed: —   •   Elapsed: —   •   ETA: —")
        self.stats.setWordWrap(True)
        self.stats.setObjectName("muted")
        layout.addWidget(self.status)
        layout.addWidget(self.bar)
        layout.addWidget(self.stats)
