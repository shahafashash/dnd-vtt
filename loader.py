from typing import List, Dict, Generator
from itertools import cycle
from functools import lru_cache
from pathlib import Path
import json
import cv2
import pygame as pg


class Map:
    def __init__(self, name: str, path: str, tags: List[str]) -> None:
        current_dir = Path(__file__).parent

        self.name = name.title()
        self.path = str(current_dir.joinpath(path).resolve())
        self.tags = list(map(str.lower, tags))
        self.cap = None
        self.num_frames = None

    def load(self) -> Generator[pg.Surface, None, None]:
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.path)
            self.num_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # reset the video to the beginning
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        # check if the video needs to be resized
        resize = False
        if (
            self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) != 1920
            or self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) != 1080
        ):
            resize = True
        for _ in range(self.num_frames):
            _, frame = self.cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = frame if not resize else cv2.resize(frame, (1920, 1080))
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame = cv2.flip(frame, 0)

            frame = pg.surfarray.make_surface(frame)
            yield frame

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.num_frames = None

    def __del__(self) -> None:
        if self.cap is not None:
            self.cap.release()


class Loader:
    def __init__(self, maps_file: str) -> None:
        self._maps = self.__load_maps(maps_file)
        self.__current = None
        self.__buffer = None

    @property
    def maps(self) -> Dict[str, Map]:
        return self._maps

    @maps.setter
    def maps(self, value: Dict[str, Map]) -> None:
        raise AttributeError("maps is a read-only property")

    def __load_maps(self, maps_file: str) -> Dict[str, Map]:
        with open(maps_file, "r") as f:
            content = json.load(f)

        config = {}
        for item in content:
            name = item["name"].title()
            path = item["path"]
            tags = item["tags"]
            config[name] = Map(name, path, tags)

        return config

    @lru_cache(maxsize=20)
    def __find_map(self, map_name: str) -> Map:
        map_name = map_name.title()
        return self._maps[map_name]

    def load_map(self, map_name: str) -> Generator[pg.Surface, None, None]:
        map_obj = self.__find_map(map_name)
        if self.__current is not None:
            if self.__current.name == map_obj.name:
                return self.__buffer
            else:
                self.__current.release()

        self.__current = map_obj
        self.__buffer = cycle(self.__current.load())
        return self.__buffer
