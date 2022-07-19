from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, Clock, ObjectProperty, StringProperty
from kivy.graphics.vertex_instructions import Line, Quad, Triangle
from kivy.graphics.context_instructions import Color
from kivy.app import App
from kivy.core.window import Window
from kivy import platform
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder
from kivy.core.audio import SoundLoader
import random

from kivy.config import Config

Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '400')


Builder.load_file("menu.kv")


class MainWidget(RelativeLayout):
    from transforms import transform, transform_perspective
    from user_actions import on_keyboard_up, on_keyboard_down, keyboard_closed

    menu_widget = ObjectProperty()
    perspective_point_x = NumericProperty(0)
    perspective_point_y = NumericProperty(0)

    VERTICAL_NUMBER_LINES = 8
    VERTICAL_LINES_SPACING = 0.4
    vertical_lines = []

    HORIZONTAL_NUMBER_LINES = 15
    HORIZONTAL_LINES_SPACING = 0.15
    horizontal_lines = []

    SPEED_OFFSET_Y = 0.8
    current_offset_y = 0
    current_y_loop = 0

    SPEED_X = 3.0
    current_speed_x = 0
    current_offset_x = 0

    NUMBER_TILES = 16
    tiles = []
    tiles_coordinates = []
    NUMBER_PRE_FILL_TILES = 15

    ship = None
    SHIP_WIDTH_PERCENT = 0.1
    SHIP_BASE_Y_PERCENT = 0.04
    SHIP_HEIGHT_PERCENT = 0.035
    ship_coordinate = [(0, 0), (0, 0), (0, 0)]

    state_game_over = False
    state_game_has_started = False

    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_button_title = StringProperty("START")
    score_txt = StringProperty()

    sound_begin = None
    sound_galaxy = None
    sound_gameover_impact = None
    sound_gameover_voice = None
    sound_music1 = None
    sound_restart = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_audio()
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()
        self.reset_game()

        if self.is_desktop():
            self._keyboard = Window.request_keyboard(
                self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)

        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def init_audio(self):
        self.sound_begin = SoundLoader.load("audio/begin.wav")
        self.sound_galaxy = SoundLoader.load("audio/galaxy.wav")
        self.sound_gameover_impact = SoundLoader.load(
            "audio/gameover_impact.wav")
        self.sound_gameover_voice = SoundLoader.load(
            "audio/gameover_voice.wav")
        self.sound_music1 = SoundLoader.load("audio/music1.wav")
        self.sound_restart = SoundLoader.load("audio/restart.wav")

        self.sound_music1.volume = 1
        self.sound_begin.volume = .25
        self.sound_galaxy.volume = .25
        self.sound_gameover_voice.volume = .25
        self.sound_restart.volume = .25
        self.sound_gameover_impact.volume = .6

    def reset_game(self):
        self.current_offset_y = 0
        self.current_y_loop = 0

        self.current_speed_x = 0
        self.current_offset_x = 0

        self.tiles_coordinates = []
        self.pre_fill_tiles_coordinates()
        self.generate_tiles_coordinates()

        self.score_txt = "SCORE:" + str(self.current_y_loop)

        self.state_game_over = False

    def is_desktop(self):
        if platform in ('linux', 'win', 'macosx'):
            return True
        return False

    def pre_fill_tiles_coordinates(self):
        for i in range(0, self.NUMBER_PRE_FILL_TILES):
            self.tiles_coordinates.append((0, i))

    def init_ship(self):
        with self.canvas:
            Color(0, 0, 0)
            self.ship = Triangle()

    def update_ship(self):
        center_x = self.width / 2
        base_y = self.SHIP_BASE_Y_PERCENT * self.height
        half_width = self.SHIP_WIDTH_PERCENT * self.width / 2
        ship_height = self.SHIP_HEIGHT_PERCENT * self.height

        self.ship_coordinate[0] = (center_x - half_width, base_y)
        self.ship_coordinate[1] = (center_x, base_y + ship_height)
        self.ship_coordinate[2] = (center_x + half_width, base_y)

        x1, y1 = self.transform(*self.ship_coordinate[0])
        x2, y2 = self.transform(*self.ship_coordinate[1])
        x3, y3 = self.transform(*self.ship_coordinate[2])
        self.ship.points = [x1, y1, x2, y2, x3, y3]

    def check_ship_collision(self):
        for i in range(0, len(self.tiles_coordinates)):
            tile_x, tile_y = self.tiles_coordinates[i]
            if tile_y > self.current_y_loop + 1:
                return False  # Game over
            if self.check_ship_collision_with_tile(tile_x, tile_y):
                return True  # ok
        return False

    def check_ship_collision_with_tile(self, tile_x, tile_y):
        xmin, ymin = self.get_tile_coordinates(tile_x, tile_y)
        xmax, ymax = self.get_tile_coordinates(tile_x + 1, tile_y + 1)
        for i in range(0, 3):
            px, py = self.ship_coordinate[i]
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False

    def init_tiles(self):
        with self.canvas:
            Color(1, 1, 1)
            for _ in range(0, self.NUMBER_TILES):
                self.tiles.append(Quad())

    def generate_tiles_coordinates(self):
        last_x = 0
        last_y = 0

        for i in range(len(self.tiles_coordinates) - 1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinate = self.tiles_coordinates[-1]
            last_x = last_coordinate[0]
            last_y = last_coordinate[1] + 1

        for _ in range(len(self.tiles_coordinates), self.NUMBER_TILES):
            random_x = random.randint(0, 2)

            start_index = -int(self.VERTICAL_NUMBER_LINES / 2) + 1
            end_index = start_index + (self.VERTICAL_NUMBER_LINES - 1) - 1

            if last_x <= start_index:
                random_x = 1
            if last_x >= end_index:
                random_x = 2

            self.tiles_coordinates.append((last_x, last_y))
            if random_x == 1:
                last_x += 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            elif random_x == 2:
                last_x -= 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            last_y += 1

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for _ in range(0, self.VERTICAL_NUMBER_LINES):
                self.vertical_lines.append(Line())

    def get_line_x_from_index(self, index):
        central_line_x = self.perspective_point_x
        spacing_line_x = self.VERTICAL_LINES_SPACING * self.width
        offset_line = index - 0.5
        line_x = central_line_x + offset_line * spacing_line_x + self.current_offset_x
        return line_x

    def get_line_y_from_index(self, index):
        spacing_line_y = self.HORIZONTAL_LINES_SPACING * self.height
        line_y = index * spacing_line_y - self.current_offset_y
        return line_y

    def get_tile_coordinates(self, tile_x, tile_y):
        tile_y = tile_y - self.current_y_loop
        x = self.get_line_x_from_index(tile_x)
        y = self.get_line_y_from_index(tile_y)
        return x, y

    def update_tiles(self):
        for id_tiles in range(0, self.NUMBER_TILES):
            tile = self.tiles[id_tiles]
            tile_coordinates = self.tiles_coordinates[id_tiles]
            xmin, ymin = self.get_tile_coordinates(
                tile_coordinates[0], tile_coordinates[1])
            xmax, ymax = self.get_tile_coordinates(
                tile_coordinates[0] + 1, tile_coordinates[1] + 1)

            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

    def update_vertical_lines(self):
        # -1 0 1 2 -- si VERTICAL_NUMBER_LINES = 4
        start_index = -int(self.VERTICAL_NUMBER_LINES / 2) + 1
        for vertical_line in range(start_index, start_index + self.VERTICAL_NUMBER_LINES):
            line_x = self.get_line_x_from_index(vertical_line)
            x1, y1 = self.transform(line_x, 0)
            x2, y2 = self.transform(line_x, self.height)
            self.vertical_lines[vertical_line].points = [x1, y1, x2, y2]

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for _ in range(0, self.HORIZONTAL_NUMBER_LINES):
                self.horizontal_lines.append(Line())

    def update_horizontal_lines(self):
        start_index = -int(self.VERTICAL_NUMBER_LINES / 2) + 1
        end_index = start_index + self.VERTICAL_NUMBER_LINES - 1

        xmin = self.get_line_x_from_index(start_index)
        xmax = self.get_line_x_from_index(end_index)

        for horizontal_line in range(0, self.HORIZONTAL_NUMBER_LINES):
            line_y = self.get_line_y_from_index(horizontal_line)
            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[horizontal_line].points = [x1, y1, x2, y2]

    def update(self, dt):
        time_factor = dt * 60
        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()

        if not self.state_game_over and self.state_game_has_started:
            speed_y = self.SPEED_OFFSET_Y * self.height / 100
            self.current_offset_y += speed_y * time_factor

            spacing_y = self.HORIZONTAL_LINES_SPACING * self.height
            while self.current_offset_y >= spacing_y:
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                self.score_txt = "SCORE:" + str(self.current_y_loop)
                self.generate_tiles_coordinates()

            self_x = self.current_speed_x * self.width / 100
            self.current_offset_x += self_x * time_factor

        if not self.check_ship_collision() and not self.state_game_over:
            self.state_game_over = True
            self.menu_title = "G  A  M  E   O  V  E  R"
            self.menu_button_title = "RESTART"
            self.menu_widget.opacity = 1

            self.sound_music1.stop()
            self.sound_gameover_impact.play()
            Clock.schedule_once(self.play_game_over_voice_sound, 1.5)
            print("GAME OVER")

    def play_game_over_voice_sound(self, dt):
        if self.state_game_over:
            self.sound_gameover_voice.play()

    def on_menu_button_pressed(self):
        print("Start Game")

        if self.state_game_over:
            self.sound_restart.play()
        else:
            self.sound_begin.play()

        self.sound_music1.play()
        self.reset_game()
        self.state_game_has_started = True
        self.menu_widget.opacity = 0


class GalaxyApp(App):
    pass


GalaxyApp().run()
