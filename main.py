"""
Railway Simulator — прямой участок пути и плавная стрелочная развилка.

Управление:
    WASD / стрелки — движение камеры
    Колёсико мыши — приближение и отдаление
    Esc — выход
"""

import math
from pathlib import Path

import pygame

from settings import (
    BACKGROUND_COLOR,
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WINDOW_TITLE,
)

# ---------------------------------------------------------------------------
# ГЕОМЕТРИЯ ПУТИ. Все размеры указаны в мировых пикселях.
# ---------------------------------------------------------------------------
TRACK_START_X = 150
TRACK_CENTER_Y = 0
TRACK_LENGTH = 2600              # основной путь стал длиннее

RAIL_GAUGE = 95                  # расстояние между центрами рельсов
RAIL_THICKNESS = 15
SLEEPER_SPACING = 105
SLEEPER_LENGTH = 175
SLEEPER_THICKNESS = 35
SLEEPER_START_OFFSET = 25

# Развилка: плавная круговая дуга, затем прямой выход под тем же углом.
BRANCH_START_X = TRACK_START_X + 1050
BRANCH_RADIUS = 1050              # радиус дуги: больше радиус — плавнее поворот
BRANCH_ANGLE_DEG = 28             # угол выхода ответвления
BRANCH_STRAIGHT_LENGTH = 1150
BRANCH_SIDE = -1                  # -1 — вверх на экране, +1 — вниз
CURVE_SAMPLE_STEP = 18             # шаг дискретизации дуги для ровной отрисовки

CAMERA_MOVE_SPEED = 650
ZOOM_STEP = 1.12
MIN_ZOOM = 0.25
MAX_ZOOM = 3.0
START_ZOOM = 0.8

SLEEPER_COLOR = (105, 82, 58)
RAIL_COLOR = (145, 151, 155)
RAIL_DARK_COLOR = (65, 69, 72)

# Кэш готовых спрайтов шпал: поворот и масштаб выполняются только один раз.
SLEEPER_SPRITE_CACHE: dict[tuple[int, int, int], pygame.Surface] = {}


def load_texture(filename: str) -> pygame.Surface | None:
    """Ищет текстуру в стандартных местах проекта."""
    candidates = (
        Path("assets") / "textures" / filename,
        Path("assets") / filename,
        Path(filename),
    )
    for path in candidates:
        if path.is_file():
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except (pygame.error, OSError) as error:
                print(f"Не удалось загрузить текстуру {path}: {error}")
    print(f"Текстура {filename} не найдена — используется простая заглушка.")
    return None


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
    rail_texture: pygame.Surface | None,
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
        pygame.draw.lines(screen, RAIL_DARK_COLOR, False, centers, thickness + 2)
        pygame.draw.lines(screen, RAIL_COLOR, False, centers, thickness)


