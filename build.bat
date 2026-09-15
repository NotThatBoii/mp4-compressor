@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Create the virtual environment first. See README.md.
    exit /b 1
)
if not exist "resources\ffmpeg\ffmpeg.exe" (
    echo Missing resources\ffmpeg\ffmpeg.exe. See README.md.
    exit /b 1
)
if not exist "resources\ffmpeg\ffprobe.exe" (
    echo Missing resources\ffmpeg\ffprobe.exe. See README.md.
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt "pyinstaller>=6.11,<7"
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm Compressly.spec
if errorlevel 1 exit /b 1
echo Build ready: dist\Compressly\Compressly.exe
echo Distribute the entire dist\Compressly folder, not just the EXE.
