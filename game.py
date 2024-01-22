from pygame import *
import pygame_menu as p_menu
from math import sin, cos, radians


class ToolBar:

    def __init__(self, screen, speed=4, r_step=2, acceleration=2):
        self.screen = screen
        my_theme = p_menu.Theme(background_color='#FFFFF0',
                                border_color='#000000',
                                border_width=3,
                                title_background_color='#75AB60',
                                title_font_color='#FFFFF0',
                                title_font_size=32,
                                title_font_shadow=True,
                                widget_margin=(0, 50),
                                widget_offset=(0, 56),
                                widget_font_color='#A9A9A9',
                                widget_font_shadow=True,
                                selection_color='#F5F5F5',
                                widget_selection_effect=p_menu.widgets.SimpleSelection(),
                                widget_font=p_menu.font.FONT_NEVIS,
                                widget_font_size=32)

        self.menu = p_menu.Menu("Fast & Furious", 800, 600, theme=my_theme, center_content=False)

        self.background = image.load('resources/menu_background.png')
        self.background = transform.scale(self.background, (self.screen.get_width(), self.screen.get_height()))

        self.speed = self.menu.add.text_input(default=str(speed), title='Speed: ', maxchar=2, input_type=p_menu.locals.INPUT_INT)
        self.r_step = self.menu.add.text_input(default=str(r_step), title='Step of rotation: ', maxchar=2, input_type=p_menu.locals.INPUT_INT)
        self.acceleration = self.menu.add.text_input(default=str(acceleration), title='Acceleration: ', maxchar=2, input_type=p_menu.locals.INPUT_INT)

        self.menu.add.button('Play', self.start_game)
        self.menu.add.button('Quit', p_menu.events.EXIT)

        self.menu.mainloop(self.screen, bgfun=self.set_background)

    def set_background(self):
        self.screen.blit(self.background, (0, 0))

    def start_game(self):
        self.speed = int(self.speed.get_value())
        self.r_step = int(self.r_step.get_value())
        self.acceleration = int(self.acceleration.get_value())
        self.menu.disable()
        self.screen.fill((255, 255, 255))
        Game(self.screen, self.speed, self.r_step, self.acceleration)


