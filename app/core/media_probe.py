from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path

from app.core.ffmpeg_manager import run_tool


def number(value, default=0.0):
    try:
        result = float(Fraction(str(value)))
        return result if math.isfinite(result) else default
    except (ValueError, ZeroDivisionError, TypeError):
        return default


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    size: int
    duration: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str
    bitrate: int
    video_index: int
    audio: dict | None
    subtitles: tuple
    hdr: bool = False


def probe_media(manager, path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("Please select a video file.")
    result = run_tool([manager.ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    if not video:
        raise ValueError("This file has no playable video stream.")
    fmt = data.get("format", {})
    duration = number(fmt.get("duration")) or number(video.get("duration"))
    width, height = int(video.get("width", 0)), int(video.get("height", 0))
    if duration <= 0 or min(width, height) <= 0:
        raise ValueError("The video's duration or dimensions could not be read. The file may be damaged or incomplete.")
    # ffmpeg autorotates by default; report display dimensions for portrait phone videos.
    rotation = number(video.get("tags", {}).get("rotate"))
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = number(side["rotation"])
    if round(rotation) % 180:
        width, height = height, width
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    size = path.stat().st_size
    return MediaInfo(path, size, duration, width, height,
        number(video.get("avg_frame_rate")) or number(video.get("r_frame_rate")),
        video.get("codec_name", "Unknown"), audio.get("codec_name", "Unknown") if audio else "None",
        int(number(fmt.get("bit_rate")) or size * 8 / duration), int(video["index"]), audio,
        tuple(s for s in streams if s.get("codec_type") == "subtitle"),
        video.get("color_transfer") in ("smpte2084", "arib-std-b67"))