def draw_sleepers(
    screen: pygame.Surface,
    centerline: list[tuple[float, float, float]],
    camera_x: float,
    camera_y: float,
    zoom: float,
    sleeper_texture: pygame.Surface | None,
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
            if sleeper_texture is not None:
                base = pygame.transform.scale(sleeper_texture, (width, height))
            else:
                base = pygame.Surface((width, height), pygame.SRCALPHA)
                base.fill(SLEEPER_COLOR)
            sleeper = pygame.transform.rotate(base, -angle_key)
            # Ограничиваем размер кэша, чтобы при прокрутке масштаба
            # не накапливались бесконечные варианты спрайтов.
            if len(SLEEPER_SPRITE_CACHE) > 700:
                SLEEPER_SPRITE_CACHE.clear()
            SLEEPER_SPRITE_CACHE[cache_key] = sleeper
        screen.blit(sleeper, sleeper.get_rect(center=(sx, sy)))
        target += SLEEPER_SPACING


def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    small_font = pygame.font.Font(None, 21)

    rail_texture = load_texture("ral.png")
    sleeper_texture = load_texture("sleeper.png")

    camera_x = TRACK_START_X + TRACK_LENGTH / 2
    camera_y = TRACK_CENTER_Y
    zoom = START_ZOOM
    running = True

    # Схема полигона: несколько параллельных путей и плавные отводы.
    # Каждая линия хранит точки центра и угол касательной.
    track_lines: list[list[tuple[float, float, float]]] = []
    track_sleepers: list[tuple[list[tuple[float, float, float]], float]] = []

    POLYGON_TRACK_COUNT = 5
    POLYGON_TRACK_SPACING = 320
    POLYGON_TRACK_LENGTH = 5200
    POLYGON_START_X = -400
    POLYGON_BRANCH_RADIUS = 900
    POLYGON_BRANCH_ANGLE = 24
    POLYGON_BRANCH_LENGTH = 1350
    POLYGON_BRANCH_STARTS = [900, 1850, 2850, 3900]

    for lane in range(POLYGON_TRACK_COUNT):
        lane_y = (lane - (POLYGON_TRACK_COUNT - 1) / 2) * POLYGON_TRACK_SPACING
        straight_line = [
            (float(POLYGON_START_X), float(lane_y), 0.0),
            (float(POLYGON_START_X + POLYGON_TRACK_LENGTH), float(lane_y), 0.0),
        ]
        track_lines.append(straight_line)
        track_sleepers.append((straight_line, 0.0))

        # На нескольких линиях добавляем ответвления с разными направлениями.
        if lane in (0, 1, 3, 4):
            side = -1 if lane < 2 else 1
            start_x = POLYGON_BRANCH_STARTS[lane if lane < 2 else lane - 1]
            angle_max = math.radians(POLYGON_BRANCH_ANGLE)
            radius = float(POLYGON_BRANCH_RADIUS)
            arc_len = radius * angle_max
            arc_count = max(3, math.ceil(arc_len / CURVE_SAMPLE_STEP))
            branch: list[tuple[float, float, float]] = []
            for i in range(arc_count + 1):
                a = angle_max * i / arc_count
                branch.append((
                    start_x + radius * math.sin(a),
                    lane_y + side * radius * (1.0 - math.cos(a)),
                    side * a,
                ))
            ex, ey, ea = branch[-1]
            straight_count = max(2, math.ceil(POLYGON_BRANCH_LENGTH / CURVE_SAMPLE_STEP))
            for i in range(1, straight_count + 1):
                d = POLYGON_BRANCH_LENGTH * i / straight_count
                branch.append((ex + d * math.cos(ea), ey + d * math.sin(ea), ea))
            track_lines.append(branch)
            # Сохраняем настройку пропуска шпал только у изначальной стрелки.
            track_sleepers.append((branch, 600.0 if lane == 2 else 0.0))

    camera_x = 2100.0
    camera_y = 0.0
    zoom = START_ZOOM
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    zoom = min(MAX_ZOOM, zoom * (ZOOM_STEP ** event.y))
                elif event.y < 0:
                    zoom = max(MIN_ZOOM, zoom / (ZOOM_STEP ** (-event.y)))

        keys = pygame.key.get_pressed()
        move_x = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT])
        move_y = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP])
        if move_x and move_y:
            move_x *= 0.7071
            move_y *= 0.7071
        camera_x += move_x * CAMERA_MOVE_SPEED * dt / zoom
        camera_y += move_y * CAMERA_MOVE_SPEED * dt / zoom

        screen.fill(BACKGROUND_COLOR)

        # Рисуем все шпалы, затем все рельсы — так текстуры рельсов остаются сверху.
        for centerline, skip_distance in track_sleepers:
            draw_sleepers(
                screen, centerline, camera_x, camera_y, zoom, sleeper_texture,
                skip_start_distance=skip_distance,
            )
        for centerline in track_lines:
            draw_rail_path(screen, centerline, camera_x, camera_y, zoom, rail_texture)

        title = font.render("Railway Simulator — железнодорожный полигон", True, (240, 243, 238))
        screen.blit(title, (18, 16))
        hint = small_font.render("WASD / стрелки: камера   Колёсико: масштаб   Esc: выход", True, (230, 235, 228))
        screen.blit(hint, (18, 46))
        status = small_font.render(
            f"Zoom: {zoom:.2f}x | Путей: {len(track_lines)} | Радиус дуг: {POLYGON_BRANCH_RADIUS}",
            True, (230, 235, 228)
        )
        screen.blit(status, (18, 72))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
