"""Constants used by the Tetris game."""

CELL_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

BOARD_PIXEL_WIDTH = CELL_SIZE * BOARD_WIDTH
BOARD_PIXEL_HEIGHT = CELL_SIZE * BOARD_HEIGHT

WINDOW_WIDTH = 620
WINDOW_HEIGHT = 660
BOARD_LEFT = 40
BOARD_TOP = 30

FPS = 60
FALL_INTERVAL = 500  # milliseconds between automatic downward moves

BACKGROUND_COLOR = (18, 22, 32)
BOARD_COLOR = (28, 34, 48)
GRID_COLOR = (48, 56, 72)
TEXT_COLOR = (240, 244, 255)
GAME_OVER_COLOR = (255, 110, 110)

# Each shape is a small matrix: 1 means that a block exists there.
SHAPES = [
    [[1, 1, 1, 1]],                         # I
    [[1, 0, 0], [1, 1, 1]],                 # J
    [[0, 0, 1], [1, 1, 1]],                 # L
    [[1, 1], [1, 1]],                       # O
    [[0, 1, 1], [1, 1, 0]],                 # S
    [[0, 1, 0], [1, 1, 1]],                 # T
    [[1, 1, 0], [0, 1, 1]],                 # Z
]

PIECE_COLORS = [
    (70, 220, 230),
    (70, 100, 240),
    (245, 155, 65),
    (245, 220, 80),
    (90, 210, 120),
    (180, 100, 230),
    (240, 85, 100),
]
