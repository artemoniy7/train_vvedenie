"""Main game rules and drawing."""

import pygame

from board import Board
from piece import Piece
from settings import (
    BACKGROUND_COLOR, BOARD_COLOR, BOARD_HEIGHT, BOARD_WIDTH, BOARD_LEFT,
    BOARD_PIXEL_HEIGHT, BOARD_PIXEL_WIDTH, BOARD_TOP, CELL_SIZE, FALL_INTERVAL,
    GAME_OVER_COLOR, GRID_COLOR, TEXT_COLOR, WINDOW_HEIGHT, WINDOW_WIDTH,
)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Simple Tetris")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 34)
        self.small_font = pygame.font.Font(None, 24)

        self.board = Board()
        self.score = 0
        self.game_over = False
        self.fall_timer = 0
        self.current_piece = Piece()
        self.next_piece = Piece()

    def run(self):
        running = True
        while running:
            elapsed = self.clock.tick(60)
            running = self.handle_events()
            self.update(elapsed)
            self.draw()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if self.game_over and event.key == pygame.K_r:
                    self.restart()
                elif not self.game_over:
                    self.handle_key(event.key)
        return True

    def handle_key(self, key):
        if key == pygame.K_a:
            self.rotate_piece(clockwise=False)
        elif key == pygame.K_d:
            self.rotate_piece(clockwise=True)
        elif key == pygame.K_s:
            # Hard drop: the piece lands immediately and can no longer be changed.
            while self.try_move(0, 1):
                pass
            self.place_piece()

    def rotate_piece(self, clockwise):
        old_shape = [row[:] for row in self.current_piece.shape]
        self.current_piece.rotate(clockwise)
        if not self.board.is_valid(self.current_piece):
            self.current_piece.shape = old_shape

    def try_move(self, dx, dy):
        self.current_piece.x += dx
        self.current_piece.y += dy
        if self.board.is_valid(self.current_piece):
            return True
        self.current_piece.x -= dx
        self.current_piece.y -= dy
        return False

    def update(self, elapsed):
        if self.game_over:
            return
        self.fall_timer += elapsed
        if self.fall_timer >= FALL_INTERVAL:
            self.fall_timer = 0
            if not self.try_move(0, 1):
                self.place_piece()

    def place_piece(self):
        self.board.lock_piece(self.current_piece)
        self.score += self.board.clear_full_lines() * 100
        self.current_piece = self.next_piece
        self.current_piece.x = 3
        self.current_piece.y = 0
        self.next_piece = Piece()
        self.fall_timer = 0
        if not self.board.is_valid(self.current_piece):
            self.game_over = True

    def restart(self):
        self.board.reset()
        self.score = 0
        self.game_over = False
        self.fall_timer = 0
        self.current_piece = Piece()
        self.next_piece = Piece()
        if not self.board.is_valid(self.current_piece):
            self.game_over = True

    def draw_cell(self, x, y, color):
        rect = pygame.Rect(
            BOARD_LEFT + x * CELL_SIZE, BOARD_TOP + y * CELL_SIZE,
            CELL_SIZE, CELL_SIZE,
        )
        pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=3)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        board_rect = pygame.Rect(
            BOARD_LEFT, BOARD_TOP, BOARD_PIXEL_WIDTH, BOARD_PIXEL_HEIGHT
        )
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect)

        for y, row in enumerate(self.board.cells):
            for x, color in enumerate(row):
                if color is not None:
                    self.draw_cell(x, y, color)

        if not self.game_over:
            for x, y in self.current_piece.cells():
                if y >= 0:
                    self.draw_cell(x, y, self.current_piece.color)

        for x in range(BOARD_WIDTH + 1):
            px = BOARD_LEFT + x * CELL_SIZE
            pygame.draw.line(self.screen, GRID_COLOR, (px, BOARD_TOP),
                             (px, BOARD_TOP + BOARD_PIXEL_HEIGHT))
        for y in range(BOARD_HEIGHT + 1):
            py = BOARD_TOP + y * CELL_SIZE
            pygame.draw.line(self.screen, GRID_COLOR, (BOARD_LEFT, py),
                             (BOARD_LEFT + BOARD_PIXEL_WIDTH, py))

        info_x = BOARD_LEFT + BOARD_PIXEL_WIDTH + 25
        self.screen.blit(self.font.render("TETRIS", True, TEXT_COLOR), (info_x, 45))
        self.screen.blit(self.small_font.render(f"Score: {self.score}", True, TEXT_COLOR),
                         (info_x, 95))
        self.screen.blit(self.small_font.render("NEXT:", True, TEXT_COLOR), (info_x, 145))

        for row_index, row in enumerate(self.next_piece.shape):
            for col_index, value in enumerate(row):
                if value:
                    rect = pygame.Rect(info_x + col_index * 22,
                                       180 + row_index * 22, 22, 22)
                    pygame.draw.rect(self.screen, self.next_piece.color,
                                     rect.inflate(-2, -2), border_radius=3)

        self.screen.blit(self.small_font.render("A: rotate left", True, TEXT_COLOR),
                         (info_x, 290))
        self.screen.blit(self.small_font.render("D: rotate right", True, TEXT_COLOR),
                         (info_x, 320))
        self.screen.blit(self.small_font.render("S: drop", True, TEXT_COLOR),
                         (info_x, 350))
        self.screen.blit(self.small_font.render("ESC: quit", True, TEXT_COLOR),
                         (info_x, 380))

        if self.game_over:
            message = self.font.render("GAME OVER", True, GAME_OVER_COLOR)
            self.screen.blit(message, message.get_rect(
                center=(BOARD_LEFT + BOARD_PIXEL_WIDTH // 2,
                        BOARD_TOP + BOARD_PIXEL_HEIGHT // 2 - 12)))
            restart = self.small_font.render("R: restart", True, TEXT_COLOR)
            self.screen.blit(restart, restart.get_rect(
                center=(BOARD_LEFT + BOARD_PIXEL_WIDTH // 2,
                        BOARD_TOP + BOARD_PIXEL_HEIGHT // 2 + 22)))

        pygame.display.flip()
