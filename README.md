# Tetris (Pygame)

A small, class-based Tetris prototype.

## Run

1. Install Python 3.10 or newer.
2. Install the dependency:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Start the game:

   ```bash
   python main.py
   ```

## Controls

- **Left / Right** or **A / D** — move
- **Down** or **S** — move down faster
- **Up**, **W**, or **Space** — rotate
- **R** — restart after game over
- **Esc** — quit

## Code layout

- `main.py` — starts the game.
- `game.py` — game loop, controls, scoring, and drawing.
- `board.py` — board cells, collision checks, and completed lines.
- `piece.py` — falling piece shape, color, position, and rotation.
- `settings.py` — window, board, colors, and piece shapes.
