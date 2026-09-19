"""Exercise real Qt worker signals and cancellation when integration tests are enabled."""
import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest


@unittest.skipUnless(os.environ.get("COMPRESSLY_INTEGRATION") == "1" and importlib.util.find_spec("PySide6"),
                     "Requires PySide6 and COMPRESSLY_INTEGRATION=1")
class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        from app.core.ffmpeg_manager import FFmpegManager, run_tool
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)
        cls.temp = tempfile.TemporaryDirectory(prefix="compressly gui ")
        cls.root = Path(cls.temp.name)
        cls.source = cls.root / "gui sample.mp4"
        manager = FFmpegManager()
        run_tool([manager.ffmpeg, "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
                  "-t", "8", "-c:v", "libx264", "-preset", "ultrafast", str(cls.source)])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def wait_for(self, predicate, timeout=60):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            time.sleep(0.01)
        self.fail("Timed out waiting for GUI operation")

    def setUp(self):
        from app.main_window import MainWindow

        class CheckedWindow(MainWindow):
            def show_error(self, message):
                self.errors.append(message)

        self.window = CheckedWindow()
        self.window.errors = []
        self.window.show()
        self.wait_for(lambda: self.window.task is None and self.window.manager is not None)
        self.window.drop.accept_path(str(self.source))
        self.wait_for(lambda: self.window.task is None and self.window.media is not None)
        self.window.settings.encoder.setCurrentText("CPU")

    def tearDown(self):
        self.window.close()
        self.wait_for(lambda: self.window.job is None and self.window.task is None)
        self.app.processEvents()
        self.window.deleteLater()
        self.app.processEvents()

    def test_compress_keeps_ui_responsive(self):
        from PySide6.QtCore import QTimer
        ticks = []
        timer = QTimer()
        timer.timeout.connect(lambda: ticks.append(1))
        timer.start(10)
        self.window.start.click()
        self.assertFalse(self.window.settings.isEnabled())
        self.wait_for(lambda: self.window.job is None)
        timer.stop()
        self.assertFalse(self.window.errors)
        self.assertGreater(len(ticks), 5)
        self.assertEqual(self.window.progress.bar.value(), 100)
        self.assertTrue(self.window.last_output.is_file())
        self.assertTrue(self.window.start.isEnabled())

    def test_close_cancels_then_exits(self):
        self.window.start.click()
        self.window.close()
        self.wait_for(lambda: self.window.job is None and not self.window.isVisible())
        self.assertFalse(self.window.errors)
        self.assertFalse(list(self.root.glob(".compressly-*")))

    def test_conversion_mode_and_mov_output(self):
        self.window.operation.setCurrentText("Convert")
        self.window.conversion.format.setCurrentIndex(self.window.conversion.format.findData("mov"))
        self.assertTrue(self.window.conversion.isVisible())
        self.assertFalse(self.window.settings.isVisible())
        self.assertEqual(self.window.start.text(), "Convert Video")
        self.assertIn("copy original", self.window.conversion.plan.text())
        self.window.conversion.method.setCurrentText("Re-encode")
        self.assertIn("re-encode (libx264)", self.window.conversion.plan.text())
        self.window.conversion.method.setCurrentText("Auto")
        self.window.start.click()
        self.assertFalse(self.window.operation.isEnabled())
        self.assertFalse(self.window.conversion.isEnabled())
        self.wait_for(lambda: self.window.job is None)
        self.assertFalse(self.window.errors)
        self.assertEqual(self.window.last_output.suffix, ".mov")
        self.assertIn("Conversion complete", self.window.progress.status.text())
        self.assertTrue(self.window.operation.isEnabled())
        self.window.operation.setCurrentText("Compress")
        self.assertTrue(self.window.settings.isVisible())
        self.assertEqual(self.window.start.text(), "Compress Video")

    def test_unlisted_extension_is_probed_and_subtitle_option_resets(self):
        import shutil
        unusual = self.root / "video.unlisted"
        shutil.copyfile(self.source, unusual)
        self.window.drop.accept_path(str(unusual))
        self.wait_for(lambda: self.window.task is None and self.window.media is not None)
        self.assertTrue(self.window.media.path.samefile(unusual))
        box = self.window.conversion.format
        box.setCurrentIndex(box.findData("mkv"))
        self.window.conversion.subtitles.setChecked(True)
        box.setCurrentIndex(box.findData("mp4"))
        self.assertFalse(self.window.conversion.options().keep_subtitles)


if __name__ == "__main__":
    unittest.main()
