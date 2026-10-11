"""Основные правила игры, обработка управления и отрисовка."""  # Назначение этого модуля.

import pygame  # Подключаем библиотеку для окна, событий, времени и графики.

from board import Board  # Импортируем класс игрового поля.
from piece import Piece  # Импортируем класс фигуры.
from settings import (  # Импортируем параметры окна, поля, цветов и скорости.
    BACKGROUND_COLOR, BOARD_COLOR, BOARD_HEIGHT, BOARD_WIDTH, BOARD_LEFT,
    BOARD_PIXEL_HEIGHT, BOARD_PIXEL_WIDTH, BOARD_TOP, CELL_SIZE, FALL_INTERVAL,
    GAME_OVER_COLOR, GRID_COLOR, TEXT_COLOR, WINDOW_HEIGHT, WINDOW_WIDTH,
)


class Game:  # Главный класс, управляющий игровым процессом.
    def __init__(self):  # Подготавливает все объекты и переменные для новой игры.
        pygame.init()  # Инициализируем модули Pygame.
        pygame.display.set_caption("Тетрис")  # Устанавливаем заголовок окна.
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))  # Создаём игровое окно заданного размера.
        self.clock = pygame.time.Clock()  # Создаём часы для контроля частоты кадров.
        self.font = pygame.font.Font(None, 34)  # Создаём шрифт для крупных надписей.
        self.small_font = pygame.font.Font(None, 24)  # Создаём шрифт для подсказок и счёта.

        self.board = Board()  # Создаём игровое поле.
        self.score = 0  # Начальное количество очков.
        self.game_over = False  # Флаг: игра пока не завершена.
        self.fall_timer = 0  # Накопленное время до следующего автоматического падения.
        self.current_piece = Piece()  # Создаём фигуру, которой игрок управляет сейчас.
        self.next_piece = Piece()  # Создаём фигуру, которая появится следующей.

    def run(self):  # Запускает основной цикл игры.
        running = True  # Пока это значение True, игра продолжает работать.
        while running:  # Повторяем обработку событий, обновление и рисование.
            elapsed = self.clock.tick(60)  # Ограничиваем скорость до 60 кадров и получаем время прошедшего кадра в миллисекундах.
            running = self.handle_events()  # Обрабатываем события и узнаём, нужно ли продолжать игру.
            self.update(elapsed)  # Обновляем игровую логику с учётом прошедшего времени.
            self.draw()  # Рисуем текущее состояние игры на экране.
        pygame.quit()  # Корректно завершаем работу Pygame после выхода из цикла.

    def handle_events(self):  # Обрабатывает закрытие окна и нажатия клавиш.
        for event in pygame.event.get():  # Получаем все события, накопившиеся с прошлого кадра.
            if event.type == pygame.QUIT:  # Если пользователь нажал кнопку закрытия окна...
                return False  # ...сообщаем главному циклу, что пора завершаться.
            if event.type == pygame.KEYDOWN:  # Если была нажата клавиша...
                if event.key == pygame.K_ESCAPE:  # Проверяем, нажал ли игрок Esc.
                    return False  # Esc завершает игру.
                if self.game_over and event.key == pygame.K_r:  # Если игра окончена и нажата R...
                    self.restart()  # ...начинаем игру заново.
                elif not self.game_over:  # Если игра ещё продолжается...
                    self.handle_key(event.key)  # ...передаём клавишу обработчику управления.
        return True  # Если выход не запрошен, продолжаем игру.

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
            # Быстрое падение: фигура опускается до упора и сразу закрепляется.
            while self.try_move(0, 1):  # Повторяем движение вниз, пока оно возможно.
                pass  # Тело цикла пустое: всё действие выполняется в условии while.
            self.place_piece()  # Закрепляем фигуру и создаём следующую.

    def rotate_piece(self, clockwise):  # Поворачивает фигуру, только если новое положение допустимо.
        old_shape = [row[:] for row in self.current_piece.shape]  # Сохраняем копию исходной формы на случай неудачного поворота.
        self.current_piece.rotate(clockwise)  # Поворачиваем текущую фигуру.
        if not self.board.is_valid(self.current_piece):  # Проверяем, не пересекается ли фигура с границами или другими блоками.
            self.current_piece.shape = old_shape  # Если положение недопустимо, возвращаем прежнюю форму.

    def try_move(self, dx, dy):  # Пытается сдвинуть фигуру на dx клеток по горизонтали и dy по вертикали.
        self.current_piece.x += dx  # Временно изменяем горизонтальную координату.
        self.current_piece.y += dy  # Временно изменяем вертикальную координату.
        if self.board.is_valid(self.current_piece):  # Проверяем новое положение фигуры.
            return True  # Движение допустимо, оставляем фигуру на новом месте.
        self.current_piece.x -= dx  # Отменяем горизонтальное перемещение, если оно привело к столкновению.
        self.current_piece.y -= dy  # Отменяем вертикальное перемещение, если оно привело к столкновению.
        return False  # Сообщаем, что выполнить движение нельзя.

    def update(self, elapsed):  # Обновляет состояние игры между кадрами.
        if self.game_over:  # Если игра уже завершена...
            return  # ...ничего больше не обновляем.
        self.fall_timer += elapsed  # Добавляем время, прошедшее с прошлого кадра.
        if self.fall_timer >= FALL_INTERVAL:  # Если наступило время очередного шага вниз...
            self.fall_timer = 0  # ...обнуляем таймер падения.
            if not self.try_move(0, 1):  # Пробуем опустить фигуру на одну клетку.
                self.place_piece()  # Если вниз двигаться нельзя, закрепляем фигуру на поле.

    def place_piece(self):  # Закрепляет текущую фигуру и подготавливает следующую.
        self.board.lock_piece(self.current_piece)  # Записываем клетки фигуры в игровое поле.
        self.score += self.board.clear_full_lines() * 100  # За каждую удалённую линию добавляем 100 очков.
        self.current_piece = self.next_piece  # Следующая фигура становится текущей.
        self.current_piece.x = 3  # Ставим новую фигуру в начальную позицию по горизонтали.
        self.current_piece.y = 0  # Ставим новую фигуру в верхнюю часть поля.
        self.next_piece = Piece()  # Генерируем фигуру, которая будет следующей.
        self.fall_timer = 0  # Сбрасываем таймер, чтобы новая фигура не падала сразу.
        if not self.board.is_valid(self.current_piece):  # Проверяем, есть ли место для новой фигуры.
            self.game_over = True  # Если места нет, завершаем раунд.

    def restart(self):  # Полностью сбрасывает состояние игры.
        self.board.reset()  # Очищаем игровое поле.
        self.score = 0  # Обнуляем счёт.
        self.game_over = False  # Снимаем флаг завершения игры.
        self.fall_timer = 0  # Сбрасываем таймер падения.
        self.current_piece = Piece()  # Создаём новую текущую фигуру.
        self.next_piece = Piece()  # Создаём новую следующую фигуру.
        if not self.board.is_valid(self.current_piece):  # Проверяем, допустимо ли начальное положение фигуры.
            self.game_over = True  # На случай отсутствия места сразу отмечаем завершение игры.

    def draw_cell(self, x, y, color):  # Рисует одну клетку фигуры или игрового поля.
        rect = pygame.Rect(  # Создаём прямоугольник клетки в пиксельных координатах окна.
            BOARD_LEFT + x * CELL_SIZE, BOARD_TOP + y * CELL_SIZE,  # Переводим координаты клетки в пиксели.
            CELL_SIZE, CELL_SIZE,  # Задаём ширину и высоту клетки.
        )
        pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=3)  # Рисуем клетку с небольшим отступом и скруглёнными углами.

    def draw(self):  # Отрисовывает всё игровое окно.
        self.screen.fill(BACKGROUND_COLOR)  # Закрашиваем окно цветом фона.
        board_rect = pygame.Rect(  # Создаём прямоугольник, обозначающий игровое поле.
            BOARD_LEFT, BOARD_TOP, BOARD_PIXEL_WIDTH, BOARD_PIXEL_HEIGHT  # Указываем положение и размеры поля.
        )
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect)  # Рисуем фон игрового поля.

        for y, row in enumerate(self.board.cells):  # Перебираем все строки закреплённых клеток поля.
            for x, color in enumerate(row):  # Перебираем клетки в каждой строке.
                if color is not None:  # Если клетка занята фигурой...
                    self.draw_cell(x, y, color)  # ...рисуем её соответствующим цветом.

        if not self.game_over:  # Пока игра продолжается...
            for x, y in self.current_piece.cells():  # Перебираем клетки текущей падающей фигуры.
                if y >= 0:  # Рисуем только клетки, попадающие в видимую область поля.
                    self.draw_cell(x, y, self.current_piece.color)  # Отображаем клетку текущей фигуры.

        for x in range(BOARD_WIDTH + 1):  # Перебираем вертикальные линии сетки, включая края поля.
            px = BOARD_LEFT + x * CELL_SIZE  # Вычисляем горизонтальную координату линии в пикселях.
            pygame.draw.line(self.screen, GRID_COLOR, (px, BOARD_TOP),  # Начинаем линию у верхнего края поля...
                             (px, BOARD_TOP + BOARD_PIXEL_HEIGHT))  # ...и заканчиваем у нижнего края поля.
        for y in range(BOARD_HEIGHT + 1):  # Перебираем горизонтальные линии сетки, включая края поля.
            py = BOARD_TOP + y * CELL_SIZE  # Вычисляем вертикальную координату линии в пикселях.
            pygame.draw.line(self.screen, GRID_COLOR, (BOARD_LEFT, py),  # Начинаем линию у левого края поля...
                             (BOARD_LEFT + BOARD_PIXEL_WIDTH, py))  # ...и заканчиваем у правого края поля.

        info_x = BOARD_LEFT + BOARD_PIXEL_WIDTH + 25  # Находим координату области с информацией справа от поля.
        self.screen.blit(self.font.render("ТЕТРИС", True, TEXT_COLOR), (info_x, 45))  # Рисуем заголовок игры.
        self.screen.blit(self.small_font.render(f"Очки: {self.score}", True, TEXT_COLOR),  # Создаём надпись с текущим счётом...
                         (info_x, 95))  # ...и задаём её положение.
        self.screen.blit(self.small_font.render("ДАЛЕЕ:", True, TEXT_COLOR), (info_x, 145))  # Подписываем область следующей фигуры.

        for row_index, row in enumerate(self.next_piece.shape):  # Перебираем строки матрицы следующей фигуры.
            for col_index, value in enumerate(row):  # Перебираем клетки в каждой строке.
                if value:  # Если клетка занята частью фигуры...
                    rect = pygame.Rect(info_x + col_index * 22,  # Вычисляем горизонтальную координату клетки предпросмотра...
                                       180 + row_index * 22, 22, 22)  # ...и её вертикальную координату, ширину и высоту.
                    pygame.draw.rect(self.screen, self.next_piece.color,  # Выбираем цвет следующей фигуры...
                                     rect.inflate(-2, -2), border_radius=3)  # ...и рисуем клетку со скруглёнными углами.

        self.screen.blit(self.small_font.render("Z: влево", True, TEXT_COLOR), (info_x, 275))  # Показываем клавишу движения влево.
        self.screen.blit(self.small_font.render("X: вправо", True, TEXT_COLOR), (info_x, 305))  # Показываем клавишу движения вправо.
        self.screen.blit(self.small_font.render("A: поворот влево", True, TEXT_COLOR), (info_x, 335))  # Показываем клавишу поворота влево.
        self.screen.blit(self.small_font.render("D: поворот вправо", True, TEXT_COLOR), (info_x, 365))  # Показываем клавишу поворота вправо.
        self.screen.blit(self.small_font.render("S: сбросить вниз", True, TEXT_COLOR), (info_x, 395))  # Показываем клавишу мгновенного падения.
        self.screen.blit(self.small_font.render("Esc: выход", True, TEXT_COLOR), (info_x, 425))  # Показываем клавишу выхода.

        if self.game_over:  # Если игра завершилась...
            message = self.font.render("ИГРА ОКОНЧЕНА", True, GAME_OVER_COLOR)  # Создаём сообщение о завершении игры.
            self.screen.blit(message, message.get_rect(  # Размещаем сообщение по центру игрового поля...
                center=(BOARD_LEFT + BOARD_PIXEL_WIDTH // 2,  # ...вычисляем центральную координату по горизонтали...
                        BOARD_TOP + BOARD_PIXEL_HEIGHT // 2 - 12)))  # ...и немного смещаем по вертикали.
            restart = self.small_font.render("R: начать заново", True, TEXT_COLOR)  # Создаём подсказку о перезапуске.
            self.screen.blit(restart, restart.get_rect(  # Размещаем подсказку по центру...
                center=(BOARD_LEFT + BOARD_PIXEL_WIDTH // 2,  # ...по горизонтали...
                        BOARD_TOP + BOARD_PIXEL_HEIGHT // 2 + 22)))  # ...и чуть ниже главного сообщения.

        pygame.display.flip()  # Показываем на экране всё, что нарисовали в этом кадре.
