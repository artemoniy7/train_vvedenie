"""
Railway Simulator — участок пути и камера.

Управление:
    WASD / стрелки — движение камеры
    Колёсико мыши — приближение и отдаление
    Esc — выход
"""

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
# ПАРАМЕТРЫ ПУТИ — можно спокойно менять под свои текстуры.
# Координаты задаются в мировых пикселях, а не в пикселях окна.
# ---------------------------------------------------------------------------
TRACK_START_X = 150
TRACK_CENTER_Y = 0
TRACK_LENGTH = 1800

RAIL_GAUGE = 105           # расстояние между центрами двух рельсов
RAIL_THICKNESS = 20        # высота отрисовки текстуры рельса
SLEEPER_SPACING = 105      # расстояние между шпалами
SLEEPER_LENGTH = 175       # длина шпалы поперёк пути
SLEEPER_THICKNESS = 25     # толщина шпалы при отрисовке
SLEEPER_START_OFFSET = 25  # сдвиг первой шпалы от начала рельсов

# Камера.
CAMERA_MOVE_SPEED = 650    # мировых пикселей в секунду
ZOOM_STEP = 1.12
MIN_ZOOM = 0.25
MAX_ZOOM = 3.0
START_ZOOM = 0.8

# Цвета запасной отрисовки, если картинки не найдены.
SLEEPER_COLOR = (105, 82, 58)
RAIL_COLOR = (145, 151, 155)
RAIL_DARK_COLOR = (65, 69, 72)


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


def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    small_font = pygame.font.Font(None, 21)

    rail_texture = load_texture("ral.png")
    sleeper_texture = load_texture("sleeper.png")

    # Поворот исходной вертикальной шпалы в горизонтальное положение.
    if sleeper_texture is not None:
        sleeper_texture = pygame.transform.rotate(sleeper_texture, 90)

    camera_x = TRACK_START_X + TRACK_LENGTH / 2
    camera_y = TRACK_CENTER_Y
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
                old_zoom = zoom
                if event.y > 0:
                    zoom = min(MAX_ZOOM, zoom * (ZOOM_STEP ** event.y))
                elif event.y < 0:
                    zoom = max(MIN_ZOOM, zoom / (ZOOM_STEP ** (-event.y)))

                # Сохраняем точку мира под центром окна при масштабировании.
                if old_zoom != zoom:
                    camera_x += SCREEN_WIDTH / 2 * (1 / old_zoom - 1 / zoom)
                    camera_y += SCREEN_HEIGHT / 2 * (1 / old_zoom - 1 / zoom)

        keys = pygame.key.get_pressed()
        move_x = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        move_y = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )
        if move_x and move_y:
            move_x *= 0.7071
            move_y *= 0.7071

        camera_x += move_x * CAMERA_MOVE_SPEED * dt / zoom
        camera_y += move_y * CAMERA_MOVE_SPEED * dt / zoom

        screen.fill(BACKGROUND_COLOR)

        # Шпалы рисуются первыми, чтобы рельсы были поверх них.
        sleeper_world_width = SLEEPER_LENGTH
        sleeper_world_height = SLEEPER_THICKNESS
        sleeper_count = int(TRACK_LENGTH / SLEEPER_SPACING) + 2
        for index in range(sleeper_count):
            x = TRACK_START_X + SLEEPER_START_OFFSET + index * SLEEPER_SPACING
            if x > TRACK_START_X + TRACK_LENGTH:
                break
            sx, sy = world_to_screen(x, TRACK_CENTER_Y, camera_x, camera_y, zoom)
            width = max(1, round(sleeper_world_width * zoom))
            height = max(1, round(sleeper_world_height * zoom))
            rect = pygame.Rect(0, 0, width, height)
            rect.center = (sx, sy)

            if sleeper_texture is not None:
                scaled_sleeper = pygame.transform.smoothscale(
                    sleeper_texture, (width, height)
                )
                screen.blit(scaled_sleeper, rect)
            else:
                pygame.draw.rect(screen, SLEEPER_COLOR, rect, border_radius=2)

        # Две параллельные рельсовые полосы.
        rail_count = 2
        for index in range(rail_count):
            rail_y = TRACK_CENTER_Y + (index - 0.5) * RAIL_GAUGE
            start = world_to_screen(
                TRACK_START_X, rail_y, camera_x, camera_y, zoom
            )
            end = world_to_screen(
                TRACK_START_X + TRACK_LENGTH, rail_y, camera_x, camera_y, zoom
            )
            thickness = max(2, round(RAIL_THICKNESS * zoom))

            if rail_texture is not None:
                rail_width = max(1, round(TRACK_LENGTH * zoom))
                rail_height = max(1, thickness)
                scaled_rail = pygame.transform.smoothscale(
                    rail_texture, (rail_width, rail_height)
                )
                rail_rect = scaled_rail.get_rect()
                rail_rect.midleft = start
                screen.blit(scaled_rail, rail_rect)
            else:
                pygame.draw.line(screen, RAIL_DARK_COLOR, start, end, thickness + 2)
                pygame.draw.line(screen, RAIL_COLOR, start, end, thickness)

        # Небольшая подпись и подсказки закреплены на экране, а не в мире.
        title = font.render("Railway Simulator — тестовый участок пути", True, (240, 243, 238))
        screen.blit(title, (18, 16))
        hint = small_font.render("WASD / стрелки: камера   Колёсико: масштаб   Esc: выход", True, (230, 235, 228))
        screen.blit(hint, (18, 46))
        status = small_font.render(f"Zoom: {zoom:.2f}x", True, (230, 235, 228))
        screen.blit(status, (18, 72))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
