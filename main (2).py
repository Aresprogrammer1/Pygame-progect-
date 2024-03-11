import contextvars

import pygame
import pytmx
import random
import sqlite3
import pygame_gui

window_size = width, height = 672, 608
fps = 1500
maps_dir = "maps"
tile_size = 32
enemy_event_type = 30
n = 0
name_level_list = ['level.tmx', 'level1.tmx']
score = 0
best_score = 0
pygame.init()
gui_manager = pygame_gui.UIManager(window_size)
log_result = ''
password_result = ''
result = ''
screen_colour = 'black'
diff = ''


class Window:

    def __init__(self):
        self.log_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((220, 175), (200, 50)),
            text='Логин',
            manager=gui_manager
        )
        self.con = sqlite3.connect('C:/Users/Ученик11/PycharmProjects/pythonProject1/game.sqlite')
        self.cur = self.con.cursor()
        self.log = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((220, 225), (200, 50)),
            manager=gui_manager
        )
        self.password = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((220, 300), (200, 50)),
            manager=gui_manager
        )
        self.password_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((220, 350), (200, 50)),
            text='Пароль',
            manager=gui_manager
        )


class Window1:

    def __init__(self):
        self.start = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((225, 250), (200, 50)),
            text='Начать играть',
            manager=gui_manager
        )
        self.settings = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((225, 325), (200, 50)),
            text='Настроки',
            manager=gui_manager
        )
        self.colour = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((225, 282), (200, 50)),
            text='смена цвета',
            manager=gui_manager
        )
        self.exit = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((225, 375), (200, 50)),
            text='Выход',
            manager=gui_manager
        )
        self.exit_main = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((474, 566), (200, 50)),
            text='Выход',
            manager=gui_manager
        )


class Labyrinth:

    def __init__(self, filename, free_tiles, finish_tile):
        self.map1 = pytmx.load_pygame(f"{maps_dir}/{filename}")
        self.height = self.map1.height
        self.width = self.map1.width
        self.tile_size = self.map1.tilewidth
        self.free_tiles = free_tiles
        self.finish_tile = finish_tile

    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                image = self.map1.get_tile_image(x, y, 0)
                screen.blit(image, (x * self.tile_size, y * self.tile_size))

    def get_tile_id(self, position):
        return self.map1.tiledgidmap[self.map1.get_tile_gid(*position, 0)]

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles

    def find_path_step(self, start, target):
        inf = 1000
        x, y = start
        distance = [[inf] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[(0, 0)] * self.width for _ in range(self.height)]
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in (1, 0), (0, 1), (-1, 0), (0, -1):
                next_x, next_y = x + dx, y + dy
                if (0 <= next_x < self.width and 0 < next_y < self.height and self.is_free((next_x, next_y)) and
                        distance[next_y][next_x] == inf):
                    distance[next_y][next_x] = distance[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))
            x, y = target
        if distance[y][x] == inf or start == target:
            return start
        while prev[y][x] != start:
            if prev[y][x] == (0, 0):
                break
            x, y = prev[y][x]
        return x, y


