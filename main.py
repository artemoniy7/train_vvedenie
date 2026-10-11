"""
Railway Simulator — прямой участок пути и плавная стрелочная развилка.

Управление:
    WASD / стрелки — движение камеры
    Колёсико мыши — приближение и отдаление
    Esc — выход
"""

import math

import pygame

from settings import (
    BACKGROUND_COLOR,
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WINDOW_TITLE,
)
from utils import draw_rail_path, draw_sleepers

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


def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    small_font = pygame.font.Font(None, 21)

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
                screen, centerline, camera_x, camera_y, zoom,
                skip_start_distance=skip_distance,
            )
        for centerline in track_lines:
            draw_rail_path(screen, centerline, camera_x, camera_y, zoom)

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
