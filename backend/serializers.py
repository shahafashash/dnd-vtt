from typing import List, Dict, Any, Set
from abc import ABC, abstractmethod
import pickle
import pygame as pg
from backend.loader import Map, Loader
from main import GameManager, Grid, GridColors
from tools.utils import cycle


class Serializer(ABC):
    @staticmethod
    @abstractmethod
    def serialize() -> bytes:
        raise NotImplementedError("Must implement serialize method")

    @staticmethod
    @abstractmethod
    def deserialize(data: bytes) -> None:
        raise NotImplementedError("Must implement deserialize method")


class GameState:
    def __init__(
        self,
        current_map: str,
        grid_size: int,
        grid_state: Grid,
        grid_color: GridColors,
    ) -> None:
        self.__current_map = current_map
        self.__grid_size = grid_size
        self.__grid_state = grid_state
        self.__grid_color = grid_color

    @property
    def current_map(self) -> str:
        return self.__current_map

    @property
    def grid_size(self) -> int:
        return self.__grid_size

    @property
    def grid_state(self) -> Grid:
        return self.__grid_state

    @property
    def grid_color(self) -> GridColors:
        return self.__grid_color


class GameSerializer(Serializer):
    def serialize(game_state: GameState) -> bytes:
        game_state = GameState(
            game_state.current_map,
            game_state.grid_size,
            game_state.grid_state,
            game_state.grid_color,
        )
        return pickle.dumps(game_state)

    def deserialize(data: bytes) -> GameState:
        game_state = pickle.loads(data)
        return game_state
