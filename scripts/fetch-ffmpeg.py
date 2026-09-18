"""Fetch the release's fixed FFmpeg build, verifying SHA-256 before extraction."""
import hashlib
from pathlib import Path
import shutil
import urllib.request
import zipfile

root = Path(__file__).resolve().parents[1]
work = root / 'work'
work.mkdir(exist_ok=True)
archive = work / 'ffmpeg-9.0.1.zip'
url = 'https://github.com/GyanD/codexffmpeg/releases/download/9.0.1/ffmpeg-9.0.1-essentials_build.zip'
expected = 'fec81ae03971d9dd4be3ebe02e263bd2ec1d789483f931bdba5f5715e65da2e9'
if not archive.exists():
    with urllib.request.urlopen(url, timeout=120) as response, archive.open('wb') as output:
        shutil.copyfileobj(response, output)
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
if digest != expected:
    raise SystemExit('FFmpeg download checksum mismatch; refusing to use it. Delete work/ffmpeg-9.0.1.zip and retry.')
destination = root / 'resources' / 'ffmpeg'
destination.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive) as bundle:
    for filename in ('ffmpeg.exe', 'ffprobe.exe', 'LICENSE'):
        matches = [n for n in bundle.namelist() if Path(n).name == filename]
        if len(matches) != 1:
            raise SystemExit(f'Expected exactly one {filename} in the verified archive.')
        with bundle.open(matches[0]) as source, (destination / filename).open('wb') as output:
            shutil.copyfileobj(source, output)
print('Verified FFmpeg 9.0.1 prepared.')
