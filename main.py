"""
Railway Simulator — стартовая точка проекта.

Запуск:
    python -m pip install -r requirements.txt
    python main.py
"""

import pygame

from settings import (
    BACKGROUND_COLOR,
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WINDOW_TITLE,
)


def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 30)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(BACKGROUND_COLOR)

        label = font.render(
            "Railway Simulator — стартовая сцена",
            True,
            (220, 225, 230),
        )
        screen.blit(label, (24, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
