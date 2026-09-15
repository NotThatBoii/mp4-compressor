import os
from pathlib import Path
import shutil
import subprocess
import sys

CREATE_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def run_tool(args, timeout=30):
    return subprocess.run([str(a) for a in args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout,
                          creationflags=CREATE_FLAGS, check=True)


class FFmpegManager:
    """Find a bundled pair first, then PATH. Supports PyInstaller's resource root."""
    def __init__(self, directory=None):
        root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        roots = [Path(directory)] if directory else []
        if getattr(sys, "frozen", False):
            roots.append(Path(sys.executable).parent / "resources" / "ffmpeg")
        roots.append(root / "resources" / "ffmpeg")
        suffix = ".exe" if os.name == "nt" else ""
        self.ffmpeg = self.ffprobe = None
        for folder in roots:
            pair = [folder / (name + suffix) for name in ("ffmpeg", "ffprobe")]
            if all(p.is_file() for p in pair):
                self.ffmpeg, self.ffprobe = map(str, pair)
                break
        if not self.ffmpeg:
            self.ffmpeg, self.ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
        if not self.ffmpeg or not self.ffprobe:
            raise ValueError("FFmpeg and ffprobe are missing. Put both executables in resources/ffmpeg, or add their bin folder to PATH, then restart Compressly.")
        for executable in (self.ffmpeg, self.ffprobe):
            run_tool([executable, "-version"], timeout=10)
