"""Test encoders at runtime: an FFmpeg listing alone does not prove GPU support."""
import logging
import os
import subprocess
import time

from app.core.ffmpeg_manager import CREATE_FLAGS, run_tool

CPU_ENCODERS = {"h264": "libx264", "hevc": "libx265", "av1": "libsvtav1"}
VENDORS = {"NVIDIA": "nvenc", "Intel": "qsv", "AMD": "amf"}
CRF = {"h264": [19, 23, 27], "hevc": [22, 26, 30], "av1": [24, 32, 40]}


def rate_control(options, encoder, video_bps=None):
    if video_bps is not None:
        # Hardware does not expose traditional x264/x265 two-pass analysis.
        # Use average-bitrate VBR; SVT-AV1 also uses a single-pass bitrate target here.
        if encoder.endswith("_nvenc"):
            return ["-preset", "p5", "-rc", "vbr", "-b:v", str(video_bps)]
        if encoder.endswith("_amf"):
            return ["-rc", "vbr_peak", "-b:v", str(video_bps), "-maxrate", str(video_bps * 2)]
        if encoder.endswith("_qsv"):
            return ["-preset", "medium", "-b:v", str(video_bps), "-maxrate", str(video_bps * 2)]
        return ["-preset", "6" if encoder == "libsvtav1" else "medium", "-b:v", str(video_bps)]
    index = ["High Quality", "Balanced", "Small File"].index(options.mode)
    quality = CRF[options.codec][index]
    if encoder.endswith("_nvenc"):
        return ["-preset", "p5", "-rc", "vbr", "-cq", str(quality), "-b:v", "0"]
    if encoder.endswith("_qsv"):
        return ["-preset", "medium", "-global_quality", str(quality)]
    if encoder.endswith("_amf"):
        return ["-rc", "cqp", "-qp_i", str(quality), "-qp_p", str(quality)]
    return ["-preset", "6" if encoder == "libsvtav1" else "medium", "-crf", str(quality)]


class EncoderDetector:
    def __init__(self, manager):
        self.manager = manager
        self._encoders = None
        self.cache = {}

    def available(self):
        if self._encoders is None:
            output = run_tool([self.manager.ffmpeg, "-hide_banner", "-encoders"], timeout=10).stdout
            self._encoders = {parts[1] for line in output.splitlines()
                              if len(parts := line.split()) > 1 and len(parts[0]) == 6 and parts[0].startswith("V")}
        return self._encoders

    def cpu(self, codec):
        encoder = CPU_ENCODERS[codec]
        if encoder not in self.available():
            raise ValueError(f"This FFmpeg build does not include {encoder}. Install a full FFmpeg build or choose another codec.")
        return encoder

    def usable(self, encoder, options, cancel_event):
        key = (encoder, options.mode)
        if key in self.cache:
            return self.cache[key]
        args = [self.manager.ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                "-i", "color=size=128x128:rate=30", "-frames:v", "6", "-an", "-c:v", encoder,
                "-pix_fmt", "yuv420p"]
        args += rate_control(options, encoder, 500000 if options.mode == "Target File Size" else None)
        args += ["-f", "null", os.devnull]
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            creationflags=CREATE_FLAGS)
        started = time.monotonic()
        try:
            while True:
                if cancel_event.is_set() or time.monotonic() - started > 10:
                    process.kill()
                    process.communicate()
                    return False
                try:
                    _, error = process.communicate(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    continue
            success = process.returncode == 0
            if not success:
                logging.info("Encoder %s unavailable: %s", encoder, error.decode("utf-8", "replace")[-2000:])
            self.cache[key] = success
            return success
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()

    def choose(self, options, cancel_event, status):
        if options.encoder != "CPU":
            vendors = VENDORS if options.encoder == "Auto" else [options.encoder]
            for vendor in vendors:
                if cancel_event.is_set():
                    break
                candidate = f"{options.codec}_{VENDORS[vendor]}"
                if candidate in self.available():
                    status(f"Checking {vendor} {options.codec.upper()} encoder…")
                    if self.usable(candidate, options, cancel_event):
                        return candidate
            status("Hardware encoder unavailable. Using CPU encoding.")
        return self.cpu(options.codec)
