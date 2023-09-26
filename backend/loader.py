from typing import Generator
from tools.utils import cycle
import pygame as pg
from backend.config import Config


class Loader:
    def __init__(self, config: Config) -> None:
        self.__config = config
        self.__current = None
        self.__buffer = None

    def load_map(self, map_name: str) -> Generator[pg.Surface, None, None]:
        map_obj = self.__config.get_map(map_name)
        if self.__current is not None:
            if self.__current.name == map_obj.name:
                return self.__buffer
            else:
                self.__current.release()

        self.__current = map_obj
        self.__buffer = cycle(self.__current.load)
        return self.__buffer
