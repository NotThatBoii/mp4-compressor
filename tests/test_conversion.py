"""Real container/codec conversions, stream-copy fidelity and safe cancellation."""
import hashlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.core.conversion import ConversionOptions, FORMATS, plan_conversion
from app.core.compression_engine import CompressionEngine, Cancelled, EncoderFailure
from app.core.ffmpeg_manager import FFmpegManager, run_tool
from app.core.media_probe import probe_media


class ConversionPlanningTests(unittest.TestCase):
    def test_audio_and_video_are_planned_independently(self):
        media = SimpleNamespace(video_codec="h264", audio_codec="opus", audio={"index": 1}, hdr=False, subtitles=())
        plan = plan_conversion(media, ConversionOptions("mp4"))
        self.assertEqual((plan.video_encoder, plan.audio_encoder), ("copy", "aac"))
        with self.assertRaisesRegex(ValueError, "cannot be copied"):
            plan_conversion(media, ConversionOptions("mp4", "Stream copy only"))
        self.assertTrue(plan_conversion(media, ConversionOptions("mp4", "Stream copy only", keep_audio=False)).lossless)

    def test_invalid_options_and_hdr_are_rejected(self):
        for options in (ConversionOptions("unknown"), ConversionOptions(method="unknown"), ConversionOptions(keep_subtitles=True)):
            with self.assertRaises(ValueError):
                options.validate()
        with self.assertRaisesRegex(ValueError, "HDR"):
            plan_conversion(SimpleNamespace(hdr=True), ConversionOptions())


@unittest.skipUnless(os.environ.get("COMPRESSLY_INTEGRATION") == "1", "Set COMPRESSLY_INTEGRATION=1")
class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = FFmpegManager()
        cls.temp = tempfile.TemporaryDirectory(prefix="compressly conversion ")
        cls.root = Path(cls.temp.name)
        cls.source = cls.root / "original with spaces.mp4"
        run_tool([cls.manager.ffmpeg, "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "2",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-metadata", "title=Private title", str(cls.source)])
        cls.media = probe_media(cls.manager, cls.source)
        cls.original_hash = hashlib.sha256(cls.source.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def tearDown(self):
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash)
        self.assertFalse(list(self.root.glob(".compressly-*")))

    def convert(self, options, media=None):
        result = CompressionEngine(self.manager).run(media or self.media, options, self.root)
        output = probe_media(self.manager, result.path)
        self.assertAlmostEqual(output.duration, self.media.duration, delta=0.3)
        self.assertEqual(result.operation, "conversion")
        self.assertIn("_converted", result.path.name)
        # Probe alone cannot prove the file decodes. Decode every produced frame.
        run_tool([self.manager.ffmpeg, "-v", "error", "-xerror", "-i", str(result.path), "-f", "null", "-"], timeout=60)
        return result, output

    def test_all_output_formats_auto_and_reencode(self):
        for method in ("Auto", "Re-encode"):
            for extension in FORMATS:
                with self.subTest(method=method, format=extension):
                    result, output = self.convert(ConversionOptions(extension, method))
                    self.assertEqual(result.path.suffix, "." + extension)
                    self.assertIsNotNone(output.audio)
                    self.assertEqual((output.width, output.height), (320, 180))
                    if extension == "m4v":
                        self.assertEqual(output.video_codec, "h264")

    def test_mov_mp4_roundtrip_copies_original_frames(self):
        first, mov = self.convert(ConversionOptions("mov", "Stream copy only"))
        second, _ = self.convert(ConversionOptions("mp4", "Stream copy only"), mov)
        def frames(path):
            return run_tool([self.manager.ffmpeg, "-v", "error", "-i", str(path), "-map", "0:v:0", "-f", "hash", "-"]).stdout.strip()
        self.assertEqual(frames(self.source), frames(first.path))
        self.assertEqual(frames(self.source), frames(second.path))

    def test_remove_audio_metadata_and_preserve_existing_output(self):
        options = ConversionOptions("mov", keep_audio=False, keep_metadata=False)
        first, output = self.convert(options)
        digest = hashlib.sha256(first.path.read_bytes()).digest()
        second, _ = self.convert(options)
        self.assertNotEqual(first.path, second.path)
        self.assertEqual(hashlib.sha256(first.path.read_bytes()).digest(), digest)
        self.assertIsNone(output.audio)
        data = run_tool([self.manager.ffprobe, "-v", "error", "-show_format", "-of", "json", str(first.path)]).stdout
        self.assertNotIn("Private title", data)

    def test_subtitles_and_strict_copy(self):
        subtitle = self.root / "captions.srt"
        subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello converter\n", encoding="utf-8")
        source = self.root / "subtitled.mp4"
        run_tool([self.manager.ffmpeg, "-y", "-i", str(self.source), "-i", str(subtitle),
            "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text", str(source)])
        media = probe_media(self.manager, source)
        _, output = self.convert(ConversionOptions("mkv", keep_subtitles=True), media)
        self.assertEqual(output.subtitles[0]["codec_name"], "subrip")
        with self.assertRaisesRegex(ValueError, "timed-text"):
            plan_conversion(media, ConversionOptions("mkv", "Stream copy only", keep_subtitles=True))
        with self.assertRaisesRegex(ValueError, "cannot be copied"):
            self.convert(ConversionOptions("webm", "Stream copy only"))

    def test_cancel_copy_and_reencode_clean_up(self):
        for method in ("Auto", "Re-encode"):
            before = set(self.root.iterdir())
            engine = CompressionEngine(self.manager)
            with self.assertRaises(Cancelled):
                engine.run(self.media, ConversionOptions("mov", method), self.root, lambda data: engine.cancel())
            self.assertEqual(set(self.root.iterdir()), before)

    def test_auto_retries_failed_copy_once_and_strict_copy_does_not(self):
        engine = CompressionEngine(self.manager)
        execute = engine._execute
        calls = []
        def fail_copy(args, *rest):
            calls.append(args)
            if len(calls) == 1:
                raise EncoderFailure("Simulated incompatible codec tag")
            return execute(args, *rest)
        with patch.object(engine, "_execute", side_effect=fail_copy):
            result = engine.run(self.media, ConversionOptions("mov"), self.root)
        self.assertEqual(len(calls), 2)
        self.assertIn("libx264", calls[1])
        self.assertTrue(result.path.is_file())
        with patch.object(engine, "_execute", side_effect=EncoderFailure("Cannot remux")) as execute:
            with self.assertRaises(EncoderFailure):
                engine.run(self.media, ConversionOptions("mov", "Stream copy only"), self.root)
            self.assertEqual(execute.call_count, 1)
