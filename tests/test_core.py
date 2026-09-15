import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.core.bitrate_calculator import calculate_target_bitrate
from app.core.compression_engine import build_commands
from app.core.encoder_detector import EncoderDetector
from app.core.media_probe import MediaInfo, probe_media
from app.core.models import CompressionOptions
from app.utils.file_utils import output_path
from threading import Event


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.manager = SimpleNamespace(ffmpeg="ffmpeg", ffprobe="ffprobe")
        self.media = MediaInfo(Path("C:/videos/a file.mp4"), 5_000_000, 60, 1920, 1080,
                              30, "h264", "aac", 1_000_000, 0,
                              {"index": 1, "bit_rate": "96000"}, ())

    def test_budget_accounts_for_audio_and_overhead(self):
        budget = calculate_target_bitrate(500, 3600, 128, 1920, 1080, 30)
        self.assertEqual(budget.video_bps, 960888)
        self.assertLess((budget.video_bps + budget.audio_bps) * 3600 / 8, 500_000_000)

    def test_impossible_budget_rejected(self):
        with self.assertRaises(ValueError):
            calculate_target_bitrate(20, 7200, 128, 3840, 2160, 30)
        for target in (float("nan"), float("inf"), -1):
            with self.assertRaises(ValueError):
                calculate_target_bitrate(target, 60, 0, 640, 360, 30)

    def test_poor_quality_budget_warns(self):
        self.assertIsNotNone(calculate_target_bitrate(20, 7200, 0, 3840, 2160, 30).warning)

    def test_unique_names_never_replace_source(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "video.mp4"
            source.write_bytes(b"original")
            first = output_path(source, folder)
            self.assertEqual(first.name, "video_compressed.mp4")
            first.write_bytes(b"existing")
            self.assertEqual(output_path(source, folder).name, "video_compressed_2.mp4")
            self.assertEqual(source.read_bytes(), b"original")

    def test_two_pass_commands_are_codec_specific(self):
        options = CompressionOptions(mode="Target File Size", encoder="CPU", target_mb=5)
        for encoder in ("libx264", "libx265"):
            commands = build_commands(self.manager, self.media, options, encoder, Path("output.mp4"))
            self.assertEqual(len(commands), 2)
            self.assertIn("null", commands[0])
            self.assertIn("-an", commands[0])
            self.assertNotIn("-crf", commands[1])
            self.assertIn("pass=2:stats=passlog" if encoder == "libx265" else "-pass", commands[1])
            self.assertEqual(commands[1][-1], "output.mp4")

    def test_audio_copy_and_paths_with_spaces(self):
        args = build_commands(self.manager, self.media, CompressionOptions(), "libx265", Path("out file.mp4"))[0]
        self.assertEqual(args[args.index("-i") + 1], str(self.media.path))
        self.assertEqual(args[args.index("-c:a") + 1], "copy")
        args = build_commands(self.manager, self.media, CompressionOptions(audio_kbps=0), "libx265", Path("out.mp4"))[0]
        self.assertIn("-an", args)
        self.assertNotIn("-c:a", args)

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            CompressionOptions(resolution=(1919, 1080)).validate()

    def test_probe_ignores_cover_art_and_handles_rotation(self):
        data = {"format": {"duration": "10", "bit_rate": "800000"}, "streams": [
            {"index": 0, "codec_type": "video", "disposition": {"attached_pic": 1}},
            {"index": 1, "codec_type": "video", "width": 1920, "height": 1080,
             "avg_frame_rate": "30000/1001", "codec_name": "h264", "side_data_list": [{"rotation": -90}]}]}
        with TemporaryDirectory() as folder:
            path = Path(folder) / "input.mp4"
            path.write_bytes(b"fixture")
            with patch("app.core.media_probe.run_tool", return_value=SimpleNamespace(stdout=json.dumps(data))):
                info = probe_media(self.manager, path)
            self.assertEqual((info.width, info.height), (1080, 1920))
            self.assertEqual(info.video_index, 1)
            self.assertAlmostEqual(info.fps, 29.970, places=3)

    def test_hardware_listing_requires_runtime_check(self):
        detector = EncoderDetector(self.manager)
        detector._encoders = {"hevc_nvenc", "libx265"}
        with patch.object(detector, "usable", return_value=False) as check:
            chosen = detector.choose(CompressionOptions(), Event(), lambda message: None)
        self.assertEqual(chosen, "libx265")
        check.assert_called_once()


if __name__ == "__main__":
    unittest.main()
