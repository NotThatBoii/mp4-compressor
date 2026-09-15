from dataclasses import dataclass


@dataclass(frozen=True)
class CompressionOptions:
    mode: str = "Balanced"
    codec: str = "hevc"
    encoder: str = "Auto"
    target_mb: float = 500
    resolution: tuple[int, int] | None = None
    fps: int | None = None
    audio_kbps: int = 128
    keep_metadata: bool = True
    keep_subtitles: bool = False

    def validate(self):
        if self.mode not in ("High Quality", "Balanced", "Small File", "Target File Size"):
            raise ValueError("Choose a valid compression mode.")
        if self.codec not in ("h264", "hevc", "av1"):
            raise ValueError("Choose a supported codec.")
        if self.encoder not in ("Auto", "CPU", "NVIDIA", "Intel", "AMD"):
            raise ValueError("Choose a supported encoder.")
        if not 1 <= self.target_mb <= 1000000:
            raise ValueError("Target size must be between 1 and 1,000,000 MB.")
        if self.resolution and any(v < 2 or v > 7680 or v % 2 for v in self.resolution):
            raise ValueError("Custom dimensions must be even numbers between 2 and 7680.")
        if self.fps not in (None, 24, 30, 60):
            raise ValueError("Choose a supported frame rate.")
        if self.audio_kbps not in (0, 96, 128, 192, 256, 320):
            raise ValueError("Choose a supported audio bitrate.")
