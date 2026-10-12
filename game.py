"""Основные правила игры, обработка управления и отрисовка."""  # Назначение этого модуля.

import sys  # Позволяет определить платформу, на которой запущена программа.
import pygame  # Подключаем библиотеку для окна, событий, времени и графики.

from board import Board  # Импортируем класс игрового поля.
from piece import Piece  # Импортируем класс фигуры.
from settings import (  # Импортируем параметры окна, поля, цветов и скорости.
    BACKGROUND_COLOR, BOARD_COLOR, BOARD_HEIGHT, BOARD_WIDTH, BOARD_LEFT,
    BOARD_PIXEL_HEIGHT, BOARD_PIXEL_WIDTH, BOARD_TOP, BUTTON_COLOR,
    BUTTON_ACTIVE_COLOR, CELL_SIZE, FALL_INTERVAL, GAME_OVER_COLOR,
    GRID_COLOR, IS_LINUX, TEXT_COLOR, WINDOW_HEIGHT, WINDOW_WIDTH,
)


class Game:  # Главный класс, управляющий игровым процессом.
    def __init__(self):  # Подготавливает все объекты и переменные для новой игры.
        pygame.init()  # Инициализируем модули Pygame.
        self.is_linux = sys.platform.startswith("linux")  # Определяем Linux непосредственно при запуске игры.
        pygame.display.set_caption("Тетрис")  # Устанавливаем заголовок окна.
        if self.is_linux:  # На Linux-устройстве...
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)  # ...открываем игру на весь экран 1224×2720.
        else:  # На других системах...
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))  # ...открываем обычное окно.
        self.clock = pygame.time.Clock()  # Создаём часы для контроля частоты кадров.
        self.font = pygame.font.Font(None, 64 if self.is_linux else 34)  # Создаём крупный шрифт заголовка.
        self.small_font = pygame.font.Font(None, 42 if self.is_linux else 24)  # Создаём шрифт счёта и подсказок.

        self.board = Board()  # Создаём игровое поле.
        self.score = 0  # Начальное количество очков.
        self.game_over = False  # Флаг: игра пока не завершена.
        self.fall_timer = 0  # Накопленное время до следующего автоматического падения.
        self.current_piece = Piece()  # Создаём фигуру, которой игрок управляет сейчас.
        self.next_piece = Piece()  # Создаём фигуру, которая появится следующей.
        self.buttons = self.create_touch_buttons() if self.is_linux else {}  # Создаём экранные кнопки только для Linux.

    def create_touch_buttons(self):  # Создаёт большие кнопки для управления пальцами.
        margin = 24  # Отступ между кнопками и от краёв экрана.
        gap = 18  # Расстояние между соседними кнопками.
        button_width = (WINDOW_WIDTH - margin * 2 - gap * 2) // 3  # Ширина каждой из трёх кнопок в ряду.
        button_height = 150  # Высота кнопки, чтобы по ней было удобно нажимать.
        first_y = BOARD_TOP + BOARD_PIXEL_HEIGHT + 130  # Располагаем кнопки ниже игрового поля.
        labels = [  # Названия и действия кнопок первого ряда.
            ("ВЛЕВО", "left"), ("ПОВОРОТ", "rotate"), ("ВПРАВО", "right"),
        ]
        buttons = {}  # Словарь для хранения прямоугольников кнопок и связанных действий.
        for index, (label, action) in enumerate(labels):  # Создаём три кнопки первого ряда.
            x = margin + index * (button_width + gap)  # Вычисляем горизонтальную координату кнопки.
            buttons[action] = (pygame.Rect(x, first_y, button_width, button_height), label)  # Сохраняем область кнопки и подпись.
        second_y = first_y + button_height + gap  # Координата второго ряда кнопок.
        second_width = (WINDOW_WIDTH - margin * 2 - gap) // 2  # Ширина двух кнопок второго ряда.
        buttons["down"] = (pygame.Rect(margin, second_y, second_width, button_height), "ВНИЗ")  # Кнопка мягкого падения.
        buttons["drop"] = (pygame.Rect(margin + second_width + gap, second_y, second_width, button_height), "СБРОСИТЬ")  # Кнопка мгновенного падения.
        return buttons  # Возвращаем все подготовленные кнопки.

    def run(self):  # Запускает основной цикл игры.
        running = True  # Пока это значение True, игра продолжает работать.
        while running:  # Повторяем обработку событий, обновление и рисование.
            elapsed = self.clock.tick(60)  # Ограничиваем скорость до 60 кадров и получаем время прошедшего кадра в миллисекундах.
            running = self.handle_events()  # Обрабатываем события и узнаём, нужно ли продолжать игру.
            self.update(elapsed)  # Обновляем игровую логику с учётом прошедшего времени.
            self.draw()  # Рисуем текущее состояние игры на экране.
        pygame.quit()  # Корректно завершаем работу Pygame после выхода из цикла.

    def handle_events(self):  # Обрабатывает закрытие окна, клавиатуру и сенсорные нажатия.
        for event in pygame.event.get():  # Получаем все события, накопившиеся с прошлого кадра.
            if event.type == pygame.QUIT:  # Если пользователь закрыл окно...
                return False  # ...завершаем игру.
            if event.type == pygame.KEYDOWN:  # Если нажата клавиша физической клавиатуры...
                if event.key == pygame.K_ESCAPE:  # Проверяем клавишу выхода.
                    return False  # Esc завершает игру.
                if self.game_over and event.key == pygame.K_r:  # Если игра окончена и нажата R...
                    self.restart()  # ...начинаем игру заново.
                elif not self.game_over:  # Если игра продолжается...
                    self.handle_key(event.key)  # ...передаём клавишу обработчику управления.
            if self.is_linux and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Обрабатываем касание экрана или щелчок мышью на Linux.
                self.handle_touch(event.pos)  # Выполняем действие кнопки, на которую нажали.
        return True  # Если выход не запрошен, продолжаем игру.

    def handle_touch(self, position):  # Определяет, на какую экранную кнопку нажал игрок.
        if self.game_over:  # Если раунд завершён...
            restart_rect = pygame.Rect(WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2, WINDOW_WIDTH // 2, 180)  # Создаём большую область перезапуска.
            if restart_rect.collidepoint(position):  # Проверяем, попало ли касание в область перезапуска.
                self.restart()  # Начинаем новый раунд.
            return  # Во время завершённой игры другие кнопки не работают.
        for action, (rect, _label) in self.buttons.items():  # Проверяем каждую экранную кнопку.
            if rect.collidepoint(position):  # Если касание попало внутрь кнопки...
                if action == "left":  # Кнопка движения влево.
                    self.try_move(-1, 0)  # Перемещаем фигуру на одну клетку влево.
                elif action == "right":  # Кнопка движения вправо.
                    self.try_move(1, 0)  # Перемещаем фигуру на одну клетку вправо.
                elif action == "rotate":  # Кнопка поворота.
                    self.rotate_piece(clockwise=True)  # Поворачиваем фигуру по часовой стрелке.
                elif action == "down":  # Кнопка движения вниз.
                    if not self.try_move(0, 1):  # Пробуем опустить фигуру на клетку.
                        self.place_piece()  # Если вниз двигаться нельзя, закрепляем фигуру.
                elif action == "drop":  # Кнопка мгновенного сброса.
                    while self.try_move(0, 1):  # Опускаем фигуру до самого нижнего допустимого положения.
                        pass  # Повторяем перемещение, пока оно возможно.
                    self.place_piece()  # Закрепляем фигуру и создаём следующую.
                return  # После обработки кнопки больше ничего не проверяем.

    def handle_key(self, key):  # Выполняет действие в зависимости от нажатой клавиши.
        if key == pygame.K_z:  # Клавиша Z перемещает фигуру влево.
            self.try_move(-1, 0)  # Меняем координату X на одну клетку влево.
        elif key == pygame.K_x:  # Клавиша X перемещает фигуру вправо.
            self.try_move(1, 0)  # Меняем координату X на одну клетку вправо.
        elif key == pygame.K_a:  # Клавиша A поворачивает фигуру против часовой стрелки.
            self.rotate_piece(clockwise=False)  # Выполняем поворот влево.
        elif key == pygame.K_d:  # Клавиша D поворачивает фигуру по часовой стрелке.
            self.rotate_piece(clockwise=True)  # Выполняем поворот вправо.
        elif key == pygame.K_s:  # Клавиша S мгновенно опускает фигуру вниз.
            while self.try_move(0, 1):  # Повторяем движение вниз, пока оно возможно.
                pass  # Тело цикла пустое: действие выполняется в условии while.
            self.place_piece()  # Закрепляем фигуру и создаём следующую.

    def rotate_piece(self, clockwise):  # Поворачивает фигуру, только если новое положение допустимо.
        old_shape = [row[:] for row in self.current_piece.shape]  # Сохраняем копию формы на случай неудачного поворота.
        self.current_piece.rotate(clockwise)  # Поворачиваем текущую фигуру.
        if not self.board.is_valid(self.current_piece):  # Проверяем новое положение.
            self.current_piece.shape = old_shape  # Если поворот невозможен, возвращаем исходную форму.

    def try_move(self, dx, dy):  # Пытается сдвинуть фигуру на dx и dy клеток.
        self.current_piece.x += dx  # Временно меняем горизонтальную координату.
        self.current_piece.y += dy  # Временно меняем вертикальную координату.
        if self.board.is_valid(self.current_piece):  # Проверяем новое положение фигуры.
            return True  # Движение допустимо.
        self.current_piece.x -= dx  # Отменяем горизонтальное перемещение при столкновении.
        self.current_piece.y -= dy  # Отменяем вертикальное перемещение при столкновении.
        return False  # Сообщаем, что движение невозможно.

    def update(self, elapsed):  # Обновляет состояние игры между кадрами.
        if self.game_over:  # Если игра завершена...
            return  # ...ничего не обновляем.
        self.fall_timer += elapsed  # Добавляем время, прошедшее с прошлого кадра.
        if self.fall_timer >= FALL_INTERVAL:  # Если пора сделать автоматический шаг вниз...
            self.fall_timer = 0  # Сбрасываем таймер.
            if not self.try_move(0, 1):  # Пробуем опустить фигуру.
                self.place_piece()  # Если движение невозможно, закрепляем фигуру.

    def place_piece(self):  # Закрепляет текущую фигуру и подготавливает следующую.
        self.board.lock_piece(self.current_piece)  # Записываем клетки фигуры в поле.
        self.score += self.board.clear_full_lines() * 100  # За каждую удалённую линию начисляем 100 очков.
        self.current_piece = self.next_piece  # Следующая фигура становится текущей.
        self.current_piece.x = 3  # Устанавливаем начальную горизонтальную координату.
        self.current_piece.y = 0  # Устанавливаем начальную вертикальную координату.
        self.next_piece = Piece()  # Создаём фигуру для следующего хода.
        self.fall_timer = 0  # Сбрасываем таймер падения.
        if not self.board.is_valid(self.current_piece):  # Проверяем, есть ли место для новой фигуры.
            self.game_over = True  # Если места нет, завершаем раунд.

    def restart(self):  # Полностью сбрасывает состояние игры.
        self.board.reset()  # Очищаем игровое поле.
        self.score = 0  # Обнуляем счёт.
        self.game_over = False  # Снимаем флаг завершения игры.
        self.fall_timer = 0  # Сбрасываем таймер падения.
        self.current_piece = Piece()  # Создаём новую текущую фигуру.
        self.next_piece = Piece()  # Создаём новую следующую фигуру.
        if not self.board.is_valid(self.current_piece):  # Проверяем начальное положение фигуры.
            self.game_over = True  # Если положение недопустимо, завершаем игру.

    def draw_cell(self, x, y, color):  # Рисует одну клетку фигуры или игрового поля.
        rect = pygame.Rect(BOARD_LEFT + x * CELL_SIZE, BOARD_TOP + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)  # Переводим координаты клетки в пиксели.
        pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=5 if self.is_linux else 3)  # Рисуем клетку с небольшим отступом.

    def draw_touch_buttons(self):  # Отрисовывает экранные кнопки для сенсорного управления.
        for _action, (rect, label) in self.buttons.items():  # Перебираем все кнопки и их подписи.
            pygame.draw.rect(self.screen, BUTTON_COLOR, rect, border_radius=20)  # Рисуем фон кнопки со скруглёнными углами.
            text = self.small_font.render(label, True, TEXT_COLOR)  # Создаём текст подписи.
            self.screen.blit(text, text.get_rect(center=rect.center))  # Размещаем подпись по центру кнопки.

    def draw(self):  # Отрисовывает всё игровое окно.
        self.screen.fill(BACKGROUND_COLOR)  # Закрашиваем окно цветом фона.
        if self.is_linux:  # Для Linux используем компоновку под высокий сенсорный экран.
            title = self.font.render("ТЕТРИС", True, TEXT_COLOR)  # Создаём заголовок игры.
            self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 55)))  # Размещаем заголовок по центру сверху.
            score = self.small_font.render(f"Очки: {self.score}", True, TEXT_COLOR)  # Создаём надпись со счётом.
            self.screen.blit(score, score.get_rect(center=(WINDOW_WIDTH // 2, 125)))  # Показываем счёт под заголовком.
        board_rect = pygame.Rect(BOARD_LEFT, BOARD_TOP, BOARD_PIXEL_WIDTH, BOARD_PIXEL_HEIGHT)  # Создаём прямоугольник игрового поля.
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect)  # Рисуем фон поля.

        for y, row in enumerate(self.board.cells):  # Перебираем строки закреплённых клеток.
            for x, color in enumerate(row):  # Перебираем клетки каждой строки.
                if color is not None:  # Если клетка занята...
                    self.draw_cell(x, y, color)  # ...рисуем её.

        if not self.game_over:  # Пока игра продолжается...
            for x, y in self.current_piece.cells():  # Перебираем клетки падающей фигуры.
                if y >= 0:  # Проверяем, что клетка находится внутри видимой области.
                    self.draw_cell(x, y, self.current_piece.color)  # Рисуем клетку текущей фигуры.

        for x in range(BOARD_WIDTH + 1):  # Перебираем вертикальные линии сетки.
            px = BOARD_LEFT + x * CELL_SIZE  # Вычисляем положение линии по горизонтали.
            pygame.draw.line(self.screen, GRID_COLOR, (px, BOARD_TOP), (px, BOARD_TOP + BOARD_PIXEL_HEIGHT))  # Рисуем вертикальную линию.
        for y in range(BOARD_HEIGHT + 1):  # Перебираем горизонтальные линии сетки.
            py = BOARD_TOP + y * CELL_SIZE  # Вычисляем положение линии по вертикали.
            pygame.draw.line(self.screen, GRID_COLOR, (BOARD_LEFT, py), (BOARD_LEFT + BOARD_PIXEL_WIDTH, py))  # Рисуем горизонтальную линию.

        if self.is_linux:  # На Linux показываем сенсорные кнопки вместо текстовых подсказок клавиатуры.
            self.draw_touch_buttons()  # Рисуем кнопки под игровым полем.
            if self.game_over:  # Если раунд завершён...
                message = self.font.render("ИГРА ОКОНЧЕНА", True, GAME_OVER_COLOR)  # Создаём сообщение о завершении игры.
                self.screen.blit(message, message.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100)))  # Показываем сообщение в центре экрана.
                restart_rect = pygame.Rect(WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2, WINDOW_WIDTH // 2, 180)  # Определяем большую область для касания и перезапуска.
                pygame.draw.rect(self.screen, BUTTON_COLOR, restart_rect, border_radius=20)  # Рисуем кнопку перезапуска.
                restart_text = self.small_font.render("НАЧАТЬ ЗАНОВО", True, TEXT_COLOR)  # Создаём подпись кнопки.
                self.screen.blit(restart_text, restart_text.get_rect(center=restart_rect.center))  # Размещаем подпись по центру кнопки.
        else:  # На остальных системах оставляем управление клавиатурой.
            info_x = BOARD_LEFT + BOARD_PIXEL_WIDTH + 25  # Вычисляем начало информационной области справа от поля.
            self.screen.blit(self.font.render("ТЕТРИС", True, TEXT_COLOR), (info_x, 45))  # Показываем название игры.
            self.screen.blit(self.small_font.render(f"Очки: {self.score}", True, TEXT_COLOR), (info_x, 95))  # Показываем счёт.
            self.screen.blit(self.small_font.render("ДАЛЕЕ:", True, TEXT_COLOR), (info_x, 145))  # Подписываем предпросмотр следующей фигуры.
            for row_index, row in enumerate(self.next_piece.shape):  # Перебираем строки следующей фигуры.
                for col_index, value in enumerate(row):  # Перебираем клетки строки.
                    if value:  # Если клетка принадлежит фигуре...
                        rect = pygame.Rect(info_x + col_index * 22, 180 + row_index * 22, 22, 22)  # Создаём прямоугольник клетки предпросмотра.
                        pygame.draw.rect(self.screen, self.next_piece.color, rect.inflate(-2, -2), border_radius=3)  # Рисуем клетку предпросмотра.
            hints = [("Z: влево", 275), ("X: вправо", 305), ("A: поворот влево", 335), ("D: поворот вправо", 365), ("S: сбросить вниз", 395), ("Esc: выход", 425)]  # Подсказки клавиш для компьютера.
            for label, y in hints:  # Перебираем подсказки и их вертикальные координаты.
                self.screen.blit(self.small_font.render(label, True, TEXT_COLOR), (info_x, y))  # Рисуем подсказку.
            if self.game_over:  # Если игра завершена...
                message = self.font.render("ИГРА ОКОНЧЕНА", True, GAME_OVER_COLOR)  # Создаём сообщение о завершении игры.
                self.screen.blit(message, message.get_rect(center=(BOARD_LEFT + BOARD_PIXEL_WIDTH // 2, BOARD_TOP + BOARD_PIXEL_HEIGHT // 2 - 12)))  # Размещаем сообщение по центру поля.
                restart = self.small_font.render("R: начать заново", True, TEXT_COLOR)  # Создаём подсказку о перезапуске.
                self.screen.blit(restart, restart.get_rect(center=(BOARD_LEFT + BOARD_PIXEL_WIDTH // 2, BOARD_TOP + BOARD_PIXEL_HEIGHT // 2 + 22)))  # Размещаем подсказку под сообщением.

        pygame.display.flip()  # Показываем на экране всё, что нарисовали в этом кадре.
