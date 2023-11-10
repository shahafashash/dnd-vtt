from typing import List
from abc import ABC, abstractmethod
from functools import lru_cache
from backend.searchers.strategies import SearchingStrategy


class Searcher(ABC):
    @abstractmethod
    def search(self, query: str, n: int = -1) -> List[str]:
        raise NotImplementedError("Must implement search method")


class MapSearcher(Searcher):
    def __init__(self, strategy: SearchingStrategy) -> None:
        self.__strategy = strategy

    @lru_cache(maxsize=1024)
    def search(self, query: str, n: int = -1) -> List[str]:
        matches = self.__strategy.search(query, n)
        return matches


class TokenSearcher(Searcher):
    def __init__(self, strategy: SearchingStrategy) -> None:
        self.__strategy = strategy

    @lru_cache(maxsize=1024)
    def search(self, query: str, n: int = -1) -> List[str]:
        matches = self.__strategy.search(query, n)
        return matches


class DBSearcher(Searcher):
    def __init__(self, strategy: SearchingStrategy) -> None:
        self.__strategy = strategy

    @lru_cache(maxsize=1024)
    def search(self, query: str, n: int = -1) -> List[str]:
        matches = self.__strategy.search(query, n)
        return matches
