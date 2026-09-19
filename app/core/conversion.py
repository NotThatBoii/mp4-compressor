"""Container-aware conversion profiles. No shell commands or UI dependencies."""
from dataclasses import dataclass


@dataclass(frozen=True)
class FormatProfile:
    label: str
    muxer: str
    video_encoder: str
    audio_encoder: str
    copy_video: tuple[str, ...]
    copy_audio: tuple[str, ...]


# Conservative compatibility lists. A codec name cannot capture every profile,
# codec tag or timestamp constraint; Auto retries a failed remux by re-encoding.
FORMATS = {
    "mp4": FormatProfile("MP4", "mp4", "libx264", "aac", ("h264", "hevc", "av1", "mpeg4"), ("aac", "mp3", "ac3", "eac3")),
    "mov": FormatProfile("MOV / QuickTime", "mov", "libx264", "aac", ("h264", "hevc", "prores", "mjpeg", "mpeg4"), ("aac", "mp3", "alac", "pcm_s16le", "pcm_s24le")),
    "mkv": FormatProfile("MKV / Matroska", "matroska", "libx264", "aac", ("h264", "hevc", "av1", "vp8", "vp9", "mpeg4", "mpeg2video", "ffv1", "mjpeg", "theora"), ("aac", "mp3", "mp2", "ac3", "eac3", "opus", "vorbis", "flac", "pcm_s16le", "pcm_s24le", "dts", "truehd")),
    "webm": FormatProfile("WebM", "webm", "libvpx-vp9", "libopus", ("vp8", "vp9", "av1"), ("opus", "vorbis")),
    "avi": FormatProfile("AVI", "avi", "mpeg4", "libmp3lame", ("mpeg4", "mjpeg", "msmpeg4v2", "msmpeg4v3", "ffv1", "huffyuv"), ("mp3", "pcm_s16le", "ac3")),
    "wmv": FormatProfile("WMV / Windows Media", "asf", "wmv2", "wmav2", ("wmv1", "wmv2", "wmv3", "vc1"), ("wmav1", "wmav2", "wmapro")),
    "flv": FormatProfile("FLV / Flash Video", "flv", "flv", "libmp3lame", ("h264", "flv1", "vp6f"), ("aac", "mp3")),
    "mpg": FormatProfile("MPG / MPEG-2", "mpeg", "mpeg2video", "mp2", ("mpeg1video", "mpeg2video"), ("mp2", "mp3", "ac3")),
    "ts": FormatProfile("TS / MPEG Transport Stream", "mpegts", "libx264", "aac", ("h264", "hevc", "mpeg2video"), ("aac", "mp2", "mp3", "ac3", "eac3")),
    "m4v": FormatProfile("M4V / MPEG-4 container", "mp4", "libx264", "aac", ("h264", "hevc", "mpeg4"), ("aac", "ac3")),
    "3gp": FormatProfile("3GP", "3gp", "libx264", "aac", ("h264", "mpeg4", "h263"), ("aac", "amr_nb", "amr_wb")),
}
METHODS = ("Auto", "Re-encode", "Stream copy only")


@dataclass(frozen=True)
class ConversionOptions:
    output_format: str = "mp4"
    method: str = "Auto"
    keep_audio: bool = True
    keep_metadata: bool = True
    keep_subtitles: bool = False

    @property
    def mode(self):
        return "Conversion"

    def validate(self):
        if self.output_format not in FORMATS:
            raise ValueError("Choose a supported output format.")
        if self.method not in METHODS:
            raise ValueError("Choose a valid conversion method.")
        if self.keep_subtitles and self.output_format != "mkv":
            raise ValueError("Choose MKV to preserve subtitles during conversion.")


@dataclass(frozen=True)
class ConversionPlan:
    video_encoder: str
    audio_encoder: str | None

    @property
    def has_copy(self):
        return self.video_encoder == "copy" or self.audio_encoder == "copy"

    @property
    def lossless(self):
        return self.video_encoder == "copy" and self.audio_encoder in (None, "copy")

    @property
    def description(self):
        video = "copy original" if self.video_encoder == "copy" else f"re-encode ({self.video_encoder})"
        audio = "none" if self.audio_encoder is None else "copy original" if self.audio_encoder == "copy" else f"re-encode ({self.audio_encoder})"
        return f"Video: {video} • Audio: {audio}"


def plan_conversion(media, options, force_encode=False):
    options.validate()
    if media.hdr:
        raise ValueError("HDR video is not supported yet. Use an SDR source to avoid incorrect colors.")
    profile = FORMATS[options.output_format]
    reencode = force_encode or options.method == "Re-encode"
    video = "copy" if not reencode and media.video_codec in profile.copy_video else profile.video_encoder
    audio = None
    if options.keep_audio and media.audio:
        audio = "copy" if not reencode and media.audio_codec in profile.copy_audio else profile.audio_encoder
    if options.method == "Stream copy only":
        if video != "copy" or audio not in (None, "copy"):
            raise ValueError(f"The source codecs ({media.video_codec}/{media.audio_codec}) cannot be copied to {profile.label}. Choose Auto or Re-encode, or a different output format.")
        if options.keep_subtitles and any(s.get("codec_name") == "mov_text" for s in media.subtitles):
            raise ValueError("MP4 timed-text subtitles need conversion to SRT for MKV. Choose Auto or remove subtitles.")
    return ConversionPlan(video, audio)


def build_conversion_command(manager, media, options, plan, destination):
    profile = FORMATS[options.output_format]
    args = [manager.ffmpeg, "-hide_banner", "-y", "-loglevel", "warning", "-nostats",
            "-progress", "pipe:1", "-i", str(media.path), "-map", f"0:{media.video_index}", "-c:v", plan.video_encoder]
    if plan.video_encoder != "copy":
        args += ["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-pix_fmt", "yuv420p"]
        if plan.video_encoder == "libx264":
            args += ["-preset", "medium", "-crf", "20"]
        elif plan.video_encoder == "libvpx-vp9":
            args += ["-crf", "30", "-b:v", "0", "-deadline", "good", "-cpu-used", "2"]
        else:
            args += ["-q:v", "3"]
        if plan.video_encoder in ("mpeg2video", "wmv2"):
            args += ["-r", "30"]
    if plan.audio_encoder:
        args += ["-map", f"0:{media.audio['index']}", "-c:a", plan.audio_encoder]
        if plan.audio_encoder != "copy":
            # Explicit stereo/sample rate works for legacy encoders and unusual
            # multichannel sources; users are told that re-encoded audio is stereo.
            args += ["-b:a", "128k", "-ac", "2", "-ar", "48000" if plan.audio_encoder in ("libopus", "mp2") else "44100"]
    else:
        args += ["-an"]
    if options.keep_subtitles and media.subtitles:
        args += ["-map", "0:s?", "-c:s", "copy", "-map", "0:t?", "-c:t", "copy"]
        for index, subtitle in enumerate(media.subtitles):
            if subtitle.get("codec_name") == "mov_text":
                args += [f"-c:s:{index}", "srt"]
    else:
        args += ["-sn"]
    args += ["-map_metadata", "0" if options.keep_metadata else "-1",
             "-map_chapters", "0" if options.keep_metadata else "-1"]
    if not options.keep_metadata:
        args += ["-map_metadata:s", "-1"]
    if profile.muxer in ("mp4", "mov"):
        args += ["-movflags", "+faststart"]
        if plan.video_encoder == "copy" and media.video_codec == "hevc":
            args += ["-tag:v", "hvc1"]
    # Explicit muxer is essential: a .m4v extension otherwise selects raw video.
    return args + ["-f", profile.muxer, str(destination)]
