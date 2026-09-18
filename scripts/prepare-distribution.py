"""Include third-party notices and reject incomplete release payloads."""
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
payload = root / 'dist' / 'Compressly'
for relative in ('Compressly.exe', '_internal/resources/ffmpeg/ffmpeg.exe', '_internal/resources/ffmpeg/ffprobe.exe'):
    if not (payload / relative).is_file():
        raise SystemExit(f'Missing release payload: {relative}')
licenses = payload / 'licenses'
licenses.mkdir(exist_ok=True)
shutil.copy2(root / 'resources/ffmpeg/LICENSE', licenses / 'FFmpeg-GPL-3.0.txt')
shutil.copy2(Path(sys.base_prefix) / 'LICENSE.txt', licenses / 'Python-LICENSE.txt')
for source in (root / 'resources/licenses').glob('*.txt'):
    shutil.copy2(source, licenses / source.name)
shutil.copy2(root / 'THIRD_PARTY.md', payload / 'THIRD_PARTY.md')
shutil.copy2(root / 'installer/install-info.txt', payload / 'README.txt')
shutil.copy2(root / 'VERSION', payload / 'VERSION')
print('Distribution payload and licenses prepared.')
