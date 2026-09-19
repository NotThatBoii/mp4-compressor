from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QCheckBox, QLabel
from app.core.conversion import FORMATS, METHODS, ConversionOptions


class ConversionSettings(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("CONVERSION")
        form = QFormLayout(group)
        self.format = QComboBox()
        for extension, profile in FORMATS.items():
            self.format.addItem(profile.label, extension)
        self.method = QComboBox()
        self.method.addItems(METHODS)
        self.audio = QCheckBox("Keep audio")
        self.audio.setChecked(True)
        self.metadata = QCheckBox("Keep metadata and chapters where supported")
        self.metadata.setChecked(True)
        self.subtitles = QCheckBox("Preserve subtitles and fonts (MKV only)")
        self.subtitles.setEnabled(False)
        form.addRow("Output format", self.format)
        form.addRow("Method", self.method)
        for widget in (self.audio, self.metadata, self.subtitles):
            form.addRow(widget)
            widget.toggled.connect(lambda _checked: self.changed.emit())
        note = QLabel("Auto copies compatible streams without quality loss and re-encodes others. If copying fails, Auto retries with re-encoding.\nStream copy only never re-encodes video or audio; incompatible files are rejected.\nRe-encoding uses CPU and may reduce quality or increase file size. Audio becomes stereo; MPG and WMV video becomes 30 FPS. Only the first video and audio tracks are kept. HDR is not supported yet.")
        note.setWordWrap(True)
        note.setObjectName("muted")
        form.addRow(note)
        layout.addWidget(group)
        self.plan = QLabel("Select a video to see the conversion plan.")
        self.plan.setWordWrap(True)
        layout.addWidget(self.plan)
        self.format.currentIndexChanged.connect(self.format_changed)
        self.method.currentIndexChanged.connect(lambda _index: self.changed.emit())

    def format_changed(self):
        supports_subtitles = self.format.currentData() == "mkv"
        if not supports_subtitles:
            self.subtitles.setChecked(False)
        self.subtitles.setEnabled(supports_subtitles)
        self.changed.emit()

    def options(self):
        result = ConversionOptions(self.format.currentData(), self.method.currentText(),
            self.audio.isChecked(), self.metadata.isChecked(), self.subtitles.isChecked())
        result.validate()
        return result
