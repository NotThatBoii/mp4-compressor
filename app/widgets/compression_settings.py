from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QDoubleSpinBox, QSpinBox, QHBoxLayout, QLabel, QCheckBox)
from app.core.models import CompressionOptions


def combo(items, selected=0):
    box = QComboBox()
    box.addItems(items)
    box.setCurrentIndex(selected)
    return box


class CompressionSettings(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        basic = QGroupBox("COMPRESSION")
        form = QFormLayout(basic)
        self.mode = combo(["High Quality", "Balanced", "Small File", "Target File Size"], 1)
        self.codec = combo(["H.264", "H.265 / HEVC", "AV1"], 1)
        self.encoder = combo(["Auto", "CPU", "NVIDIA", "Intel", "AMD"])
        self.target = QDoubleSpinBox()
        self.target.setRange(1, 1000000)
        self.target.setValue(500)
        self.target.setSuffix(" MB")
        self.target.setEnabled(False)
        self.mode.currentIndexChanged.connect(lambda i: self.target.setEnabled(i == 3))
        form.addRow("Mode", self.mode)
        form.addRow("Codec", self.codec)
        form.addRow("Encoder", self.encoder)
        form.addRow("Target size", self.target)
        note = QLabel("H.265 offers efficient compression. AV1 can be significantly slower.\nHardware is faster; CPU often gives better compression. Auto falls back to CPU.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        form.addRow(note)
        layout.addWidget(basic)
        self.expand = QCheckBox("Advanced Settings")
        layout.addWidget(self.expand)
        self.advanced = QGroupBox()
        advanced = QFormLayout(self.advanced)
        self.resolution = combo(["Original", "4K", "1440p", "1080p", "720p", "Custom"])
        custom = QWidget()
        row = QHBoxLayout(custom)
        row.setContentsMargins(0, 0, 0, 0)
        self.width, self.height = QSpinBox(), QSpinBox()
        for box, value in [(self.width, 1920), (self.height, 1080)]:
            box.setRange(2, 7680)
            box.setSingleStep(2)
            box.setValue(value)
        row.addWidget(self.width)
        row.addWidget(QLabel("×"))
        row.addWidget(self.height)
        custom.setEnabled(False)
        self.resolution.currentIndexChanged.connect(lambda i: custom.setEnabled(i == 5))
        self.fps = combo(["Original", "60", "30", "24"])
        self.audio = combo(["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "No Audio"], 3)
        self.metadata = combo(["Keep metadata", "Remove metadata"])
        self.subtitles = combo(["Remove subtitles", "Preserve subtitles"])
        for label, widget in [("Resolution", self.resolution), ("Custom bounds", custom),
                ("FPS", self.fps), ("Audio", self.audio), ("Metadata", self.metadata), ("Subtitles", self.subtitles)]:
            advanced.addRow(label, widget)
        hint = QLabel("Resolution fits within the selected bounds, preserving aspect ratio.\nPreserving subtitles uses MKV to keep original subtitle tracks and fonts.")
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        advanced.addRow(hint)
        layout.addWidget(self.advanced)
        self.advanced.hide()
        self.expand.toggled.connect(self.advanced.setVisible)
        self.estimate = QLabel("Estimated Size: select a video first")
        self.estimate.setWordWrap(True)
        layout.addWidget(self.estimate)

    def options(self):
        sizes = [None, (3840, 2160), (2560, 1440), (1920, 1080), (1280, 720), (self.width.value(), self.height.value())]
        result = CompressionOptions(mode=self.mode.currentText(), codec=["h264", "hevc", "av1"][self.codec.currentIndex()],
            encoder=self.encoder.currentText(), target_mb=self.target.value(),
            resolution=sizes[self.resolution.currentIndex()],
            fps=None if self.fps.currentIndex() == 0 else int(self.fps.currentText()),
            audio_kbps=[320, 256, 192, 128, 96, 0][self.audio.currentIndex()],
            keep_metadata=self.metadata.currentIndex() == 0,
            keep_subtitles=self.subtitles.currentIndex() == 1)
        result.validate()
        return result
