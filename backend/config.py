from typing import Dict, List, Tuple, Generator, Set
import os
from queue import Queue
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import cv2
import pygame as pg


class Map:
    def __init__(
        self, name: str, path: str, tags: List[str], thumbnail: str, url: str
    ) -> None:
        current_dir = Path(__file__).parent.parent.absolute()

        self.__name = name.title()
        self.__path = str(current_dir.joinpath(path).resolve())
        self.__tags = list(map(str.lower, tags))
        self.__thumbnail_path = str(current_dir.joinpath(thumbnail).resolve())
        thumbnail_size = (320, 320 * (9 / 16))
        self.__thumbnail = self.__load_thumbnail(self.__thumbnail_path, thumbnail_size)
        self.__url = url

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

    @property
    def url(self) -> str:
        return self.__url

    def __load_thumbnail(
        self, thumbnail_path: str, size: Tuple[int, int]
    ) -> pg.Surface:
        thumbnail = pg.image.load(thumbnail_path)
        thumbnail = pg.transform.scale(thumbnail, size)
        return thumbnail

    def to_dict(self) -> Dict[str, List[str] | str]:
        content = {
            "name": self.__name,
            "path": self.__path,
            "tags": self.__tags,
            "thumbnail": self.__thumbnail_path,
            "url": self.__url,
        }
        return content

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


class Config:
    def __init__(self, config_file: str) -> None:
        self.__config_file = str(Path(config_file).resolve())
        self.__maps = self.__load_maps(self.__config_file)
        self.__maps_names = sorted(self.__maps.keys())
        self.__tags = self.__get_tags(self.__maps)

    @property
    def maps_names(self) -> List[str]:
        return self.__maps_names

    @property
    def tags(self) -> Set[str]:
        return self.__tags

    def __worker_load_maps(self, chunk: List[Dict[str, str]], results: Queue) -> None:
        for item in chunk:
            name = item["name"].title()
            path = item["path"]
            tags = item["tags"]
            thumbnail = item["thumbnail"]
            url = item["url"]
            map_obj = Map(name, path, tags, thumbnail, url)
            results.put(map_obj)

    def __load_maps(self, maps_file: str) -> Dict[str, Map]:
        with open(maps_file, "r") as f:
            content = json.load(f)

        n = len(content)
        workers = os.cpu_count()
        results = Queue(n)
        chunks = [content[i::workers] for i in range(workers)]
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for chunk in chunks:
                executor.submit(self.__worker_load_maps, chunk, results)

            maps = {}
            for _ in range(n):
                map_obj = results.get()
                maps[map_obj.name] = map_obj

        return maps

    def __get_tags(self, maps: Dict[str, Map]) -> Set[str]:
        tags = set()
        for map_obj in maps.values():
            tags |= set(map_obj.tags)

        return tags

    def __drop_to_file(self) -> None:
        content = [map_obj.to_dict() for map_obj in self.__maps.values()]
        with open(self.__config_file, "w") as f:
            json.dump(content, f, indent=2, sort_keys=True)

    @lru_cache(maxsize=1024)
    def get_map(self, map_name: str) -> Map:
        name = map_name.title()
        return self.__maps[name]

    @lru_cache(maxsize=256)
    def get_maps_by_tags(self, tags: List[str]) -> List[Map]:
        tags = set(map(str.strip, map(str.lower, tags)))
        matches = []
        for map_obj in self.__maps.values():
            if tags.union(map_obj.tags):
                matches.append(map_obj)
        return matches

    def add_tag(self, map_name: str, tag: str) -> None:
        name = map_name.title()
        map_tags = self.__maps[name].tags
        tag_lower = tag.lower()
        if tag not in map_tags:
            map_tags.append(tag_lower)
            self.__maps[name].tags = map_tags

        self.__tags.add(tag_lower)
        self.__drop_to_file()

    def remove_tag(self, map_name: str, tag: str) -> None:
        name = map_name.title()
        map_tags = self.__maps[name].tags
        tag_lower = tag.lower()
        if tag in map_tags:
            map_tags.remove(tag_lower)
            self.__maps[name].tags = map_tags

        # count how many times the tag appears in the maps
        count = 0
        for map_obj in self.__maps.values():
            if tag_lower in map_obj.tags:
                count += 1

        # if it doesn't appear in any map, or it appears only once, remove it from the tags
        if count <= 1:
            self.__tags.discard(tag_lower)

        self.__drop_to_file()
