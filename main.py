import tracemalloc
import cv2
import pygame as pg
import json
from collections import deque
from enum import Enum
from gui import *


class Event(Enum):
    PLAY = 0
    CHANGE_MAP = 1


class State(Enum):
    GAME_MAIN_MENU = 0
    GAME_RUM_MAP = 1


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
        self.maps = load_maps("maps.json")

        self.current_map_name = None
        self.current_map_frames = None

        self.grid_size = 50

        self.state = State.GAME_MAIN_MENU
        self.event_que = deque()

    def get_instance():
        return GameManager._instance

    def add_event(self, event):
        self.event_que.append(event)

    def handle_game_events(self):
        while len(self.event_que):
            event = self.event_que.popleft()
            if event.type == Event.CHANGE_MAP:
                self.current_map_name = event.data
                self.current_map_frames = load_frames(self.current_map_name)
                print(self.current_map_name)
                self.state = State.GAME_RUM_MAP
            elif event.type == Event.PLAY:
                self.state = State.GAME_RUM_MAP

    def step(self):
        self.handle_game_events()

        if self.state == State.GAME_MAIN_MENU:
            self.main_menu()
        elif self.state == State.GAME_RUM_MAP:
            self.run_map()

    def main_menu(self):
        background = get_background()

        for event in pg.event.get():
            GUI.event_handle(event)
            if event.type == pg.QUIT:
                exit(0)
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    exit(0)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                create_menu_maps(self.maps, event.pos)

        GUI.step()

        self.screen.blit(background, (0, 0))
        GUI.draw()

        # update the display and tick the clock
        pg.display.flip()
        self.clock.tick(30)

    def run_map(self):
        for event in pg.event.get():
            GUI.event_handle(event)
            if event.type == pg.QUIT:
                exit(0)
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    exit(0)
                # plus and minus of num pad
                elif event.key == pg.K_KP_PLUS:
                    self.grid_size += 5
                elif event.key == pg.K_KP_MINUS:
                    self.grid_size -= 5
                    if self.grid_size < 5:
                        self.grid_size = 5
            # right click
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                create_menu_maps(self.maps, event.pos)

        GUI.step()

        # draw the frame
        frame = next(self.current_map_frames, None)
        if frame is None:
            self.current_map_frames = load_frames(self.current_map_name)
            frame = next(self.current_map_frames)

        self.screen.blit(frame, (0, 0))
        draw_grid(self.screen, self.grid_size)

        GUI.draw()

        # update the display and tick the clock
        pg.display.flip()
        self.clock.tick(30)


def load_frame(path: str, frame: int):
    """load a frame from a video file into a pygame surface"""
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
    ret, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pg.surfarray.make_surface(frame)
    cap.release()
    return frame


def get_number_of_frames(path: str):
    """return the number of frames in a video file"""
    cap = cv2.VideoCapture(path)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return frames


def draw_grid(surf, size=50):
    width, height = surf.get_size()
    color = pg.Color("black")
    for i in range(0, width, size):
        pg.draw.line(surf, color, (i, 0), (i, height))
    for i in range(0, height, size):
        pg.draw.line(surf, color, (0, i), (width, i))


def draw_hex_grid(surf):
    """draws a hexagonic grid on a surface, each hexagon is of size GRID_SIZE"""
    raise NotImplementedError


def load_frames(path: str):
    """load a video file into a list of pygame surfaces"""
    map_path = f"assets/maps/{path}.mp4"
    cap = cv2.VideoCapture(map_path)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    for _ in range(frames):
        _, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pg.surfarray.make_surface(frame)
        frame = pg.transform.rotate(frame, 90)
        yield frame

    cap.release()


def handle_gui_events(event: str):
    print(event)
    if event["key"] == "change_map":
        game_event = GameEvent(Event.CHANGE_MAP, event["text"])
        GameManager.get_instance().add_event(game_event)


def load_maps(json_path: str):
    with open(json_path, "r") as f:
        maps_content = json.load(f)

    maps = [map["name"] for map in maps_content]
    return maps


def get_background():
    image_path = "assets/images/background.jpg"
    image = pg.image.load(image_path)
    return image


def create_menu_maps(maps: list[str], pos: tuple[int, int]):
    context_menu = ContextMenu(pos)
    for map in maps:
        context_menu.add_button(map, "change_map")
    GUI.elements.append(context_menu)


def main():
    pg.init()

    screen = pg.display.set_mode((1920, 1080), pygame.RESIZABLE)
    clock = pg.time.Clock()
    game_manager = GameManager(screen, clock)

    GUI.win = screen
    GUI.font = pg.font.SysFont("Arial", 30)
    GUI.gui_event_handler = handle_gui_events

    while True:
        game_manager.step()


if __name__ == "__main__":
    tracemalloc.start()
    main()
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    for stat in top_stats[:10]:
        print(stat)

    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage is {current / 10**6}MB; Peak was {peak / 10**6}MB")
    tracemalloc.stop()
