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
from math import cos, sin, pi
from utils import cycle
import pygame as pg
import json
from collections import deque
from enum import Enum
from gui import *
from font import Font
from loader import Loader
from searchers import MapSearcher
from effects import DarknessEffect

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

    def __init__(self, screen, clock):
        GameManager._instance = self
        self.screen = screen
        self.clock = clock

        self.draw_loading_screen()
        self.loader = Loader("maps.json")

        self.map_searcher = MapSearcher(loader=self.loader)
        self.maps = self.loader.maps_names

        self.current_map_name = None
        self.current_map_frames = None

        self.grid_size = 60

        self.grid_states = cycle([grid_state for grid_state in Grid])
        self.grid_colors = cycle([grid_color.value for grid_color in GridColors])
        self.grid_state = next(self.grid_states)
        self.grid_color = next(self.grid_colors)

        self.avernus_filter = False

        self.state = State.GAME_MAIN_MENU
        self.event_que = deque()

        self.search_textbox = None
        self.thumbnail_columns = None

        self.effects = DarknessEffect(self.screen)

    def get_instance():
        return GameManager._instance

    def add_event(self, event):
        self.event_que.append(event)

    def draw_loading_screen(self):
        cm = StackPanel()
        label_title = Label("LOADING...", GUI.get_font_at(2))
        cm.append(label_title)
        cm.pos = (
            self.screen.get_width() // 2 - cm.size[0] // 2,
            self.screen.get_height() // 2 - cm.size[1] // 2,
        )
        self.loading_screen = cm
        cm.frame = GUI.frames[0]

        GUI.append(cm)
        self.screen.blit(get_background(), (0, 0))
        GUI.step()
        GUI.draw()
        pg.display.flip()

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
                exit(0)
            elif event.key == pg.K_F11:
                pygame.display.set_mode(self.screen.get_size(), pygame.FULLSCREEN)

    def step(self):
        self.handle_game_events()

        if self.state == State.GAME_MAIN_MENU:
            self.main_menu()
        elif self.state == State.GAME_RUM_MAP:
            self.run_map()

    def setup(self):
        GUI.elements.remove(self.loading_screen)
        cm = StackPanel()
        label_title = Label("DND VIRTUAL TABLE TOP", GUI.get_font_at(2))
        cm.append(label_title)
        label_credits = Label("By Shahaf Ashash and Simon Labunsky", GUI.get_font_at(0))
        cm.append(label_credits)
        cm.pos = (
            self.screen.get_width() // 2 - cm.size[0] // 2,
            self.screen.get_height() // 2 - cm.size[1] // 2,
        )
        cm.frame = GUI.frames[0]
        self.main_menu_label = cm

        GUI.append(cm)

    def main_menu(self):
        background = get_background()
 
        for event in pg.event.get():
            GUI.event_handle(event)
            self.global_pygame_event_handler(event)
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                if self.main_menu_label in GUI.elements:
                    GUI.elements.remove(self.main_menu_label)
                create_menu_maps(self.maps, event.pos)

        GUI.step()

        self.screen.blit(background, (0, 0))
        GUI.draw()

        # update the display and tick the clock
        pg.display.flip()
        self.clock.tick(FPS)

    def draw_grid(self):
        if self.grid_state == Grid.GRID:
            draw_grid(self.screen, self.grid_size, self.grid_color)
        elif self.grid_state == Grid.HEX:
            draw_grid_hex(self.screen, self.grid_size * 0.7, self.grid_color)

    def run_map(self):
        for event in pg.event.get():
            GUI.event_handle(event)
            self.global_pygame_event_handler(event)
            self.effects.handle_events(event)
            if event.type == pg.KEYDOWN:
                # plus and minus of num pad
                if event.key == pg.K_KP_PLUS:
                    self.grid_size += 5
                elif event.key == pg.K_KP_MINUS:
                    self.grid_size -= 5
                    if self.grid_size < 5:
                        self.grid_size = 5
                elif event.key == pg.K_g:
                    self.grid_state = next(self.grid_states)
                elif event.key == pg.K_c:
                    self.grid_color = next(self.grid_colors)
                elif event.key == pg.K_a:
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.avernus_filter = not self.avernus_filter
                elif event.key == pg.K_RIGHT:
                    map_index = self.maps.index(self.current_map_name)
                    next_map_index = (map_index + 1) % len(self.maps)
                    self.current_map_name = self.maps[next_map_index]
                    self.current_map_frames = self.loader.load_map(
                        self.current_map_name
                    )
                elif event.key == pg.K_LEFT:
                    map_index = self.maps.index(self.current_map_name)
                    next_map_index = (map_index - 1) % len(self.maps)
                    self.current_map_name = self.maps[next_map_index]
                    self.current_map_frames = self.loader.load_map(
                        self.current_map_name
                    )

            # right click
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                create_menu_maps(self.maps, event.pos)

        GUI.step()
        self.effects.step()

        # draw the frame
        frame = next(self.current_map_frames)
        self.screen.blit(frame, (0, 0))

        self.effects.draw()

        if self.avernus_filter:
            self.screen.fill((255, 100, 100), special_flags=pygame.BLEND_MULT)
        self.draw_grid()

        GUI.draw()

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
    print(event)
    if event["key"] == "change_map":
        game_event = GameEvent(Event.CHANGE_MAP, event["text"])
        GameManager.get_instance().add_event(game_event)
        GUI.elements.remove(GameManager.get_instance().thumbnail_columns)
        GUI.elements.remove(GameManager.get_instance().search_textbox)
    elif event["key"] == "search":
        found_maps = GameManager.get_instance().map_searcher.search(event["text"])
        GUI.elements.remove(GameManager.get_instance().thumbnail_columns)
        thumbnail_columns = create_columns_maps(found_maps)
        GameManager.get_instance().thumbnail_columns = thumbnail_columns
        thumbnail_columns.set_pos(
            (GUI.win.get_width() // 2 - thumbnail_columns.size[0] // 2, 200)
        )
        GUI.elements.append(thumbnail_columns)


def load_maps(json_path: str):
    with open(json_path, "r") as f:
        maps_content = json.load(f)

    maps = [map["name"] for map in maps_content]
    return maps


def get_background():
    image_path = r"assets/images/background.png"
    image = pg.image.load(image_path)
    return image


def create_columns_maps(found_maps):
    thumbnail_columns = Columns(3)
    for map in found_maps:
        map_obj = GameManager.get_instance().loader.get_map(map)
        thumbnail = map_obj.thumbnail
        thumbnail_stackpanel = StackPanel()
        thumbnail_stackpanel.append(Picture(thumbnail))
        button = Button(map, "change_map", GUI.get_font_at(3), GUI.get_font_at(4), custom_width=400)
        thumbnail_stackpanel.linked_button = button
        thumbnail_stackpanel.append(button)
        thumbnail_columns.append(thumbnail_stackpanel)
        thumbnail_columns.scrollable = True
    return thumbnail_columns


def create_menu_maps(maps: list[str], pos: tuple[int, int]):
    game_manager = GameManager.get_instance()
    if game_manager.search_textbox:
        if game_manager.search_textbox not in GUI.elements:
            GUI.elements.append(game_manager.search_textbox)
            GUI.elements.append(game_manager.thumbnail_columns)
        return

    search_textbox = TextBox("search", "search for maps", GUI.get_font_at(0))
    thumbnail_columns = create_columns_maps(maps)

    search_textbox.set_pos(
        (GUI.win.get_width() // 2 - search_textbox.size[0] // 2, 100)
    )
    thumbnail_columns.set_pos(
        (GUI.win.get_width() // 2 - thumbnail_columns.size[0] // 2, 200)
    )

    game_manager.search_textbox = search_textbox
    game_manager.thumbnail_columns = thumbnail_columns

    GUI.elements.append(thumbnail_columns)
    GUI.elements.append(search_textbox)


def main():
    pg.init()

    screen = pg.display.set_mode((1920, 1080), pygame.RESIZABLE)
    clock = pg.time.Clock()

    GUI.win = screen
    GUI.gui_event_handler = handle_gui_events

    GUI.fonts.append(Font(r"./assets/fonts/CriticalRolePlay72.json"))
    GUI.fonts.append(Font(r"./assets/fonts/CriticalRolePlay72B.json"))
    GUI.fonts.append(Font(r"./assets/fonts/CriticalRolePlay124.json"))
    GUI.fonts.append(Font(r"./assets/fonts/CriticalRolePlay30.json"))
    GUI.fonts.append(Font(r"./assets/fonts/CriticalRolePlay30B.json"))

    GUI.frames.append(Frame(r"./assets/images/frame.json"))

    game_manager = GameManager(screen, clock)

    game_manager.setup()

    while True:
        game_manager.step()


if __name__ == "__main__":
    main()
