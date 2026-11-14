# MN24 4D/5D VideoGame Studio

## Objective
A playable Godot 4 prototype for 4D and 5D hypercube exploration, with a separate MP4 capture/export workflow. MP4 is a video container, not an executable game format.

## Playable project
Open examples/mn24_4d5d_game/project.godot with Godot 4.

- 4D mode: tesseract, 16 vertices and 32 edges.
- 5D mode: penteract, 32 vertices and 80 edges.
- Rotation planes include XW/YW/ZW and, in 5D, XV/YV/ZV/WV.
- Projection pipeline: 5D → 4D → 3D → 2D screen rendering.
- Three energy cores form a simple collection objective.
- Keyboard: WASD move, Space/Ctrl vertical movement, E collect, R pause/resume rotation, 4/5 switch dimension, Home reset position.

## MP4 production
- Existing integrations/video_recorder/recorder.py encodes RGB24 frames to H.264 MP4 via FFmpeg.
- That adapter captures Pygame surfaces only; it cannot directly capture a Godot viewport.
- For the Godot game, capture the running game window using the OS/platform screen recorder or a platform-appropriate FFmpeg capture input, then encode to MP4. On Android, use the Android screen recorder; transfer the resulting video to the project's exports/ folder if desired.
- For Pygame-based games, call MN24VideoRecorder.capture(screen) after each rendered frame.
- Current recorder is video-only; synchronized game audio and microphone narration need a separate audio capture/mux stage.

## Termux / Linux workflow
```bash
cd ~/HOLOOS
git pull --ff-only origin feat/android24creator-github-integration
pkg update
pkg install ffmpeg
```
Godot editor/runtime availability depends on the device architecture and installation method. Open the project in Godot 4 on PC or a compatible Android Godot editor/runtime. Do not assume the desktop editor is installed in Termux.

## MP4 encode example
When a screen recording exists, convert it to a broadly compatible MP4:
```bash
ffmpeg -i screen-recording.mkv -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 160k exports/MN24_4D5D_GAME.mp4
```
Create exports/ first. Input filename is an example; replace it with the actual capture file.

## Status
- IMPLEMENTED: Godot 4 4D/5D exploration prototype, geometry generation, dimensional rotations, perspective projection, movement, collectible objective and HUD.
- IMPLEMENTED: Existing Python/Pygame RGB24 → FFmpeg H.264/MP4 recorder.
- PENDING: Import/run validation in Godot 4 on PC and Android.
- PENDING: Device-specific screen capture and MP4 playback tests.
- PENDING: Audio synchronization/muxing and touch/gamepad controls.
- No APK export, native Android clipboard, or device validation is claimed by this addition.


## Direct playable Pygame + MP4 build

A Pygame implementation is included for a direct capture path that uses the existing FFmpeg recorder:

```bash
cd ~/HOLOOS
python -m pip install pygame
pkg install ffmpeg
python examples/mn24_4d5d_game/playable_mp4.py
```

Press R to start/stop recording. The output is written to exports/MN24_4D5D_GAME.mp4. Press 4 or 5 to switch between 4D and 5D. The Pygame build records video without game audio. The Godot build is the native 3D-engine prototype; use platform screen capture for its MP4 recording.
