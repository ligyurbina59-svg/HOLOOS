"""Pygame Surface -> FFmpeg MP4 recorder.

This module deliberately does not import Pygame at import time. Pygame is only
needed by capture(); write_rgb_frame() can be used by other render adapters.
"""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from typing import Any


class MN24VideoRecorder:
    """Encode fixed-size RGB frames into an H.264 MP4 file."""

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        output: str | Path = "output.mp4",
        ffmpeg_bin: str = "ffmpeg",
        preset: str = "veryfast",
        crf: int = 20,
        overwrite: bool = True,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if not math.isfinite(float(fps)) or fps <= 0:
            raise ValueError("fps must be a positive finite number")
        if not 0 <= crf <= 51:
            raise ValueError("crf must be between 0 and 51")
        if not preset or preset.startswith("-"):
            raise ValueError("invalid FFmpeg preset")

        self.width = int(width)
        self.height = int(height)
        self.fps = float(fps)
        self.output = Path(output)
        self.ffmpeg_bin = ffmpeg_bin
        self.preset = preset
        self.crf = int(crf)
        self.overwrite = overwrite
        self.process: subprocess.Popen[bytes] | None = None
        self.frames_written = 0

    @property
    def recording(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def _command(self) -> list[str]:
        overwrite_flag = "-y" if self.overwrite else "-n"
        return [
            self.ffmpeg_bin,
            "-hide_banner",
            "-loglevel", "error",
            overwrite_flag,
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{self.width}x{self.height}",
            "-framerate", str(self.fps),
            "-i", "pipe:0",
            "-an",
            "-c:v", "libx264",
            "-preset", self.preset,
            "-crf", str(self.crf),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(self.output),
        ]

    def start(self) -> None:
        if self.process is not None:
            raise RuntimeError("recorder has already been started")
        executable = shutil.which(self.ffmpeg_bin)
        if executable is None:
            raise RuntimeError(f"FFmpeg executable not found: {self.ffmpeg_bin}")
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen(
            self._command(),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
        self.frames_written = 0

    def write_rgb_frame(self, frame: bytes | bytearray | memoryview) -> None:
        """Write one tightly packed RGB24 frame of exactly width*height*3 bytes."""
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("recorder is not started")
        if self.process.poll() is not None:
            raise RuntimeError("FFmpeg exited before the frame was written")

        expected = self.width * self.height * 3
        view = memoryview(frame)
        if view.nbytes != expected:
            raise ValueError(f"frame must contain {expected} RGB bytes; got {view.nbytes}")

        try:
            self.process.stdin.write(view)
        except (BrokenPipeError, OSError) as exc:
            raise RuntimeError("failed to send frame to FFmpeg") from exc
        self.frames_written += 1

    def capture(self, surface: Any) -> None:
        """Capture a Pygame Surface after it has been rendered."""
        try:
            import pygame
        except ImportError as exc:
            raise RuntimeError("Pygame is required for capture(surface)") from exc

        if surface.get_size() != (self.width, self.height):
            raise ValueError(
                f"surface size must be {(self.width, self.height)}, got {surface.get_size()}"
            )
        self.write_rgb_frame(pygame.image.tostring(surface, "RGB"))

    def stop(self, timeout: float = 30.0) -> Path:
        if self.process is None:
            return self.output

        process = self.process
        self.process = None
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()

        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                return_code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                return_code = process.wait()

        if return_code != 0:
            raise RuntimeError(f"FFmpeg failed with exit code {return_code}")
        return self.output

    def __enter__(self) -> "MN24VideoRecorder":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.stop()
