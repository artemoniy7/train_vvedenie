"""Создание и отрисовка рельсов."""
import math
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from utils import world_to_screen

RAIL_GAUGE = 95
RAIL_THICKNESS = 15
RAIL_COLOR = (155, 160, 164)
RAIL_DARK_COLOR = (62, 66, 70)
RAIL_HIGHLIGHT_COLOR = (205, 209, 211)

def draw_rail_path(
    screen: pygame.Surface,
    points: list[tuple[float, float, float]],
    camera_x: float,
    camera_y: float,
    zoom: float,
    rail_texture: pygame.Surface | None = None,
) -> None:
    """Быстро рисует рельсы линиями: без масштабирования/поворота текстур каждый кадр."""
    if len(points) < 2:
        return
    gauge_half = RAIL_GAUGE / 2
    thickness = max(2, round(RAIL_THICKNESS * zoom))
    clip = screen.get_rect()

    for side in (-1, 1):
        centers = []
        for x, y, angle in points:
            nx, ny = -math.sin(angle), math.cos(angle)
            sx, sy = world_to_screen(
                x + side * gauge_half * nx,
                y + side * gauge_half * ny,
                camera_x, camera_y, zoom,
            )
            centers.append((sx, sy))

        # Отсекаем линии, которые целиком вне экрана, прежде чем рисовать.
        xs = [p[0] for p in centers]
        ys = [p[1] for p in centers]
        margin = thickness + 4
        if (max(xs) < -margin or min(xs) > SCREEN_WIDTH + margin
                or max(ys) < -margin or min(ys) > SCREEN_HEIGHT + margin):
            continue

        # Pygame рисует полилинии значительно дешевле, чем преобразование
        # тысяч текстурных кусочков каждый кадр. Двойной штрих сохраняет объём.
        # Тёмная боковая грань, светлая верхняя поверхность и тонкий блик.
        pygame.draw.lines(screen, RAIL_DARK_COLOR, False, centers, thickness + 3)
        pygame.draw.lines(screen, RAIL_COLOR, False, centers, max(1, thickness - 2))
        if thickness >= 5:
            pygame.draw.lines(screen, RAIL_HIGHLIGHT_COLOR, False, centers, 1)

