# Build on Windows with: .venv\Scripts\python.exe -m PyInstaller Compressly.spec
from pathlib import Path
import os
import sys

# Do not collect unrelated DLLs from developer tools on PATH (for example,
# Poppler's ICU has versioned exports incompatible with Qt's Windows ICU API).
windows = Path(os.environ["SystemRoot"])
os.environ["PATH"] = os.pathsep.join([str(Path(sys.base_prefix)),
    str(Path(sys.base_prefix) / "DLLs"), str(windows / "System32"), str(windows)])

root = Path(SPECPATH)
tools = root / "resources" / "ffmpeg"
for name in ("ffmpeg.exe", "ffprobe.exe"):
    if not (tools / name).is_file():
        raise SystemExit(f"Missing resources/ffmpeg/{name}. Add both FFmpeg executables before building.")

a = Analysis([str(root / "main.py")], pathex=[str(root)],
             binaries=[], datas=[(str(root / "resources"), "resources")],
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=["tkinter", "unittest"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Compressly",
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=os.environ.get("COMPRESSLY_DEBUG_CONSOLE") == "1", disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Compressly")
