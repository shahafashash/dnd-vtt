from typing import List, Dict, Generator, Set, Tuple
from utils import cycle
from functools import lru_cache
from pathlib import Path
import json
import cv2
import pygame as pg


class Map:
    def __init__(self, name: str, path: str, tags: List[str], thumbnail: str) -> None:
        current_dir = Path(__file__).parent

        self.__name = name.title()
        self.__path = str(current_dir.joinpath(path).resolve())
        self.__tags = list(map(str.lower, tags))
        self.__thumbnail_path = str(current_dir.joinpath(thumbnail).resolve())
        thumbnail_size = (320, 300 * (9 // 16))
        self.__thumbnail = self.__load_thumbnail(self.__thumbnail_path, thumbnail_size)

        self.__cap = None
        self.__num_frames = None

    @property
    def name(self) -> str:
        return self.__name

    @property
    def path(self) -> str:
        return self.__path

    @property
    def tags(self) -> List[str]:
        return self.__tags

    @property
    def thumbnail(self) -> pg.Surface:
        return self.__thumbnail

    def __load_thumbnail(
        self, thumbnail_path: str, size: Tuple[int, int]
    ) -> pg.Surface:
        thumbnail = pg.image.load(thumbnail_path)
        thumbnail = pg.transform.scale(thumbnail, size)
        return thumbnail

    def load(self) -> Generator[pg.Surface, None, None]:
        if self.__cap is None:
            self.__cap = cv2.VideoCapture(self.path)
            self.__num_frames = int(self.__cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # reset the video to the beginning
        self.__cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        # check if the video needs to be resized
        resize = False
        if (
            self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH) != 1920
            or self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT) != 1080
        ):
            resize = True

        # Initialize the previous surface as None
        prev_surface = None
        for _ in range(self.__num_frames):
            _, frame = self.__cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = frame if not resize else cv2.resize(frame, (1920, 1080))
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame = cv2.flip(frame, 0)

            frame = pg.surfarray.make_surface(frame)

            # Release the previous surface to free memory
            if prev_surface is not None:
                del prev_surface

            prev_surface = frame

            yield frame

        # Release the last surface after the loop
        if prev_surface is not None:
            del prev_surface

    def release(self) -> None:
        if self.__cap is not None:
            self.__cap.release()
            self.__cap = None
            self.__num_frames = None

    def __del__(self) -> None:
        if self.__cap is not None:
            self.__cap.release()


class Loader:
    def __init__(self, maps_file: str) -> None:
        self.__maps = self.__load_maps(maps_file)
        self.__maps_names = sorted(self.__maps.keys())
        self.__tags = self.__get_tags(self.__maps)
        self.__current = None
        self.__buffer = None

    @property
    def maps(self) -> Dict[str, Map]:
        return self.__maps

    @property
    def maps_names(self) -> List[str]:
        return self.__maps_names

    @property
    def tags(self) -> Set[str]:
        return self.__tags

    def __get_tags(self, maps: Dict[str, Map]) -> Set[str]:
        tags = set()
        for map_obj in maps.values():
            tags |= set(map_obj.tags)

        return tags

    def __load_maps(self, maps_file: str) -> Dict[str, Map]:
        with open(maps_file, "r") as f:
            content = json.load(f)

        config = {}
        for item in content:
            name = item["name"].title()
            path = item["path"]
            tags = item["tags"]
            thumbnail = item["thumbnail"]
            config[name] = Map(name, path, tags, thumbnail)

        return config

    @lru_cache(maxsize=256)
    def __find_map(self, map_name: str) -> Map:
        map_name = map_name.title()
        return self.__maps[map_name]

    def load_map(self, map_name: str) -> Generator[pg.Surface, None, None]:
        map_obj = self.__find_map(map_name)
        if self.__current is not None:
            if self.__current.name == map_obj.name:
                return self.__buffer
            else:
                self.__current.release()

        self.__current = map_obj
        self.__buffer = cycle(self.__current.load)
        return self.__buffer

    @lru_cache(maxsize=256)
    def get_map(self, map_name: str) -> Map:
        return self.__find_map(map_name)

    @lru_cache(maxsize=256)
    def find_maps_by_tags(self, tags: List[str]) -> List[Map]:
        tags = set(map(str.lower, tags))
        tags = set(map(str.strip, tags))
        matches = [
            map_obj for map_obj in self.__maps.values() if tags.issubset(map_obj.tags)
        ]
        return matches


if __name__ == "__main__":
    loader = Loader("maps.json")