class Hero:

    def __init__(self, position):
        self.x, self.y = position

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen):
        centre = self.x * tile_size + tile_size // 2, self.y * tile_size + tile_size // 2
        pygame.draw.circle(screen, pygame.Color("white"), centre, tile_size // 2)


class Enemy:

    global diff

    def __init__(self, position):
        self.x, self.y = position
        if score < 15:
            if diff == 'Легко':
                self.delay = 200 - (score * 10)
            elif diff == 'Средне':
                self.delay = 180 - (score * 10)
            elif diff == 'Сложно':
                self.delay = 160 - (score * 10)
            else:
                self.delay = 200 - (score * 10)
        elif score > 15:
            self.delay = 50
        pygame.time.set_timer(enemy_event_type, self.delay)

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def render(self, screen):
        centre = self.x * tile_size + tile_size // 2, self.y * tile_size + tile_size // 2
        pygame.draw.circle(screen, pygame.Color("red"), centre, tile_size // 2)


class Game:

    def __init__(self, labyrinth, hero, enemy):
        self.labyrinth = labyrinth
        self.hero = hero
        self.enemy = enemy
        pygame.mixer.music.load("Sounds/1_s.mp3")
        pygame.mixer.music.play(-1)
        self.con = sqlite3.connect('C:/Users/Ученик11/PycharmProjects/pythonProject1/game.sqlite')
        self.cur = self.con.cursor()
        r_a = self.cur.execute("""SELECT all1 FROM play WHERE user_id == {}""".format(result)).fetchone()
        self.cur.execute("""INSERT INTO play(all1) VALUES('{}') """.format(r_a[0] + 1))
        self.con.close()

    def render(self, screen):
        self.labyrinth.render(screen)
        self.hero.render(screen)
        self.enemy.render(screen)

    def update_hero(self):
        next_x, next_y = self.hero.get_position()
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            next_x -= 1
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_x += 1
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            next_y += 1
        if pygame.key.get_pressed()[pygame.K_UP]:
            next_y -= 1
        if self.labyrinth.is_free((next_x, next_y)):
            self.hero.set_position((next_x, next_y))

    def move_enemy(self):
        next_position = self.labyrinth.find_path_step(self.enemy.get_position(), self.hero.get_position())
        if next_position is not None:
            self.enemy.set_position(next_position)

    def check_win(self):
        return self.labyrinth.get_tile_id(self.hero.get_position()) == self.labyrinth.finish_tile

    def check_lose(self):
        return self.hero.get_position() == self.enemy.get_position()


def show_message(screen, message):
    font = pygame.font.Font(None, 50)
    text = font.render(message, True, (50, 50, 0))
    text_x = width // 2 - text.get_width() // 2
    text_y = height // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.rect(screen, (200, 250, 50), (text_x - 20, text_y - 10, text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def main():
    global score, log_result, password_result, result, screen_colour, diff
    pygame.init()
    screen = pygame.display.set_mode(window_size)

    w = Window()
    w1 = Window1()
    w1.start.hide()
    w1.settings.hide()
    w1.colour.hide()
    w1.exit.hide()
    w1.exit_main.hide()

    clock = pygame.time.Clock()
    running = True
    game_over = False
    is_start = False
    while running:
        time_delta = pygame.time.Clock().tick(60)

        if not is_start:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    w.confirmation_dilog = pygame_gui.windows.UIConfirmationDialog(
                        rect=pygame.Rect((200, 200), (260, 200)),
                        manager=gui_manager,
                        window_title='Подтвенрждение',
                        action_long_desc='Вы уверены, что хотите выйти?',
                        action_short_name='ДА',
                        blocking=True
                    )
                if event.type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    running = False
                else:
                    screen.fill(screen_colour)
                if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                    if event.ui_element == w.log:
                        log_result = event.text
                    if event.ui_element == w.password:
                        password_result = event.text
                    if int(len(w.log.text)) > 0 and int(len(w.password.text)) > 0:
                        con = sqlite3.connect('C:/Users/Ученик11/PycharmProjects/pythonProject1/game.sqlite')
                        cur = con.cursor()
                        reg_result = cur.execute(
                            """SELECT user_id FROM user WHERE login = {} and password = {}"""
                            .format(w.log.text, w.password.text)).fetchone()
                        result = reg_result
                        con.close()
                    else:
                        pass
                    if result is not None:
                        if len(result) == 1:
                            result = result[0]
                            log_result = ''
                            w.log.hide()
                            w.password.hide()
                            w1.start.show()
                            w1.settings.show()
                            w.log_button.hide()
                            w.password_button.hide()
                            w1.exit_main.show()
                            w1.colour.hide()
                    else:
                        con = sqlite3.connect('C:/Users/Ученик11/PycharmProjects/pythonProject1/game.sqlite')
                        cur = con.cursor()
                        cur.execute(
                            """INSERT INTO user(login, password) VALUES('{}', '{}') """
                            .format(w.log.text, w.password.text))
                        con.commit()
                        cur.execute("""INSERT INTO play(win, defeat, all1) VALUES('{}', '{}', '{}')"""
                                      .format(0, 0, 0))
                        reg_result = cur.execute(
                            """SELECT user_id FROM user WHERE login = {} and password = {}"""
                            .format(w.log.text, w.password.text)).fetchone()
                        result = reg_result
                        con.commit()
                        con.close()
                        password_result = ''
                        log_result = ''
                        w.log.hide()
                        w.password.hide()
                        w1.start.show()
                        w1.settings.show()
                        w.log_button.hide()
                        w.password_button.hide()
                        w1.exit_main.show()
                        w1.colour.hide()
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == w1.start:
                        n = random.randint(0, 1)
                        game = Game(Labyrinth(name_level_list[n], [30, 46, 15], 46), Hero((10, 9)), Enemy((19, 9)))
                        is_start = True
                        game_over = False
                    if event.ui_element == w1.settings:
                        w1.settings.hide()
                        w1.start.hide()
                        w1.colour.show()
                        w1.exit.show()
                        w1.exit_main.hide()
                    if event.ui_element == w1.exit:
                        w1.colour.hide()
                        w1.exit.hide()
                        w1.start.show()
                        w1.settings.show()
                        w1.exit_main.show()
                    if event.ui_element == w1.colour:
                        if screen_colour == 'black':
                            screen.fill('white')
                            screen_colour = 'white'
                        else:
                            screen.fill('black')
                            screen_colour = 'black'
                    if event.ui_element == w1.exit_main:
                        w1.exit_main.hide()
                        w1.start.hide()
                        w1.settings.hide()
                        w.password.show()
                        w.log_button.show()
                        w.password_button.show()
                        w.log.show()
                gui_manager.process_events(event)
                gui_manager.update(time_delta)
                gui_manager.draw_ui(screen)
        if is_start:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == enemy_event_type and not game_over:
                    game.move_enemy()

            if not game_over:
                game.update_hero()
            screen.fill(screen_colour)
            game.render(screen)
            if game.check_win():
                game_over = True
                pygame.mixer.music.stop()
                show_message(screen, "Вы победили!")
                con = sqlite3.connect('C:/Users/Ученик11/PycharmProjects/pythonProject1/game.sqlite')
                cur = con.cursor()
                r_w = cur.execute("""SELECT win FROM play WHERE user_id == {}""".format(result)).fetchone()
                cur.execute("""INSERT INTO play(win) VALUES('{}') """.format(int(r_w[0] + 1)))
                con.commit()
                con.close()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    score += 1
                    n = random.randint(0, 1)
                    labyrinth = Labyrinth(name_level_list[n], [30, 46, 15], 46)
                    hero = Hero((10, 9))
                    enemy = Enemy((19, 9))
                    game = Game(labyrinth, hero, enemy)
                    game_over = False
            if game.check_lose():
                game_over = True
                score = 0
                pygame.mixer.music.stop()
                con = sqlite3.connect('C:/Users/Ученик11/PycharmProjects/pythonProject1/game.sqlite')
                cur = con.cursor()
                r_d = cur.execute("""SELECT defeat FROM play WHERE user_id == {}""".format(result)).fetchone()
                cur.execute(
                    """INSERT INTO play(defeat) VALUES('{}') """
                    .format(r_d[0] + 1))
                con.commit()
                con.close()
                is_start = False
        pygame.display.flip()
        clock.tick(fps)
    pygame.quit()


if __name__ == "__main__":
    main()
