"""Общие утилиты координат для отрисовки мира."""
from settings import SCREEN_HEIGHT, SCREEN_WIDTH

def world_to_screen(x: float, y: float, camera_x: float, camera_y: float, zoom: float) -> tuple[int, int]:
    return (round((x - camera_x) * zoom + SCREEN_WIDTH / 2),
            round((y - camera_y) * zoom + SCREEN_HEIGHT / 2))
