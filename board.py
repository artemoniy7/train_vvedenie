"""Board storage, collision checks, locking pieces, and clearing lines."""

from settings import BOARD_WIDTH, BOARD_HEIGHT


class Board:
    def __init__(self):
        self.reset()

    def reset(self):
        self.cells = [
            [None for _ in range(BOARD_WIDTH)]
            for _ in range(BOARD_HEIGHT)
        ]

    def is_valid(self, piece):
        """Check that every block is inside the board and in an empty cell."""
        for x, y in piece.cells():
            if x < 0 or x >= BOARD_WIDTH or y >= BOARD_HEIGHT:
                return False
            if y >= 0 and self.cells[y][x] is not None:
                return False
        return True

    def lock_piece(self, piece):
        """Add a landed piece to the board."""
        for x, y in piece.cells():
            if y >= 0:
                self.cells[y][x] = piece.color

    def clear_full_lines(self):
        """Remove completed rows and return how many were removed."""
        remaining = [
            row for row in self.cells
            if any(cell is None for cell in row)
        ]
        cleared = BOARD_HEIGHT - len(remaining)

        while len(remaining) < BOARD_HEIGHT:
            remaining.insert(0, [None for _ in range(BOARD_WIDTH)])

        self.cells = remaining
        return cleared
