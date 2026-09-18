# Third-party components

Compressly's own code is MIT-licensed, copyright (c) 2026 NotThatBoii; see LICENSE. That license applies only to original Compressly code. The components listed below retain their respective upstream licenses.

The installer bundles unmodified, dynamically loaded Python/Qt libraries and separate FFmpeg command-line executables. The `licenses` directory contains license texts. The app does not restrict replacing the bundled libraries or reverse engineering for debugging modifications to LGPL components.

- **CPython 3.12**: Python Software Foundation license; [source and license](https://www.python.org/downloads/source/).
- **PySide6 / Shiboken6 / Qt 6.11.2**: LGPL 3.0 or the applicable upstream license; [PySide source](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/), [Qt source](https://download.qt.io/official_releases/qt/6.11/6.11.2/single/), [license information](https://doc.qt.io/qtforpython-6/licenses.html). The installed `_internal/PySide6` and `_internal/shiboken6` directories remain replaceable; no one-file archive or integrity lock prevents replacing compatible libraries.
- **FFmpeg 9.0.1 essentials build by Gyan**: GPL 3.0 build, including its enabled third-party components. [Original binary release](https://github.com/GyanD/codexffmpeg/releases/tag/9.0.1), [FFmpeg source](https://ffmpeg.org/releases/ffmpeg-9.0.1.tar.xz), [build information and dependency source links](https://www.gyan.dev/ffmpeg/builds/). Run the included `ffmpeg.exe -buildconf` to see the exact build configuration. The executables are unmodified.
- **PyInstaller**: GPL with its bootloader exception; [license and exception](https://pyinstaller.org/en/stable/license.html).
- **Inno Setup**: [Inno Setup license](https://jrsoftware.org/files/is/license.txt); only the generated setup/uninstall runtime is distributed.

Component versions can be checked in the release build logs and the bundled tools. Third-party licenses apply to their respective components.
