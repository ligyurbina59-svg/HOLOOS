"""MN24 playable 4D/5D hypercube game with direct MP4 recording.

Controls: 4/5 switch dimension, WASD move the projection focus, arrows rotate,
R start/stop MP4 recording, ESC quit. Requires pygame and FFmpeg.
"""
from __future__ import annotations

import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame
from integrations.video_recorder import MN24VideoRecorder

WIDTH, HEIGHT, FPS = 1280, 720, 30
BG = (5, 12, 30)
CYAN = (55, 210, 255)
GOLD = (255, 180, 45)
WHITE = (225, 240, 255)


def make_hypercube(dimension: int):
    vertices = [
        [1.0 if (i & (1 << axis)) else -1.0 for axis in range(dimension)]
        for i in range(1 << dimension)
    ]
    edges = []
    for i in range(1 << dimension):
        for axis in range(dimension):
            bit = 1 << axis
            if not i & bit:
                edges.append((i, i | bit))
    return vertices, edges


def rotate_plane(point, a, b, angle):
    result = point.copy()
    c, s = math.cos(angle), math.sin(angle)
    result[a] = point[a] * c - point[b] * s
    result[b] = point[a] * s + point[b] * c
    return result


def project(point, dimension, angles, center):
    p = point.copy()
    planes = [(0, 3), (1, 3), (2, 3)]
    if dimension == 5:
        planes += [(0, 4), (1, 4), (2, 4), (3, 4)]
    for a, b in planes:
        p = rotate_plane(p, a, b, angles.get((a, b), 0.0))
    if dimension == 5:
        factor5 = 4.0 / max(0.25, 4.0 - p[4])
        p[:4] = [v * factor5 for v in p[:4]]
    factor4 = 4.0 / max(0.25, 4.0 - p[3])
    x = p[0] * factor4 * 2.2
    y = p[1] * factor4 * 2.2
    z = p[2] * factor4
    focal = 10.0 / max(1.0, 10.0 - z)
    return (int(WIDTH / 2 + (x - center[0]) * 95 * focal),
            int(HEIGHT / 2 - (y - center[1]) * 95 * focal))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MN24 4D/5D VideoGame Studio")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)
    small = pygame.font.Font(None, 23)
    dimension = 4
    vertices, edges = make_hypercube(dimension)
    angles = {}
    center = [0.0, 0.0]
    rotating = True
    recorder = None
    recording = False
    output = ROOT / "exports" / "MN24_4D5D_GAME.mp4"
    running = True
    status = "Explora el hipercubo. Pulsa R para grabar MP4."
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_4, pygame.K_5):
                    dimension = 4 if event.key == pygame.K_4 else 5
                    vertices, edges = make_hypercube(dimension)
                    angles.clear()
                    status = f"Modo {dimension}D: {len(vertices)} vértices, {len(edges)} aristas."
                elif event.key == pygame.K_r:
                    if not recording:
                        try:
                            recorder = MN24VideoRecorder(WIDTH, HEIGHT, FPS, output)
                            recorder.start()
                            recording = True
                            status = f"Grabando: {output}"
                        except Exception as exc:
                            recorder = None
                            status = f"No se pudo iniciar FFmpeg: {exc}"
                    else:
                        try:
                            saved = recorder.stop() if recorder else output
                            status = f"MP4 guardado: {saved}"
                        except Exception as exc:
                            status = f"Error al finalizar MP4: {exc}"
                        recorder = None
                        recording = False
                elif event.key == pygame.K_SPACE:
                    rotating = not rotating

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: angles[(0, 3)] = angles.get((0, 3), 0.0) - dt
        if keys[pygame.K_RIGHT]: angles[(0, 3)] = angles.get((0, 3), 0.0) + dt
        if keys[pygame.K_UP]: angles[(1, 3)] = angles.get((1, 3), 0.0) - dt
        if keys[pygame.K_DOWN]: angles[(1, 3)] = angles.get((1, 3), 0.0) + dt
        if keys[pygame.K_a]: center[0] -= dt * 1.5
        if keys[pygame.K_d]: center[0] += dt * 1.5
        if keys[pygame.K_w]: center[1] += dt * 1.5
        if keys[pygame.K_s]: center[1] -= dt * 1.5
        if rotating:
            for plane in ([(2, 3)] if dimension == 4 else [(2, 3), (0, 4), (1, 4), (2, 4), (3, 4)]):
                angles[plane] = angles.get(plane, 0.0) + dt * 0.35

        screen.fill(BG)
        projected = [project(v, dimension, angles, center) for v in vertices]
        for a, b in edges:
            pygame.draw.line(screen, CYAN, projected[a], projected[b], 2)
        for point in projected:
            pygame.draw.circle(screen, WHITE, point, 4)
        title = font.render(f"MN24 HYPERDIMENSIONAL GAME  |  {dimension}D", True, WHITE)
        screen.blit(title, (24, 20))
        stats = small.render(f"{len(vertices)} vertices  |  {len(edges)} edges  |  FPS {clock.get_fps():.0f}", True, CYAN)
        screen.blit(stats, (24, 58))
        help_text = small.render("4/5 dimension  |  WASD move  |  Arrows rotate  |  SPACE auto-rotate  |  R record MP4  |  ESC exit", True, WHITE)
        screen.blit(help_text, (24, HEIGHT - 42))
        color = GOLD if recording else (160, 190, 215)
        screen.blit(small.render(("● REC  " if recording else "") + status[:105], True, color), (24, 92))
        pygame.display.flip()
        if recording and recorder:
            try:
                recorder.capture(screen)
            except Exception as exc:
                status = f"Grabación detenida: {exc}"
                try:
                    recorder.stop()
                except Exception:
                    pass
                recorder = None
                recording = False
    if recorder:
        try:
            recorder.stop()
        except Exception as exc:
            print(f"FFmpeg shutdown error: {exc}", file=sys.stderr)
    pygame.quit()


if __name__ == "__main__":
    main()