class Game:

    def __init__(self, screen, speed, r_step, acceleration):
        self.screen = screen
        self.clock = time.Clock()
        self.initial_time = time.get_ticks()
        self.width, self.height = 1536, 864
        self.board = [400, 150]
        self.font = font.Font('resources/Retro_Gaming.ttf', 90)
        self.delay_after = 4000
        self.S_WATCH_EVENT = USEREVENT + 1
        self.total_time = None
        time.set_timer(USEREVENT, 1000)
        self.counter = 3
        self.time_before = self.counter * 1000
        self.finish_freeze = False

        self.bg = image.load('resources/map.png')
        self.bg = transform.scale(self.bg, (self.width, self.height))  # 1:1.42
        self.screen.blit(self.bg, (0, 0))

        road = image.load('resources/road.png')
        road = transform.scale(road, (self.width, self.height))
        self.m_road = mask.from_surface(road)
        self.m_road.invert()
        self.offset = 120

        self.tree = image.load('resources/tree.png')
        self.tree = transform.scale(self.tree, (self.width, self.height))
        self.screen.blit(self.tree, (0, 0))

        obstacles = image.load('resources/obstacles.png')
        obstacles = transform.scale(obstacles, (self.width, self.height))
        self.m_obstacles = mask.from_surface(obstacles)

        self.finish = image.load('resources/finish.png')
        self.finish = transform.scale(self.finish, (self.width, self.height))
        self.screen.blit(self.finish, (0, 0))

        p_1 = image.load('resources/car_1.png')
        self.r_1 = 0
        self.a_1 = 15
        p_1 = transform.rotate(p_1, self.a_1)
        x_1, y_1 = 965, 720
        self.m_1 = mask.from_surface(p_1)
        self.screen.blit(p_1, (x_1, y_1))

        p_2 = image.load('resources/car_2.png')
        self.r_2 = 0
        self.a_2 = 15
        p_2 = transform.rotate(p_2, self.a_2)
        x_2, y_2 = 993, 714
        self.m_2 = mask.from_surface(p_2)
        self.screen.blit(p_2, (x_2, y_2))

        self.players = [p_1, p_2]
        self.positions = [[x_1, y_1], [x_2, y_2]]

        self.speed = speed
        self.r_step = r_step
        self.acceleration = acceleration

        # copy in order not to lose (ToolBar)
        self.speed_copy = speed
        self.r_step_copy = r_step

        self.ex_counter = False
        self.ex = False

        bg_copy = self.bg.copy()

        while not self.ex_counter:
            for ev in event.get():
                if ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    ToolBar(self.screen, self.speed, self.r_step, self.acceleration)
                if ev.type == USEREVENT:
                    if self.counter > 0:
                        self.draw_countdown(str(self.counter))
                    elif self.counter == 0:
                        self.draw_countdown('GO!')
                    else:
                        self.ex_counter = True
                    self.counter -= 1
                    self.redraw()
            display.flip()
            self.clock.tick(120)
        self.bg.blit(bg_copy, (0, 0))
        self.run_game()

    def run_game(self):
        while not self.ex:
            for ev in event.get():
                if ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    time.set_timer(self.S_WATCH_EVENT, 0)
                    self.speed = self.speed_copy
                    self.r_step = self.r_step_copy
                    ToolBar(self.screen, self.speed, self.r_step, self.acceleration)
                elif ev.type == self.S_WATCH_EVENT:
                    self.speed = 0
                    self.r_step = 0
            self.process_keyboard()
            self.keep_within()
            self.redraw()
            self.finisher()
            display.flip()
            self.clock.tick(120)

    def is_collision(self, n, dx, dy):
        match n:
            case 1:
                if self.m_1.overlap_area(self.m_road, (-(self.positions[0][0] + dx), -(self.positions[0][1] + dy))) < self.offset:
                    self.positions[0][0] += dx
                    self.positions[0][1] += dy
            case 2:
                if self.m_2.overlap_area(self.m_road, (-(self.positions[1][0] + dx), -(self.positions[1][1] + dy))) < self.offset:
                    self.positions[1][0] += dx
                    self.positions[1][1] += dy

    def obstacles(self, n, dx, dy):
        flag = False
        match n:
            case 1:
                if self.m_1.overlap_area(self.m_obstacles, (-(self.positions[0][0] + dx), -(self.positions[0][1] + dy))) > 10:
                    flag = True
            case 2:
                if self.m_2.overlap_area(self.m_obstacles, (-(self.positions[1][0] + dx), -(self.positions[1][1] + dy))) > 10:
                    flag = True
        if flag:
            self.fortunate(n, True)

    def fortunate(self, n, collapse):
        if collapse:
            self.draw_box(n % 2 + 1, collapse)
            transparent = (0, 0, 0, 0)
            self.players[n - 1].fill(transparent)
            self.speed = 0
            self.r_step = 0
        else:
            if not self.finish_freeze:
                self.finish_freeze = True
                time.set_timer(self.S_WATCH_EVENT, self.delay_after)
                self.draw_box(n, collapse)

    def finisher(self):
        if self.positions[0][0] < 155 and self.positions[0][1] < 70:
            self.fortunate(1, False)
        if self.positions[1][0] < 155 and self.positions[1][1] < 70:
            self.fortunate(2, False)

    def draw_box(self, n, collapse):
        center_x, center_y = self.bg.get_rect().center
        half_a, half_b = self.board[0] // 2, self.board[1] // 2

        match n:
            case 1:
                draw.rect(self.bg, '#535C9F', (center_x - half_a, center_y - half_b, self.board[0], self.board[1]), 0, 10)
            case 2:
                draw.rect(self.bg, '#EA0047', (center_x - half_a, center_y - half_b, self.board[0], self.board[1]), 0, 10)
        draw.rect(self.bg, '#F0F0F0', (center_x - half_a, center_y - half_b, self.board[0], self.board[1]), 3, 10)

        if collapse:
            text = self.font.render("WIN!", True, '#F0F0F0')
            t_rect = text.get_rect(center=self.bg.get_rect().center)
            self.bg.blit(text, t_rect)
        else:
            if self.total_time is None:  # freeze total_time
                self.total_time = self.font.render(self.elapsed(), True, '#F0F0F0')
            t_rect = self.total_time.get_rect(center=self.bg.get_rect().center)
            self.bg.blit(self.total_time, t_rect)

    def keep_within(self):
        map_width, map_height = self.width, self.height
        car_width, car_height = self.players[0].get_width(), self.players[0].get_height()

        x_1, y_1 = self.positions[0]
        x_2, y_2 = self.positions[1]

        x_1 = max(0, min(x_1, map_width - car_width))
        y_1 = max(0, min(y_1, map_height - car_height))
        x_2 = max(0, min(x_2, map_width - car_width))
        y_2 = max(0, min(y_2, map_height - car_height))

        self.positions[0] = [x_1, y_1]
        self.positions[1] = [x_2, y_2]

    def process_keyboard(self):
        keys = key.get_pressed()
        dx_1, dy_1 = 0, 0
        if keys[K_w]:
            dx_1 = sin(radians(-self.a_1)) * self.speed
            dy_1 = -cos(radians(-self.a_1)) * self.speed
        if keys[K_s]:
            dx_1 = -sin(radians(-self.a_1)) * self.speed
            dy_1 = cos(radians(-self.a_1)) * self.speed
        if keys[K_a] and keys[K_w]:
            self.a_1 += self.r_step
            self.r_1 += self.r_step
            dx_1 = sin(radians(-self.a_1)) * self.speed
            dy_1 = -cos(radians(-self.a_1)) * self.speed
        if keys[K_d] and keys[K_w]:
            self.a_1 -= self.r_step
            self.r_1 -= self.r_step
            dx_1 = sin(radians(-self.a_1)) * self.speed
            dy_1 = -cos(radians(-self.a_1)) * self.speed
        if keys[K_a] and keys[K_s]:
            self.a_1 -= self.r_step
            self.r_1 -= self.r_step
            dx_1 = -sin(radians(-self.a_1)) * self.speed
            dy_1 = cos(radians(-self.a_1)) * self.speed
        if keys[K_d] and keys[K_s]:
            self.a_1 += self.r_step
            self.r_1 += self.r_step
            dx_1 = -sin(radians(-self.a_1)) * self.speed
            dy_1 = cos(radians(-self.a_1)) * self.speed
        if keys[K_w] and keys[K_LSHIFT]:
            dx_1 = sin(radians(-self.a_1)) * self.speed * self.acceleration
            dy_1 = -cos(radians(-self.a_1)) * self.speed * self.acceleration
        if keys[K_a] and keys[K_w] and keys[K_LSHIFT]:
            self.a_1 += self.r_step
            self.r_1 += self.r_step
            dx_1 = sin(radians(-self.a_1)) * self.speed * self.acceleration
            dy_1 = -cos(radians(-self.a_1)) * self.speed * self.acceleration
        if keys[K_d] and keys[K_w] and keys[K_LSHIFT]:
            self.a_1 -= self.r_step
            self.r_1 -= self.r_step
            dx_1 = sin(radians(-self.a_1)) * self.speed * self.acceleration
            dy_1 = -cos(radians(-self.a_1)) * self.speed * self.acceleration
        self.is_collision(1, dx_1, dy_1)
        self.obstacles(1, dx_1, dy_1)

        dx_2, dy_2 = 0, 0
        if keys[K_p]:
            dx_2 = sin(radians(-self.a_2)) * self.speed
            dy_2 = -cos(radians(-self.a_2)) * self.speed
        if keys[K_SEMICOLON]:
            dx_2 = -sin(radians(-self.a_2)) * self.speed
            dy_2 = cos(radians(-self.a_2)) * self.speed
        if keys[K_l] and keys[K_p]:
            self.a_2 += self.r_step
            self.r_2 += self.r_step
            dx_2 = sin(radians(-self.a_2)) * self.speed
            dy_2 = -cos(radians(-self.a_2)) * self.speed
        if keys[K_QUOTE] and keys[K_p]:
            self.a_2 -= self.r_step
            self.r_2 -= self.r_step
            dx_2 = sin(radians(-self.a_2)) * self.speed
            dy_2 = -cos(radians(-self.a_2)) * self.speed
        if keys[K_l] and keys[K_SEMICOLON]:
            self.a_2 -= self.r_step
            self.r_2 -= self.r_step
            dx_2 = -sin(radians(-self.a_2)) * self.speed
            dy_2 = cos(radians(-self.a_2)) * self.speed
        if keys[K_QUOTE] and keys[K_SEMICOLON]:
            self.a_2 += self.r_step
            self.r_2 += self.r_step
            dx_2 = -sin(radians(-self.a_2)) * self.speed
            dy_2 = cos(radians(-self.a_2)) * self.speed
        if keys[K_p] and keys[K_RSHIFT]:
            dx_2 = sin(radians(-self.a_2)) * self.speed * self.acceleration
            dy_2 = -cos(radians(-self.a_2)) * self.speed * self.acceleration
        if keys[K_l] and keys[K_p] and keys[K_RSHIFT]:
            self.a_2 += self.r_step
            self.r_2 += self.r_step
            dx_2 = sin(radians(-self.a_2)) * self.speed * self.acceleration
            dy_2 = -cos(radians(-self.a_2)) * self.speed * self.acceleration
        if keys[K_QUOTE] and keys[K_p] and keys[K_RSHIFT]:
            self.a_2 -= self.r_step
            self.r_2 -= self.r_step
            dx_2 = sin(radians(-self.a_2)) * self.speed * self.acceleration
            dy_2 = -cos(radians(-self.a_2)) * self.speed * self.acceleration
        self.is_collision(2, dx_2, dy_2)
        self.obstacles(2, dx_2, dy_2)

    def redraw(self):
        first = transform.rotate(self.players[0], self.r_1)
        second = transform.rotate(self.players[1], self.r_2)
        self.screen.blit(self.bg, (0, 0))
        self.screen.blit(first, (self.positions[0][0], self.positions[0][1]))
        self.screen.blit(second, (self.positions[1][0], self.positions[1][1]))
        self.screen.blit(self.tree, (0, 0))
        self.screen.blit(self.finish, (0, 0))

    def elapsed(self):
        total_s = (time.get_ticks() - self.initial_time - self.time_before - self.delay_after) // 1000
        minutes = total_s // 60
        seconds = total_s % 60
        return f'{minutes:02d}:{seconds:02d}'

    def draw_countdown(self, passed):
        center = list(self.bg.get_rect().center)
        center[0] -= 155
        half_a, half_b = self.board[0] // 2, self.board[1] // 2
        draw.rect(self.bg, '#7F7F7F', (center[0] - half_a, center[1] - half_b, self.board[0], self.board[1]), 0, 10)
        draw.rect(self.bg, '#F0F0F0', (center[0] - half_a, center[1] - half_b, self.board[0], self.board[1]), 3, 10)
        seconds = self.font.render(passed, True, '#F0F0F0')
        t_rect = seconds.get_rect(center=center)
        self.bg.blit(seconds, t_rect)


if __name__ == '__main__':
    init()
    viewer = display.set_mode()
    ToolBar(viewer)
