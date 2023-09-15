from typing import List, Tuple, Any, Set, Dict
from abc import ABC, abstractmethod
from collections import defaultdict
import operator
import difflib


class Searcher(ABC):
    def __init__(self, data: Any) -> None:
        self._data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data: Any):
        raise AttributeError("Cannot set data attribute")

    @abstractmethod
    def search(self, query: str, n: int = -1) -> List[str]:
        raise NotImplementedError("Must implement search method")


class MapSearcher(Searcher):
    def __init__(self, data: List[Dict[str, Any]]) -> None:
        super().__init__(data)

        self._maps = self.__get_maps()
        self._tags_mapping = self.__create_tags_mapping()
        self._tags = self.__get_tags()

    def __get_maps(self) -> List[Dict[str, Any]]:
        maps = [item["name"] for item in self._data]
        maps.sort()
        return maps

    def __create_tags_mapping(self) -> Dict[str, Set[str]]:
        tags_mapping = defaultdict(set)

        for item in self._data:
            for tag in item["tags"]:
                tags_mapping[tag].add(item["name"])

        return tags_mapping

    def __get_tags(self) -> List[str]:
        tags = set()
        for item in self._data:
            tags |= set(item["tags"])

        return list(tags)

    def __get_query_tags(self, query: str) -> List[str]:
        query_tags = list(set(list(map(str.strip, query.split()))))
        tags_matches = set()
        for tag in query_tags:
            matches = difflib.get_close_matches(tag, self._tags, n=5, cutoff=0.5)
            tags_matches |= set(matches)

        return list(tags_matches)

    def __get_maps_scores(self, query_tags: List[str]) -> Dict[str, int]:
        scores = defaultdict(lambda: 0)
        for tag in query_tags:
            for map_name in self._tags_mapping[tag]:
                scores[map_name] += 1

        # sort the scores by the number of tags matched in descending order and then by the map name in ascending order
        scores = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return scores

    def __get_best_matches(self, query_tags: List[str], maps: List[str]) -> List[str]:
        matches = []
        map_ratios = []
        for map_name in maps:
            map_ratios.clear()
            for tag in query_tags:
                # check the matching ratio between the tag and the map name
                map_ratios.append(difflib.SequenceMatcher(None, tag, map_name).ratio())
            map_ratio = sum(map_ratios) / len(map_ratios)
            matches.append((map_name, map_ratio))

        matches.sort(key=operator.itemgetter(1), reverse=True)
        matches = [map_name for map_name, _ in matches]
        return matches

    def search(self, query: str, n: int = -1) -> List[str]:
        if n < 0:
            n = len(self._data)

        if query.strip() == "":
            return self._maps[:n]

        query_tags = self.__get_query_tags(query)
        maps_scores = self.__get_maps_scores(query_tags)
        maps = [map_name for map_name, _ in maps_scores]
        matches = self.__get_best_matches(query_tags, maps)
        return matches[:n]
