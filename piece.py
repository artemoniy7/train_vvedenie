"""A falling Tetris piece."""

import random

from settings import SHAPES, PIECE_COLORS


class Piece:
    """Stores a shape, its color, and its position on the board."""

    def __init__(self, index=None):
        if index is None:
            index = random.randrange(len(SHAPES))
        self.shape = [row[:] for row in SHAPES[index]]
        self.color = PIECE_COLORS[index]
        self.x = 3
        self.y = 0

    def rotate(self, clockwise=True):
        """Rotate the matrix 90 degrees."""
        if clockwise:
            self.shape = [list(row) for row in zip(*self.shape[::-1])]
        else:
            self.shape = [list(row) for row in zip(*self.shape)][::-1]

    def cells(self):
        """Return occupied cells as board coordinates."""
        for row_index, row in enumerate(self.shape):
            for column_index, value in enumerate(row):
                if value:
                    yield self.x + column_index, self.y + row_index
