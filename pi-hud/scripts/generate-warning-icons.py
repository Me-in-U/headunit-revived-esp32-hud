#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assets" / "warning-icons"
SIZE = 128
RED = (238, 32, 36, 255)
AMBER = (255, 174, 0, 255)


def surface() -> pygame.Surface:
    return pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)


def save(name: str, icon: pygame.Surface) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pygame.image.save(icon, OUTPUT_DIR / f"{name}.png")


def draw_text(icon: pygame.Surface, text: str, color: tuple[int, int, int, int], size: int = 44) -> None:
    font = pygame.font.SysFont("Arial", size, bold=True)
    rendered = font.render(text, True, color)
    icon.blit(rendered, rendered.get_rect(center=(SIZE // 2, SIZE // 2)))


def door_open() -> pygame.Surface:
    icon = surface()
    pygame.draw.rect(icon, RED, pygame.Rect(42, 14, 44, 100), width=7, border_radius=10)
    pygame.draw.polygon(icon, RED, [(50, 34), (78, 34), (83, 50), (45, 50)])
    pygame.draw.polygon(icon, RED, [(46, 78), (82, 78), (77, 94), (51, 94)])
    pygame.draw.line(icon, RED, (42, 55), (18, 82), 8)
    pygame.draw.line(icon, RED, (42, 70), (18, 98), 8)
    pygame.draw.line(icon, RED, (86, 55), (110, 82), 8)
    pygame.draw.line(icon, RED, (86, 70), (110, 98), 8)
    pygame.draw.circle(icon, RED, (42, 63), 4)
    pygame.draw.circle(icon, RED, (86, 63), 4)
    return icon


def battery() -> pygame.Surface:
    icon = surface()
    pygame.draw.rect(icon, RED, pygame.Rect(22, 42, 78, 44), width=8, border_radius=5)
    pygame.draw.rect(icon, RED, pygame.Rect(100, 54, 10, 20), border_radius=3)
    pygame.draw.line(icon, RED, (42, 64), (58, 64), 7)
    pygame.draw.line(icon, RED, (78, 56), (78, 72), 7)
    pygame.draw.line(icon, RED, (70, 64), (86, 64), 7)
    return icon


def brake() -> pygame.Surface:
    icon = surface()
    pygame.draw.circle(icon, RED, (64, 64), 36, width=8)
    pygame.draw.arc(icon, RED, pygame.Rect(16, 24, 32, 80), 1.1, 5.2, 7)
    pygame.draw.arc(icon, RED, pygame.Rect(80, 24, 32, 80), -2.1, 2.0, 7)
    draw_text(icon, "!", RED, 48)
    return icon


def abs_icon() -> pygame.Surface:
    icon = surface()
    pygame.draw.circle(icon, AMBER, (64, 64), 40, width=7)
    draw_text(icon, "ABS", AMBER, 36)
    return icon


def airbag() -> pygame.Surface:
    icon = surface()
    pygame.draw.circle(icon, RED, (42, 42), 16, width=6)
    pygame.draw.line(icon, RED, (42, 58), (52, 88), 7)
    pygame.draw.line(icon, RED, (52, 88), (76, 88), 7)
    pygame.draw.circle(icon, RED, (86, 62), 24, width=7)
    pygame.draw.line(icon, RED, (65, 52), (100, 82), 5)
    return icon


def oil_pressure() -> pygame.Surface:
    icon = surface()
    points = [(24, 70), (58, 48), (86, 58), (104, 48), (114, 58), (96, 76), (62, 82)]
    pygame.draw.lines(icon, RED, False, points, 8)
    pygame.draw.line(icon, RED, (32, 50), (52, 50), 8)
    pygame.draw.line(icon, RED, (92, 78), (110, 94), 6)
    pygame.draw.circle(icon, RED, (112, 104), 6)
    return icon


def check_engine() -> pygame.Surface:
    icon = surface()
    pygame.draw.rect(icon, AMBER, pygame.Rect(28, 50, 66, 38), width=8, border_radius=4)
    pygame.draw.rect(icon, AMBER, pygame.Rect(44, 36, 24, 14), width=7)
    pygame.draw.line(icon, AMBER, (94, 62), (110, 62), 7)
    pygame.draw.line(icon, AMBER, (22, 62), (28, 62), 7)
    pygame.draw.line(icon, AMBER, (42, 88), (42, 102), 7)
    pygame.draw.line(icon, AMBER, (76, 88), (76, 102), 7)
    return icon


def eps() -> pygame.Surface:
    icon = surface()
    pygame.draw.circle(icon, RED, (64, 54), 32, width=7)
    pygame.draw.line(icon, RED, (64, 86), (64, 108), 7)
    pygame.draw.arc(icon, RED, pygame.Rect(36, 86, 56, 32), 0.1, 3.0, 7)
    draw_text(icon, "EPS", RED, 28)
    return icon


def coolant_temp() -> pygame.Surface:
    icon = surface()
    pygame.draw.line(icon, RED, (58, 24), (58, 84), 8)
    pygame.draw.circle(icon, RED, (58, 92), 16, width=8)
    pygame.draw.circle(icon, RED, (58, 92), 8)
    pygame.draw.line(icon, RED, (70, 34), (90, 34), 6)
    for y in (82, 100):
        pygame.draw.arc(icon, RED, pygame.Rect(24, y - 8, 28, 16), 0, 3.14, 5)
        pygame.draw.arc(icon, RED, pygame.Rect(54, y - 8, 28, 16), 0, 3.14, 5)
        pygame.draw.arc(icon, RED, pygame.Rect(84, y - 8, 28, 16), 0, 3.14, 5)
    return icon


def main() -> int:
    print("DEPRECATED: Use layout-editor-electron/scripts/modernize-warning-icons.js instead.")
    print("The new script uses high-quality SVGs from Iconify/MDI.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
