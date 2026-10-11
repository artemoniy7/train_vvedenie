"""Утилиты отрисовки железнодорожного полотна."""

import math
import random

import pygame

from settings import SCREEN_HEIGHT, SCREEN_WIDTH

RAIL_GAUGE = 95
RAIL_THICKNESS = 15
SLEEPER_SPACING = 105
SLEEPER_LENGTH = 175
SLEEPER_THICKNESS = 35
SLEEPER_START_OFFSET = 25

SLEEPER_COLOR = (112, 83, 55)
SLEEPER_DARK_COLOR = (70, 51, 35)
RAIL_COLOR = (155, 160, 164)
RAIL_DARK_COLOR = (62, 66, 70)
RAIL_HIGHLIGHT_COLOR = (205, 209, 211)

# Кэш спрайтов шпал: поворот и создание текстуры выполняются только при первом использовании.
SLEEPER_SPRITE_CACHE: dict[tuple[int, int, int], pygame.Surface] = {}

def world_to_screen(
    x: float, y: float, camera_x: float, camera_y: float, zoom: float
) -> tuple[int, int]:
    return (
        round((x - camera_x) * zoom + SCREEN_WIDTH / 2),
        round((y - camera_y) * zoom + SCREEN_HEIGHT / 2),
    )


def make_track_points() -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    """Возвращает точки основной линии и ответвления как (x, y, угол касательной).

    Дуга ответвления — часть окружности заданного радиуса. В конце дуги
    продолжаем путь прямой по касательной, поэтому излома в месте стыка нет.
    Угол задан в математических координатах; экранная ось Y направлена вниз.
    """
    main_points = [
        (float(TRACK_START_X), float(TRACK_CENTER_Y), 0.0),
        (float(TRACK_START_X + TRACK_LENGTH), float(TRACK_CENTER_Y), 0.0),
    ]

    angle_max = math.radians(BRANCH_ANGLE_DEG)
    radius = float(BRANCH_RADIUS)
    arc_length = radius * angle_max
    count = max(2, math.ceil(arc_length / CURVE_SAMPLE_STEP))
    branch_points: list[tuple[float, float, float]] = []

    # Центр дуги выбран так, чтобы в начале касательная была горизонтальной.
    # BRANCH_SIDE=-1 ведёт ветку вверх по экрану.
    for i in range(count + 1):
        angle = angle_max * i / count
        x = BRANCH_START_X + radius * math.sin(angle)
        y = TRACK_CENTER_Y + BRANCH_SIDE * radius * (1.0 - math.cos(angle))
        tangent = BRANCH_SIDE * angle
        branch_points.append((x, y, tangent))

    end_x, end_y, end_angle = branch_points[-1]
    branch_points.append((
        end_x + BRANCH_STRAIGHT_LENGTH * math.cos(end_angle),
        end_y + BRANCH_STRAIGHT_LENGTH * math.sin(end_angle),
        end_angle,
    ))
    return main_points, branch_points


def sample_branch(step: float = CURVE_SAMPLE_STEP) -> list[tuple[float, float, float]]:
    """Создаёт равномерные точки по дуге и прямому хвосту для шпал/рельсов."""
    angle_max = math.radians(BRANCH_ANGLE_DEG)
    radius = float(BRANCH_RADIUS)
    arc_length = radius * angle_max
    arc_count = max(2, math.ceil(arc_length / step))
    points: list[tuple[float, float, float]] = []
    for i in range(arc_count + 1):
        angle = angle_max * i / arc_count
        points.append((
            BRANCH_START_X + radius * math.sin(angle),
            TRACK_CENTER_Y + BRANCH_SIDE * radius * (1.0 - math.cos(angle)),
            BRANCH_SIDE * angle,
        ))

    end_x, end_y, end_angle = points[-1]
    straight_count = max(2, math.ceil(BRANCH_STRAIGHT_LENGTH / step))
    for i in range(1, straight_count + 1):
        distance = BRANCH_STRAIGHT_LENGTH * i / straight_count
        points.append((
            end_x + distance * math.cos(end_angle),
            end_y + distance * math.sin(end_angle),
            end_angle,
        ))
    return points


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

