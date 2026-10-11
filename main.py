"""
Railway Simulator — прямой участок пути и плавная стрелочная развилка.

Управление:
    WASD / стрелки — движение камеры
    Колёсико мыши — приближение и отдаление
    Esc — выход
"""

import pygame

from settings import (
    BACKGROUND_COLOR,
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WINDOW_TITLE,
)
from tracks import create_tracks, draw_tracks, POLYGON_BRANCH_RADIUS

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

    track_lines, track_sleepers = create_tracks()

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

        draw_tracks(screen, track_lines, track_sleepers, camera_x, camera_y, zoom)

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
