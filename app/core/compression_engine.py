"""FFmpeg command planning, background execution and safe output publication."""
from dataclasses import dataclass
import logging
import os
from pathlib import Path
from queue import Queue, Empty
import shutil
import subprocess
import tempfile
from threading import Event, Thread
import time

from app.core.ffmpeg_manager import CREATE_FLAGS
from app.utils.file_utils import output_path

CPU_ENCODERS = {"h264": "libx264", "hevc": "libx265", "av1": "libsvtav1"}
CRF = {"h264": [19, 23, 27], "hevc": [22, 26, 30], "av1": [24, 32, 40]}


class Cancelled(Exception):
    pass


@dataclass
class CompressionResult:
    path: Path
    original_size: int
    size: int
    elapsed: float
    encoder: str


def video_filters(options):
    filters = []
    if options.resolution:
        w, h = options.resolution
        # Bounds preserve aspect ratio; min() avoids upscaling small sources.
        filters.append(f"scale=w='min(iw,{w})':h='min(ih,{h})':force_original_aspect_ratio=decrease:force_divisible_by=2")
    else:
        filters.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")
    if options.fps:
        filters.append(f"fps={options.fps}")
    return ",".join(filters)


def build_commands(manager, media, options, encoder, destination):
    options.validate()
    quality = CRF[options.codec][["High Quality", "Balanced", "Small File"].index(options.mode)]
    args = [manager.ffmpeg, "-hide_banner", "-y", "-loglevel", "warning", "-nostats",
            "-progress", "pipe:1", "-i", str(media.path), "-map", f"0:{media.video_index}",
            "-vf", video_filters(options), "-c:v", encoder, "-pix_fmt", "yuv420p",
            "-preset", "6" if encoder == "libsvtav1" else "medium", "-crf", str(quality)]
    if media.audio and options.audio_kbps:
        args += ["-map", f"0:{media.audio['index']}", "-c:a", "aac", "-b:a", f"{options.audio_kbps}k"]
    else:
        args += ["-an"]
    if options.keep_subtitles and media.subtitles:
        args += ["-map", "0:s?", "-c:s", "copy", "-map", "0:t?", "-c:t", "copy"]
    else:
        args += ["-sn"]
    args += ["-map_metadata", "0" if options.keep_metadata else "-1",
             "-map_chapters", "0" if options.keep_metadata else "-1"]
    if not options.keep_metadata:
        args += ["-map_metadata:s", "-1"]
    if destination.suffix == ".mp4":
        args += ["-movflags", "+faststart"]
        if options.codec == "hevc":
            args += ["-tag:v", "hvc1"]
    return [args + [str(destination)]]


class CompressionEngine:
    def __init__(self, manager):
        self.manager = manager
        self.cancel_event = Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self, media, options, folder, progress=lambda data: None, status=lambda message: None):
        options.validate()
        folder = Path(folder).expanduser().resolve()
        if not folder.is_dir():
            raise ValueError("The output folder does not exist. Choose an existing writable folder.")
        if media.hdr:
            raise ValueError("HDR video is not supported in this MVP. Use an SDR source to avoid incorrect colors.")
        if shutil.disk_usage(folder).free < 100_000_000:
            raise ValueError("Not enough disk space. Free at least 100 MB before compressing.")
        suffix = ".mkv" if options.keep_subtitles and media.subtitles else ".mp4"
        started = time.monotonic()
        encoder = CPU_ENCODERS[options.codec]
        # Private temporary directory on the destination volume; originals are never opened for writing.
        with tempfile.TemporaryDirectory(prefix=".compressly-", dir=folder) as work:
            temp = Path(work) / ("encoded" + suffix)
            commands = build_commands(self.manager, media, options, encoder, temp)
            for index, args in enumerate(commands):
                status(f"Compressing with {encoder} — pass {index + 1}/{len(commands)}")
                self._execute(args, Path(work), media.duration, index, len(commands), started, progress)
            if self.cancel_event.is_set():
                raise Cancelled()
            if not temp.is_file() or temp.stat().st_size == 0:
                raise ValueError("FFmpeg did not produce a valid output file.")
            final = output_path(media.path, folder, suffix)
            # Reserve the final name atomically, including when multiple app instances run.
            while True:
                try:
                    with final.open("xb"):
                        pass
                    break
                except FileExistsError:
                    final = output_path(media.path, folder, suffix)
            try:
                os.replace(temp, final)
            except OSError:
                final.unlink(missing_ok=True)
                raise
            return CompressionResult(final, media.size, final.stat().st_size, time.monotonic() - started, encoder)

    def _execute(self, args, work, duration, pass_index, pass_count, started, progress):
        if self.cancel_event.is_set():
            raise Cancelled()
        logging.info("Running FFmpeg: %r", args)
        with (work / "ffmpeg-errors.log").open("w+", encoding="utf-8") as errors:
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=errors, text=True, encoding="utf-8", errors="replace", bufsize=1,
                cwd=work, creationflags=CREATE_FLAGS)
            lines = Queue()

            def read_stdout():
                for line in process.stdout:
                    lines.put(line)
                lines.put(None)

            reader = Thread(target=read_stdout, daemon=True)
            reader.start()
            data = {}
            cancelled_at = None
            try:
                while True:
                    if self.cancel_event.is_set():
                        if cancelled_at is None:
                            cancelled_at = time.monotonic()
                            try:
                                process.stdin.write("q\n")
                                process.stdin.flush()
                            except (OSError, ValueError):
                                pass
                        elif time.monotonic() - cancelled_at > 3 and process.poll() is None:
                            process.kill()
                    try:
                        line = lines.get(timeout=0.1)
                    except Empty:
                        continue
                    if line is None:
                        break
                    key, separator, value = line.strip().partition("=")
                    if separator:
                        data[key] = value
                    if key == "progress":
                        elapsed = time.monotonic() - started
                        try:
                            encoded = max(0.0, float(data.get("out_time_us", 0)) / 1_000_000)
                            fraction = (pass_index + min(encoded / duration, 1)) / pass_count
                            progress({"percent": min(99, fraction * 100), "fps": data.get("fps", "—"),
                                "speed": data.get("speed", "—"), "elapsed": elapsed,
                                "eta": elapsed / fraction - elapsed if fraction > 0.001 else None,
                                "size": int(data.get("total_size", "0")) if data.get("total_size", "0").isdigit() else 0})
                        except (ValueError, ZeroDivisionError):
                            pass
                code = process.wait(timeout=10)
                if self.cancel_event.is_set():
                    raise Cancelled()
                if code:
                    errors.flush()
                    errors.seek(max(0, errors.tell() - 16000))
                    detail = errors.read()
                    logging.error("FFmpeg exit %s: %s", code, detail)
                    if "No space left" in detail:
                        raise ValueError("The output drive is full. Free some space and try again.")
                    raise ValueError("FFmpeg could not compress this video. Try CPU encoding or another codec. Technical details are in logs/compressly.log.")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                reader.join(timeout=2)
                process.stdout.close()
                process.stdin.close()
