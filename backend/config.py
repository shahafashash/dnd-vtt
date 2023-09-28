from typing import Dict, List, Tuple, Generator, Set
import os
from queue import Queue
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import cv2
import pygame as pg
from nltk.tokenize import word_tokenize


class Map:
    def __init__(
        self,
        name: str,
        path: str,
        tags: List[str],
        thumbnail: str,
        url: str,
        favorite: bool = False,
    ) -> None:
        current_dir = Path(__file__).parent.parent.absolute()

        self.__name = name.title()
        self.__path = str(current_dir.joinpath(path).resolve())
        self.__tags = list(map(str.lower, tags))
        self.__thumbnail_path = str(current_dir.joinpath(thumbnail).resolve())
        thumbnail_size = (320, 320 * (9 / 16))
        self.__thumbnail = self.__load_thumbnail(self.__thumbnail_path, thumbnail_size)
        self.__url = url
        self.__favorite = favorite

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

    @property
    def favorite(self) -> bool:
        return self.__favorite

    def __load_thumbnail(
        self, thumbnail_path: str, size: Tuple[int, int]
    ) -> pg.Surface:
        thumbnail = pg.image.load(thumbnail_path)
        thumbnail = pg.transform.scale(thumbnail, size)
        return thumbnail

    def to_dict(self) -> Dict[str, List[str] | str | bool]:
        # get the part of the path from the assets folder to the file
        assets_index = Path(self.__path).parts.index("assets")
        path = Path("assets").joinpath(*Path(self.__path).parts[assets_index + 1 :])
        thumbnail_path = Path("assets").joinpath(
            *Path(self.__thumbnail_path).parts[assets_index + 1 :]
        )
        content = {
            "name": self.__name,
            "path": str(path),
            "tags": self.__tags,
            "thumbnail": str(thumbnail_path),
            "url": self.__url,
            "favorite": self.__favorite,
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
            favorite = item["favorite"]
            map_obj = Map(name, path, tags, thumbnail, url, favorite)
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

    def __update_config_file(self) -> None:
        content = [map_obj.to_dict() for map_obj in self.__maps.values()]
        with open(self.__config_file, "w") as f:
            json.dump(content, f, indent=2, sort_keys=True)

    @lru_cache(maxsize=256)
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

    @lru_cache(maxsize=256)
    def get_favorite_maps(self) -> List[Map]:
        matches = []
        for map_obj in self.__maps.values():
            if map_obj.favorite:
                matches.append(map_obj)
        return matches

    def add_tags(self, map_name: str, tags: str) -> None:
        name = map_name.title()
        map_tags = self.__maps[name].tags
        new_tags = word_tokenize(tags)
        for tag in new_tags:
            tag_lower = tag.lower().strip()
            if tag not in map_tags:
                map_tags.append(tag_lower)
            self.__tags.add(tag_lower)

        self.__update_config_file()

    def remove_tags(self, map_name: str, tags: str) -> None:
        name = map_name.title()
        map_tags = self.__maps[name].tags
        tags_to_remove = word_tokenize(tags)
        for tag in tags_to_remove:
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

        self.__update_config_file()

    def set_favorite(self, map_name: str, favorite: bool) -> None:
        name = map_name.title()
        self.__maps[name].favorite = favorite
        self.__update_config_file()

    def remove_favorite(self, map_name: str) -> None:
        name = map_name.title()
        self.__maps[name].favorite = False
        self.__update_config_file()

    def add_map(self, map_obj: Map) -> None:
        if map_obj.name in self.__maps_names:
            raise ValueError(f"Map {map_obj.name} already exists")
        self.__maps[map_obj.name] = map_obj
        self.__maps_names.append(map_obj.name)
        self.__tags |= set(map_obj.tags)
        self.__update_config_file()

    def remove_map(self, map_name: str) -> None:
        name = map_name.title()
        if name not in self.__maps_names:
            raise ValueError(f"Map {name} does not exist")

        map_obj = self.__maps.pop(name)
        for tag in map_obj.tags:
            self.remove_tag(name, tag)
        self.__maps_names.remove(name)
        # removing the thumbnail and the map file
        Path(map_obj.thumbnail).unlink()
        Path(map_obj.path).unlink()
        self.__update_config_file()

    def rename_map(self, map_name: str, new_name: str) -> None:
        name = map_name.title()
        new_name = new_name.title()
        if name not in self.__maps_names:
            raise ValueError(f"Map {name} does not exist")

        if new_name in self.__maps_names:
            raise ValueError(f"Map {new_name} already exists")

        map_obj = self.__maps.pop(name)
        new_map_obj = Map(
            new_name,
            map_obj.path,
            map_obj.tags,
            map_obj.thumbnail,
            map_obj.url,
            map_obj.favorite,
        )
        self.__maps[new_name] = new_map_obj
        self.__maps_names.remove(name)
        self.__maps_names.append(new_name)
        self.__update_config_file()
