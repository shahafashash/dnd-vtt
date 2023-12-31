"""
    ____  _   ______         _    ______________
   / __ \/ | / / __ \       | |  / /_  __/_  __/
  / / / /  |/ / / / /       | | / / / /   / /
 / /_/ / /|  / /_/ /        | |/ / / /   / /
/_____/_/ |_/_____/         |___/ /_/   /_/
    by Shahaf Ashash and Simon Labunsky

"""

__version__ = "1.0.0"

from typing import Tuple
from math import cos, sin, pi, atan2, degrees, sqrt
from tools.utils import cycle
import pygame as pg
from collections import deque
from enum import Enum
from frontend.gui import *
from frontend.font import Font
from backend.factories import AbstractFactory, SimpleFactory
from frontend.effects import Effects, DarknessEffect, ColorFilter
from frontend.tokens import TokenManager, TokenSurf
from frontend.menus import MenuManager

FPS = 60


class Event(Enum):
    PLAY = 0
    CHANGE_MAP = 1


class State(Enum):
    GAME_MAIN_MENU = 0
    GAME_RUM_MAP = 1


class Grid(Enum):
    GRID = 0
    HEX = 1
    NONE = 2


class GridColors(Tuple, Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (128, 128, 128)


class GameEvent:
    def __init__(self, event_type: Event, data: Any):
        self.type = event_type
        self.data = data


class GameManager:
    _instance = None

    def __init__(self, factory: AbstractFactory):
        GameManager._instance = self
        self.menu_manager = MenuManager()
        self.settings = factory.create_settings("settings.json")

        # Setting up GUI fonts
        self.__setup_gui_fonts()

        # Creating GUI frame
        self.__setup_gui_frame()

        self.draw_custom_cursor = False

        # Create the screen
        self.screen = None
        self.__setup_screen()

        # Create the clock
        self.clock = pg.time.Clock()

        self.menu_manager.create_loading_screen(self.screen)
        maps_config_path = self.settings.get("maps_config", default="maps.json")
        tokens_dir = self.settings.get("tokens_path", default="assets/tokens")
        self.config = factory.create_config(maps_config_path)
        self.loader = factory.create_loader(self.config)
        self.map_searcher = factory.create_searcher(self.config)
        self.controls = factory.create_controls(self.settings)
        self.tokens_manager = factory.create_tokens_manager(tokens_dir)
        self.token_searcher = factory.create_token_searcher(self.tokens_manager)
        self.db_searcher = factory.create_db_searcher()
        self.maps = self.config.maps_names
        self.menu_manager.set_config(self.config)

        # update screen
        self.screen.blit(get_background(), (0, 0))
        GUI.step()
        GUI.draw()
        pg.display.flip()

        self.current_map_name = None
        self.current_map_frames = None

        # Setting up the grid
        self.grid_size = None
        self.grid_color = None
        self.grid_state = None
        self.grid_states = None
        self.grid_colors = None
        self.__setup_grid()

        self.state = State.GAME_MAIN_MENU
        self.event_que = deque()

        self.effects = Effects()
        self.tokens = TokenManager(
            self.screen,
            self.controls,
        )
        self.tokens.load_tokens(r"./assets/tokens")

        self.map_zoom = 1.0
        self.map_offset = (0, 0)
        self.map_drag = False

        self.cursor = pg.image.load(r"./assets/images/cursor.png")
        self.cursor_length = 50
        self.cursor_edge = (0, 0)

    def __setup_screen(self) -> None:
        # Create the screen
        resolution_width = self.settings.get(
            "resolution", subname="width", default=1920
        )
        resolution_height = self.settings.get(
            "resolution", subname="height", default=1080
        )
        screen = pg.display.set_mode(
            (resolution_width, resolution_height), pygame.RESIZABLE
        )
        if self.draw_custom_cursor:
            pg.mouse.set_visible(False)

        self.screen = screen
        GUI.win = screen

    def __setup_gui_fonts(self) -> None:
        # Setting up GUI fonts
        fonts = self.settings.get("fonts", default=[])
        for path in fonts.values():
            GUI.fonts.append(Font(path))

    def __setup_gui_frame(self) -> None:
        # Creating GUI frame
        frame = self.settings.get("frame", default="assets/images/frame.json")
        GUI.frames.append(Frame(frame))

    def __setup_grid(self) -> None:
        # Setting up the grid
        self.grid_size = self.settings.get("grid", subname="size", default=60)
        grid_color = self.settings.get("grid", subname="color", default="black")
        self.grid_color = GridColors[grid_color.upper()].value
        grid_state = self.settings.get("grid", subname="type", default="grid")
        self.grid_state = Grid[grid_state.upper()]
        self.grid_states = cycle([grid_state for grid_state in Grid])
        self.grid_colors = cycle([grid_color.value for grid_color in GridColors])

        # Iterate over the grid states and colors to get to the current one
        while next(self.grid_states) != self.grid_state:
            pass
        while next(self.grid_colors) != self.grid_color:
            pass

    def get_instance():
        return GameManager._instance

    def add_event(self, event):
        self.event_que.append(event)

    def handle_game_events(self):
        while len(self.event_que):
            event = self.event_que.popleft()
            if event.type == Event.CHANGE_MAP:
                self.current_map_name = event.data
                self.current_map_frames = self.loader.load_map(self.current_map_name)
                print(self.current_map_name)
                self.state = State.GAME_RUM_MAP
            elif event.type == Event.PLAY:
                self.state = State.GAME_RUM_MAP

    def global_pygame_event_handler(self, event):
        if event.type == pg.QUIT:
            exit(0)
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                if self.state == State.GAME_MAIN_MENU:
                    exit(0)
                elif self.state == State.GAME_RUM_MAP:
                    if self.menu_manager.current_menu:
                        GUI.remove(self.menu_manager.current_menu)
                        self.menu_manager.current_menu = None
                    else:
                        self.menu_manager.create_menu_game(self.screen)
            elif event.key == pg.K_F11:
                pygame.display.set_mode(self.screen.get_size(), pygame.FULLSCREEN)
            elif event.key == pg.K_t:
                self.test()
        elif event.type == pg.MOUSEMOTION:
            dir_to_cursor_edge = (
                self.cursor_edge[0] - event.pos[0],
                self.cursor_edge[1] - event.pos[1],
            )
            length = sqrt(dir_to_cursor_edge[0] ** 2 + dir_to_cursor_edge[1] ** 2)
            self.cursor_edge = (
                event.pos[0]
                + dir_to_cursor_edge[0] * (1 / length) * self.cursor_length,
                event.pos[1]
                + dir_to_cursor_edge[1] * (1 / length) * self.cursor_length,
            )

    def test(self):
        pass

    def step(self):
        self.handle_game_events()

        if self.state == State.GAME_MAIN_MENU:
            self.main_menu()
        elif self.state == State.GAME_RUM_MAP:
            self.run_map()

    def setup(self):
        self.menu_manager.create_main_menu(self.screen)

    def main_menu(self):
        background = get_background()

        for event in pg.event.get():
            GUI.event_handle(event)
            self.global_pygame_event_handler(event)

        GUI.step()

        self.screen.blit(background, (0, 0))
        GUI.draw()

        self.draw_cursor()
        # update the display and tick the clock
        pg.display.flip()
        self.clock.tick(FPS)

    def apply_color_filter(self, color, name, apply):
        if not apply:
            for effect in self.effects:
                if effect.name == name:
                    self.effects.remove(effect)
                    return
        else:
            self.effects.append(ColorFilter(self.screen, color, self.controls))
            self.effects[-1].name = name

    def draw_grid(self):
        if self.grid_state == Grid.GRID:
            draw_grid(self.screen, self.grid_size, self.grid_color)
        elif self.grid_state == Grid.HEX:
            draw_grid_hex(self.screen, self.grid_size * 0.7, self.grid_color)

    def draw_cursor(self):
        if not self.draw_custom_cursor:
            return
        mouse_pos = pg.mouse.get_pos()
        dir = (mouse_pos[0] - self.cursor_edge[0], mouse_pos[1] - self.cursor_edge[1])
        cursor_angle = atan2(dir[1], dir[0])
        cursor = pg.transform.rotate(self.cursor, degrees(-cursor_angle))
        self.screen.blit(
            cursor,
            (
                mouse_pos[0] - cursor.get_width() // 2,
                mouse_pos[1] - cursor.get_height() // 2,
            ),
        )

    def run_map(self):
        for event in pg.event.get():
            GUI.event_handle(event)
            self.global_pygame_event_handler(event)
            self.tokens.handle_pygame_events(event)
            self.effects.handle_pygame_events(event)
            if pygame.key.get_mods() & pygame.KMOD_ALT:
                map_orientation_changed = False
                if event.type == pygame.MOUSEWHEEL:
                    # zoom map
                    old_zoom = self.map_zoom
                    zoom_factor = event.y * 0.05
                    if self.map_zoom + zoom_factor < 1.0:
                        zoom_factor = 1.0 - self.map_zoom
                    self.map_zoom += zoom_factor
                    center = pygame.mouse.get_pos()
                    vec = (
                        self.map_offset[0] - center[0],
                        self.map_offset[1] - center[1],
                    )
                    back_factor = 1 / old_zoom
                    vec = (
                        vec[0] * self.map_zoom * back_factor,
                        vec[1] * self.map_zoom * back_factor,
                    )
                    self.map_offset = (center[0] + vec[0], center[1] + vec[1])
                    map_orientation_changed = True
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.map_drag = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.map_drag = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.map_drag:
                        self.map_offset = (
                            self.map_offset[0] + event.rel[0],
                            self.map_offset[1] + event.rel[1],
                        )
                    map_orientation_changed = True

                if map_orientation_changed:
                    # limit map to screen
                    if self.map_offset[0] > 0:
                        self.map_offset = (0, self.map_offset[1])
                    if self.map_offset[1] > 0:
                        self.map_offset = (self.map_offset[0], 0)
                    if self.map_offset[0] <= self.screen.get_width() * (
                        1 - self.map_zoom
                    ):
                        self.map_offset = (
                            self.screen.get_width() * (1 - self.map_zoom),
                            self.map_offset[1],
                        )
                    if self.map_offset[1] <= self.screen.get_height() * (
                        1 - self.map_zoom
                    ):
                        self.map_offset = (
                            self.map_offset[0],
                            self.screen.get_height() * (1 - self.map_zoom),
                        )
            if event.type == pg.KEYDOWN:
                if event.key == self.controls.get("enlarge_grid"):
                    self.grid_size += 5
                elif event.key == self.controls.get("reduce_grid"):
                    self.grid_size -= 5
                    if self.grid_size < 5:
                        self.grid_size = 5
                elif event.key == self.controls.get("change_grid"):
                    self.grid_state = next(self.grid_states)
                elif event.key == self.controls.get("change_grid_color"):
                    self.grid_color = next(self.grid_colors)
                elif event.key == self.controls.get("next_map"):
                    map_index = self.maps.index(self.current_map_name)
                    next_map_index = (map_index + 1) % len(self.maps)
                    self.current_map_name = self.maps[next_map_index]
                    self.current_map_frames = self.loader.load_map(
                        self.current_map_name
                    )
                elif event.key == self.controls.get("previous_map"):
                    map_index = self.maps.index(self.current_map_name)
                    next_map_index = (map_index - 1) % len(self.maps)
                    self.current_map_name = self.maps[next_map_index]
                    self.current_map_frames = self.loader.load_map(
                        self.current_map_name
                    )

            # right click
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                self.menu_manager.create_menu_maps(self.maps)

            # file drop
            elif event.type == pg.DROPFILE:
                path = event.file
                if any([path.endswith(i) for i in [".png", ".jpg"]]):
                    token_surf = pg.image.load(path)
                    token = TokenSurf(token_surf, 100)
                    token.pos = pygame.mouse.get_pos()
                    self.tokens.append(token)

        GUI.step()
        self.tokens.step()
        self.effects.step()

        # draw the frame,
        frame = next(self.current_map_frames)
        if self.map_zoom > 1.0:
            frame = pygame.transform.smoothscale_by(frame, self.map_zoom)

        self.screen.blit(frame, self.map_offset)

        self.draw_grid()
        self.tokens.draw()
        self.effects.draw()

        GUI.draw()

        self.draw_cursor()
        # update the display and tick the clock
        pg.display.flip()
        self.clock.tick(FPS)


def draw_grid(surf, size=50, color=GridColors.BLACK.value):
    width, height = surf.get_size()
    for i in range(0, width, size):
        pg.draw.line(surf, color, (i, 0), (i, height))
    for i in range(0, height, size):
        pg.draw.line(surf, color, (0, i), (width, i))


def draw_grid_hex(surf, size=50, color=GridColors.BLACK.value):
    a = size
    b = a * cos(pi / 3)
    c = a * sin(pi / 3)
    lines = [
        [(b, 2 * c), (0, c), (b, 0), (a + b, 0), (2 * b + a, c), (a + b, 2 * c)],
        [(2 * b + a, c), (2 * b + 2 * a, c)],
    ]

    for y in range(0, surf.get_height(), int(2 * c)):
        for x in range(0, surf.get_width(), int(2 * b + 2 * a)):
            for line in lines:
                line_offset = [(t[0] + x, t[1] + y) for t in line]
                pg.draw.lines(surf, color, False, line_offset)


def handle_gui_events(event: str):
    print("[GUI EVENT]", event)
    values = GUI.get_values()
    game_manager = GameManager.get_instance()
    menu_manager = game_manager.menu_manager
    if event["key"] == "change_map":
        game_event = GameEvent(Event.CHANGE_MAP, event["text"])
        game_manager.add_event(game_event)
        GUI.elements.remove(menu_manager.current_menu)
        menu_manager.current_menu = None
    elif event["key"] == "search":
        found_maps = game_manager.map_searcher.search(event["text"])
        game_manager.maps = found_maps
        thumbnail_columns = menu_manager.current_menu.elements[0]
        menu_manager.current_menu.elements.remove(thumbnail_columns)
        thumbnail_columns = game_manager.menu_manager.create_columns_maps(found_maps)
        menu_manager.current_menu.elements.insert(0, thumbnail_columns)
        thumbnail_columns.set_pos(
            (GUI.win.get_width() // 2 - thumbnail_columns.size[0] // 2, 200)
        )
    elif event["key"] == "map_menu":
        game_manager.menu_manager.create_menu_maps(game_manager.maps)
    elif event["key"] == "start":
        game_manager.menu_manager.create_menu_maps(game_manager.maps)
    elif event["key"] == "exit":
        exit(0)
    elif event["key"] == "toggle_darkness":
        for effect in game_manager.effects:
            if effect.name == "darkness":
                game_manager.effects.remove(effect)
                GUI.remove(menu_manager.current_menu)
                menu_manager.current_menu = None
                return
        game_manager.effects.append(
            DarknessEffect(game_manager.screen, game_manager.controls)
        )
        GUI.remove(menu_manager.current_menu)
        menu_manager.current_menu = None
    elif event["key"] == "add_tag_menu":
        game_manager.menu_manager.create_menu_add_tag(game_manager.screen)
    elif event["key"] == "add_tags":
        button = event["element"]
        new_tag = button.parent.elements[0].text
        game_manager.config.add_tags(game_manager.current_map_name, new_tag)
        GUI.remove(menu_manager.current_menu)
        menu_manager.current_menu = None
    elif event["key"] == "favorited":
        map_name = event["map_name"]
        checked = event["state"]
        game_manager.config.set_favorite(map_name, checked)
    elif event["key"] == "add_rename_map_menu":
        game_manager.menu_manager.create_menu_rename_map(game_manager.screen)
    elif event["key"] == "rename_map":
        button = event["element"]
        new_name = button.parent.elements[0].text
        game_manager.config.rename_map(game_manager.current_map_name, new_name)
        GUI.remove(menu_manager.current_menu)
        menu_manager.current_menu = None
    elif event["key"] == "color_filter":
        game_manager.menu_manager.create_filters_menu(game_manager.screen)
    elif "fileter_check" in event["key"]:
        if event["key"] == "fileter_check_avernus":
            game_manager.apply_color_filter(
                (228, 117, 117), "avernus", values["fileter_check_avernus"]
            )
        if event["key"] == "fileter_check_mexico":
            game_manager.apply_color_filter(
                (243, 171, 78), "mexico", values["fileter_check_mexico"]
            )
        if event["key"] == "fileter_check_matrix":
            game_manager.apply_color_filter(
                (150, 234, 141), "matrix", values["fileter_check_matrix"]
            )
    elif event["key"] == "token_menu":
        game_manager.menu_manager.create_menu_tokens(
            game_manager.screen, game_manager.tokens.available_tokens
        )
    elif event["key"] == "insert_token":
        path = event["token"]["path"]
        token_surf = pg.image.load(path)
        token = TokenSurf(token_surf, 100)
        token.pos = (
            game_manager.screen.get_width() // 2,
            game_manager.screen.get_height() // 2,
        )
        game_manager.tokens.append(token)
        GUI.remove(menu_manager.current_menu)
        menu_manager.current_menu = None


def get_background():
    image_path = r"assets/images/background.png"
    image = pg.image.load(image_path)
    return image


def main():
    pg.init()

    GUI.gui_event_handler = handle_gui_events
    GUI.initialize("./assets/images/gui_config.json")

    game_manager = GameManager(factory=SimpleFactory)

    game_manager.setup()

    while True:
        game_manager.step()


if __name__ == "__main__":
    main()
