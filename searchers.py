from typing import List, Any, Set, Dict
from abc import ABC, abstractmethod
from collections import defaultdict
import operator
import difflib
from functools import lru_cache
from loader import Loader


class Searcher(ABC):
    @abstractmethod
    def search(self, query: str, n: int = -1) -> List[str]:
        raise NotImplementedError("Must implement search method")


class MapSearcher(Searcher):
    def __init__(self, loader: Loader, accuracy: float = 0.05) -> None:
        self.__loader = loader
        self.__accuracy = accuracy
        self.__maps_names = self.__loader.maps_names
        self.__tags = self.__loader.tags
        self.__tags_mapping = self.__create_tags_mapping()

    @property
    def accuracy(self) -> float:
        return self.__accuracy

    def __create_tags_mapping(self) -> Dict[str, Set[str]]:
        tags_mapping = defaultdict(set)
        for map_name in self.__maps_names:
            map_obj = self.__loader.get_map(map_name)
            for tag in map_obj.tags:
                tags_mapping[tag].add(map_name)

        return tags_mapping

    def __get_query_tags(self, query: str) -> List[str]:
        query_tags = list(set(list(map(str.strip, query.split()))))
        tags_matches = set()
        # self.__accuracy is a float between 0 and 1. tries is the number of times we will try to find a match
        tries = int(1.0 / self.__accuracy) + 1
        # tries = int(100 // self.__accuracy) + 1
        for tag in query_tags:
            for i in range(tries):
                cutoff = 1.0 - (self.accuracy * i)
                matches = difflib.get_close_matches(
                    tag, self.__tags, n=5, cutoff=cutoff
                )
                if len(matches) != 0:
                    tags_matches |= set(matches)
                    break

        return list(tags_matches)

    def __get_maps_scores(self, query_tags: List[str]) -> Dict[str, int]:
        scores = defaultdict(lambda: 0)
        for tag in query_tags:
            for map_name in self.__tags_mapping[tag]:
                scores[map_name] += 1

        # sort the scores by the number of tags matched in descending order and then by the map name in ascending order
        scores = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return scores

    def __get_best_matches(self, query_tags: List[str], maps: List[str]) -> List[str]:
        matches = []
        num_tags = len(query_tags)
        for map_name in maps:
            map_ratio = 0
            for tag in query_tags:
                # check the matching ratio between the tag and the map name
                ratio = difflib.SequenceMatcher(None, tag, map_name).ratio()
                map_ratio += ratio
            map_ratio = map_ratio / num_tags
            matches.append((map_name, map_ratio))

        matches.sort(key=operator.itemgetter(1), reverse=True)
        matches = [map_name for map_name, _ in matches]
        return matches

    @lru_cache(maxsize=256)
    def search(self, query: str, n: int = -1) -> List[str]:
        if n < 0:
            n = len(self.__maps_names)

        if query.strip() == "":
            return self.__maps_names[:n]

        query_tags = self.__get_query_tags(query)
        maps_scores = self.__get_maps_scores(query_tags)
        maps = [map_name for map_name, _ in maps_scores]
        matches = self.__get_best_matches(query_tags, maps)
        return matches[:n]
