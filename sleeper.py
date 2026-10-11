"""Создание и отрисовка деревянных шпал."""
import math
import random
import pygame
from settings import SCREEN_HEIGHT, SCREEN_WIDTH
from utils import world_to_screen

SLEEPER_SPACING = 105
SLEEPER_LENGTH = 175
SLEEPER_THICKNESS = 35
SLEEPER_START_OFFSET = 25
SLEEPER_COLOR = (112, 83, 55)
SLEEPER_DARK_COLOR = (70, 51, 35)
SLEEPER_SPRITE_CACHE: dict[tuple[int, int, int], pygame.Surface] = {}

def draw_sleepers(
    screen: pygame.Surface,
    centerline: list[tuple[float, float, float]],
    camera_x: float,
    camera_y: float,
    zoom: float,
    sleeper_texture: pygame.Surface | None = None,
    skip_start_distance: float = 0.0,
) -> None:
    """Ставит шпалы поперёк пути; при необходимости пропускает начало ветки."""
    if len(centerline) < 2:
        return
    cumulative = [0.0]
    for i in range(1, len(centerline)):
        x1, y1, _ = centerline[i - 1]
        x2, y2, _ = centerline[i]
        cumulative.append(cumulative[-1] + math.hypot(x2 - x1, y2 - y1))

    total = cumulative[-1]
    target = SLEEPER_START_OFFSET
    index = 0
    while target <= total:
        while index + 1 < len(cumulative) - 1 and cumulative[index + 1] < target:
            index += 1
        span = cumulative[index + 1] - cumulative[index]
        t = 0.0 if span == 0 else (target - cumulative[index]) / span
        x1, y1, a1 = centerline[index]
        x2, y2, a2 = centerline[index + 1]
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        angle = a1 + (a2 - a1) * t

        # Пропускаем только первые шпалы ответвления, которые накладывались
        # на шпалы основной линии. Основной путь при этом остаётся непрерывным.
        if target < skip_start_distance:
            target += SLEEPER_SPACING
            continue

        sx, sy = world_to_screen(x, y, camera_x, camera_y, zoom)
        # Не тратим время на шпалы, которые далеко за пределами окна.
        if (sx < -SCREEN_WIDTH or sx > SCREEN_WIDTH * 2
                or sy < -SCREEN_HEIGHT or sy > SCREEN_HEIGHT * 2):
            target += SLEEPER_SPACING
            continue

        width = max(1, round(SLEEPER_THICKNESS * zoom))
        height = max(1, round(SLEEPER_LENGTH * zoom))
        angle_key = round(math.degrees(angle) / 3) * 3
        cache_key = (width, height, angle_key)
        sleeper = SLEEPER_SPRITE_CACHE.get(cache_key)
        if sleeper is None:
            # Процедурная деревянная шпала с небольшим зерном и тёмными волокнами.
            base = pygame.Surface((width, height), pygame.SRCALPHA)
            base.fill(SLEEPER_COLOR)
            rng = random.Random((width * 73856093) ^ (height * 19349663))
            if width >= 3 and height >= 8:
                for _ in range(max(3, height // 5)):
                    gx = rng.randrange(width)
                    gy = rng.randrange(height)
                    grain_len = rng.randrange(2, max(3, min(15, height // 3)))
                    pygame.draw.line(
                        base, SLEEPER_DARK_COLOR, (gx, gy),
                        (gx + rng.choice((-1, 0, 1)), min(height - 1, gy + grain_len)),
                        1,
                    )
                for _ in range(max(2, height // 18)):
                    gx = rng.randrange(width)
                    gy = rng.randrange(height)
                    base.set_at((gx, gy), SLEEPER_DARK_COLOR)
            sleeper = pygame.transform.rotate(base, -angle_key)
            # Ограничиваем размер кэша, чтобы при прокрутке масштаба
            # не накапливались бесконечные варианты спрайтов.
            if len(SLEEPER_SPRITE_CACHE) > 700:
                SLEEPER_SPRITE_CACHE.clear()
            SLEEPER_SPRITE_CACHE[cache_key] = sleeper
        screen.blit(sleeper, sleeper.get_rect(center=(sx, sy)))
        target += SLEEPER_SPACING


