# MN24 VIDEO GAME MP4 STUDIO

## Purpose

Provide a reusable FFmpeg H.264/MP4 recorder for Pygame-rendered frames and document the correct capture path for the other HOLOOS game runtimes.

## Implemented

- `integrations/video_recorder/recorder.py`: Pygame Surface to RGB24 frames to FFmpeg/libx264 MP4.
- Validates dimensions, frame rate, CRF and exact RGB frame byte count.
- Checks FFmpeg availability, detects broken pipes, closes stdin, waits for encoder completion and terminates a stuck process.
- `examples/tesseract_4d/`: standalone Godot 4 project that generates 16 tesseract vertices, 32 edges, rotates in XW/YW/ZW and projects 4D to 3D.
- Unit tests mock FFmpeg; they do not require an installed encoder.

## Runtime separation

The Pygame recorder only captures Pygame Surface objects. It does not capture a Godot viewport or a browser iframe.

- **Pygame:** call `recorder.capture(screen)` after rendering and before the next frame.
- **Godot 4D:** open `examples/tesseract_4d/project.godot` in Godot 4 and use Godot's platform-specific display/screen recording for the running scene. Do not pass a Godot viewport to the Pygame adapter.
- **Cebolla HTML5 games:** run the game in the browser and use Android's system screen recorder or a desktop capture source. The current iframe is intentionally sandboxed; the parent page cannot freely read its canvas.
- **Audio:** this Pygame adapter is video-only (`-an`). Audio mixing and synchronized game audio are a separate pipeline.

## Termux setup

From the HOLOOS repository root:

```bash
pkg update
pkg install python ffmpeg
python -m pip install pygame
python -m unittest tests.test_video_recorder -v
```

NumPy is not required by this recorder. The recorder uses `pygame.image.tostring(surface, "RGB")`.

## Pygame integration

```python
import pygame
from integrations.video_recorder import MN24VideoRecorder

pygame.init()
size = (1280, 720)
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()

recorder = MN24VideoRecorder(*size, fps=30, output="exports/MN24_GAME.mp4")
recorder.start()
try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Render the complete game frame here.
        screen.fill((8, 12, 28))
        pygame.display.flip()
        recorder.capture(screen)
        clock.tick(30)
finally:
    recorder.stop()
    pygame.quit()
```

## Performance guidance

- Start at 1280x720 / 30 FPS on Android.
- 1920x1080 / 30 FPS RGB24 input is about 178 MiB/s before encoding.
- FFmpeg's stdin write is synchronous and can block when encoding is slower than rendering. Use a bounded producer/consumer queue only if asynchronous capture is later implemented; never allow an unbounded frame queue.
- Use a separate audio capture/mux stage if synchronized sound is required.
- H.264 `yuv420p` is broadly compatible, but verify the target device/browser.

## Verification status

- Code and unit tests are committed to the integration branch.
- FFmpeg encoding and MP4 playback require a local Termux/device test.
- Godot project import/run requires Godot 4 validation.
- Cebolla game capture requires a real browser/device recording test.
- No APK conversion, live stream, or audio capture is claimed.

## Safety

The recorder invokes FFmpeg with an argument list (not a shell command), does not execute game assets, and writes only to the configured output path. Keep generated recordings out of version control unless intentionally adding a sample.
