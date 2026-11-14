import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from integrations.video_recorder.recorder import MN24VideoRecorder


class RecorderValidationTests(unittest.TestCase):
    def test_rejects_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            MN24VideoRecorder(width=0)

    def test_rejects_invalid_fps(self):
        with self.assertRaises(ValueError):
            MN24VideoRecorder(fps=0)

    def test_rejects_invalid_crf(self):
        with self.assertRaises(ValueError):
            MN24VideoRecorder(crf=52)

    def test_frame_size_must_match_rgb24_dimensions(self):
        recorder = MN24VideoRecorder(width=2, height=2)
        recorder.process = MagicMock()
        recorder.process.stdin = io.BytesIO()
        recorder.process.poll.return_value = None
        with self.assertRaises(ValueError):
            recorder.write_rgb_frame(b"too short")

    @patch("integrations.video_recorder.recorder.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("integrations.video_recorder.recorder.subprocess.Popen")
    def test_writes_frame_and_stops(self, popen, _which):
        process = MagicMock()
        process.stdin = io.BytesIO()
        process.poll.return_value = None
        process.wait.return_value = 0
        popen.return_value = process

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "game.mp4"
            recorder = MN24VideoRecorder(width=2, height=2, output=output)
            recorder.start()
            recorder.write_rgb_frame(bytes(2 * 2 * 3))
            self.assertEqual(recorder.frames_written, 1)
            self.assertEqual(recorder.stop(), output)
            process.wait.assert_called_once()


if __name__ == "__main__":
    unittest.main()
