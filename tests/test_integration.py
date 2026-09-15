"""Real FFmpeg integration tests. Run with COMPRESSLY_INTEGRATION=1."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from app.core.ffmpeg_manager import FFmpegManager, run_tool
from app.core.compression_engine import CompressionEngine, Cancelled
from app.core.media_probe import probe_media
from app.core.models import CompressionOptions


@unittest.skipUnless(os.environ.get("COMPRESSLY_INTEGRATION") == "1", "Set COMPRESSLY_INTEGRATION=1 to run FFmpeg tests")
class FFmpegTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = FFmpegManager()
        cls.temp = tempfile.TemporaryDirectory(prefix="compressly tests ")
        cls.root = Path(cls.temp.name)
        cls.source = cls.root / "source with spaces.mp4"
        run_tool([cls.manager.ffmpeg, "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "12",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12", "-c:a", "aac",
            "-b:a", "96k", "-metadata", "title=Private sample title", str(cls.source)], timeout=60)
        cls.info = probe_media(cls.manager, cls.source)
        cls.original_hash = hashlib.sha256(cls.source.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def tearDown(self):
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash)
        self.assertFalse(list(self.root.glob(".compressly-*")))

    def encode(self, options):
        progress, statuses = [], []
        result = CompressionEngine(self.manager).run(self.info, options, self.root, progress.append, statuses.append)
        output = probe_media(self.manager, result.path)
        self.assertAlmostEqual(output.duration, self.info.duration, delta=0.2)
        self.assertTrue(progress)
        self.assertTrue(all(0 <= p["percent"] <= 99 for p in progress))
        return result, output, statuses

    def test_h265_crf_resize_audio_and_metadata(self):
        result, output, _ = self.encode(CompressionOptions(encoder="CPU", resolution=(320, 180), fps=24, audio_kbps=0, keep_metadata=False))
        self.assertEqual((output.width, output.height), (320, 180))
        self.assertEqual(output.fps, 24)
        self.assertEqual(output.video_codec, "hevc")
        self.assertIsNone(output.audio)
        self.assertLess(result.size, self.info.size)
        data = run_tool([self.manager.ffprobe, "-v", "error", "-show_format", "-of", "json", str(result.path)]).stdout
        self.assertNotIn("Private sample title", data)

    def test_h264_and_h265_two_pass(self):
        for codec in ("h264", "hevc"):
            with self.subTest(codec=codec):
                result, _, statuses = self.encode(CompressionOptions(codec=codec, encoder="CPU", mode="Target File Size", target_mb=1))
                self.assertTrue(any("pass 2/2" in s for s in statuses))
                self.assertLess(abs(result.size - 1_000_000) / 1_000_000, 0.20)
                print(f"\n{codec} target 1 MB -> {result.size / 1_000_000:.3f} MB", flush=True)

    def test_av1_if_available(self):
        engine = CompressionEngine(self.manager)
        if "libsvtav1" not in engine.detector.available():
            self.skipTest("This FFmpeg build has no SVT-AV1")
        _, output, _ = self.encode(CompressionOptions(codec="av1", encoder="CPU", resolution=(320, 180)))
        self.assertEqual(output.video_codec, "av1")

    def test_cancel_cleans_output(self):
        before = set(self.root.iterdir())
        engine = CompressionEngine(self.manager)
        with self.assertRaises(Cancelled):
            engine.run(self.info, CompressionOptions(encoder="CPU"), self.root, lambda data: engine.cancel())
        self.assertEqual(set(self.root.iterdir()), before)

    def test_auto_encoder_and_fallback(self):
        result, output, _ = self.encode(CompressionOptions(codec="h264", encoder="Auto", resolution=(320, 180)))
        self.assertEqual(output.video_codec, "h264")
        print(f"\nAuto selected {result.encoder}", flush=True)

    def test_default_hevc_auto_and_hardware_target(self):
        for mode in ("Balanced", "Target File Size"):
            with self.subTest(mode=mode):
                result, output, _ = self.encode(CompressionOptions(mode=mode, target_mb=1, resolution=(320, 180)))
                self.assertEqual(output.video_codec, "hevc")
                print(f"\nHEVC {mode}: {result.encoder}, {result.size / 1_000_000:.3f} MB", flush=True)

    def test_subtitle_preservation(self):
        subtitle = self.root / "captions.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:03,000\nHello Compressly\n", encoding="utf-8")
        source = self.root / "subtitled.mkv"
        run_tool([self.manager.ffmpeg, "-y", "-i", str(self.source), "-i", str(subtitle),
                  "-map", "0", "-map", "1", "-c", "copy", str(source)])
        info = probe_media(self.manager, source)
        result = CompressionEngine(self.manager).run(info, CompressionOptions(codec="h264", encoder="CPU", keep_subtitles=True), self.root)
        output = probe_media(self.manager, result.path)
        self.assertEqual(result.path.suffix, ".mkv")
        self.assertEqual(output.subtitles[0]["codec_name"], "subrip")

    def test_mp4_timed_text_becomes_mkv_srt(self):
        subtitle = self.root / "timed text.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:03,000\nHello timed text\n", encoding="utf-8")
        source = self.root / "timed text.mp4"
        run_tool([self.manager.ffmpeg, "-y", "-i", str(self.source), "-i", str(subtitle),
                  "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text", str(source)])
        result = CompressionEngine(self.manager).run(probe_media(self.manager, source),
            CompressionOptions(codec="h264", encoder="CPU", keep_subtitles=True), self.root)
        output = probe_media(self.manager, result.path)
        self.assertEqual(output.subtitles[0]["codec_name"], "subrip")

    def test_invalid_output_and_corrupt_source(self):
        with self.assertRaises(ValueError):
            CompressionEngine(self.manager).run(self.info, CompressionOptions(), self.root / "absent")
        corrupt = self.root / "corrupt.mp4"
        corrupt.write_bytes(b"not a video")
        with self.assertRaises(Exception):
            probe_media(self.manager, corrupt)


if __name__ == "__main__":
    unittest.main()
