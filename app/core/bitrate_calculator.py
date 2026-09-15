from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BitrateBudget:
    video_bps: int
    audio_bps: int
    target_bytes: int
    warning: str | None


def calculate_target_bitrate(target_mb, duration, audio_kbps, width, height, fps):
    """Decimal MB, decimal kbps. Reserve 2% for muxing and rate-control variance."""
    if not all(math.isfinite(v) for v in (target_mb, duration, audio_kbps, width, height, fps)) or duration <= 0 or target_mb <= 0:
        raise ValueError("A positive target size and valid video duration are required.")
    target_bytes = int(target_mb * 1_000_000)
    audio_bps = int(audio_kbps * 1000)
    video_bps = int(target_bytes * 8 * 0.98 / duration - audio_bps)
    if video_bps < 10000:
        raise ValueError("The target is too small for the selected audio and video. Increase the target size, lower the audio bitrate, or choose No Audio.")
    # A warning heuristic, not a quality prediction: scene complexity and codec matter.
    bits_per_pixel = video_bps / max(1, width * height * (fps or 30))
    warning = None
    if video_bps < 150000 or bits_per_pixel < 0.025:
        warning = f"This target leaves only {video_bps / 1000:,.0f} kbps for video. Quality may be extremely poor at this resolution. Increase the target size or lower the resolution. Continue anyway?"
    return BitrateBudget(video_bps, audio_bps, target_bytes, warning)


def budget_for(media, options):
    width, height = media.width, media.height
    if options.resolution:
        factor = min(1, options.resolution[0] / width, options.resolution[1] / height)
        width, height = width * factor, height * factor
    return calculate_target_bitrate(options.target_mb, media.duration,
        options.audio_kbps if media.audio else 0, width, height, options.fps or media.fps)
