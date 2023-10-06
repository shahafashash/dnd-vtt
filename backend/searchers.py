from typing import List, Set, Dict
from abc import ABC, abstractmethod
from collections import defaultdict
import operator
import difflib
from functools import lru_cache
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet

try:
    from backend.config import Config
    from backend.tokens import TokensManager
except ModuleNotFoundError:
    from config import Config
    from tokens import TokensManager


class SearchingStrategy(ABC):
    @abstractmethod
    def search(self, query: str, n: int = -1) -> List[str]:
        raise NotImplementedError("Must implement search method")


class BasicMapSearchingStrategy(SearchingStrategy):
    def __init__(self, config: Config, accuracy: float = 0.5) -> None:
        self.__config = config
        self.__accuracy = accuracy
        self.__maps_names = self.__config.maps_names
        self.__tags = self.__config.tags
        self.__tags_mapping = self.__create_tags_mapping()
        self.__n = len(self.__maps_names)

    def __create_tags_mapping(self) -> Dict[str, Set[str]]:
        tags_mapping = defaultdict(set)
        for map_name in self.__maps_names:
            map_obj = self.__config.get_map(map_name)
            for tag in map_obj.tags:
                tags_mapping[tag].add(map_name)

        return tags_mapping

    def __get_query_tags(self, query: str) -> List[str]:
        query_tags = list(set(list(map(str.strip, query.split()))))
        tags_matches = set()
        # self.__accuracy is a float between 0 and 1. tries is the number of times we will try to find a match
        tries = int(1.0 / self.__accuracy) + 1
        for tag in query_tags:
            for i in range(tries):
                cutoff = 1.0 - (self.__accuracy * i)
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

    def search(self, query: str, n: int = -1) -> List[str]:
        if n < 0:
            n = self.__n

        if query.strip() == "":
            return self.__maps_names

        query_tags = self.__get_query_tags(query)
        maps_scores = self.__get_maps_scores(query_tags)
        maps = [map_name for map_name, _ in maps_scores]
        matches = self.__get_best_matches(query_tags, maps)
        return matches[:n]


class ScoredMapSearchingStrategy(SearchingStrategy):
    def __init__(self, config: Config) -> None:
        self.__config = config
        self.__maps_names = self.__config.maps_names
        self.__tags_mapping = self.__create_tags_mapping()
        self.__n = len(self.__maps_names)

    def __create_tags_mapping(self) -> Dict[str, Set[str]]:
        tags_mapping = defaultdict(set)
        for map_name in self.__maps_names:
            map_obj = self.__config.get_map(map_name)
            for tag in map_obj.tags:
                tags_mapping[tag].add(map_name)

        return tags_mapping

    def __get_query_tokens(self, query: str) -> List[str]:
        return word_tokenize(query)

    def __get_query_tags_scores(self, query: str) -> Dict[str, int]:
        scores = defaultdict(lambda: 0)
        query_tokens = self.__get_query_tokens(query)
        # sum the ratios of each token to each tag
        for token in query_tokens:
            for tag, maps in self.__tags_mapping.items():
                ratio = difflib.SequenceMatcher(None, token, tag).ratio()
                for map_name in maps:
                    scores[map_name] += ratio
        return scores

    def __get_maps_names_scores(self, query: str) -> Dict[str, int]:
        scores = defaultdict(lambda: 0)
        query_as_title = query.title()
        # sum the ratios of each token to each map name
        for map_name in self.__maps_names:
            score = 0
            for token in query_as_title.split():
                ratio = difflib.SequenceMatcher(None, token, map_name).ratio()
                score += ratio
            scores[map_name] = score
        return scores

    def __get_query_tags_synonyms(self, query: str) -> Dict[str, Set[str]]:
        query_tokens = self.__get_query_tokens(query)
        tokens_synonyms = defaultdict(set)
        for token in query_tokens:
            for syn in wordnet.synsets(token):
                for l in syn.lemmas():
                    tokens_synonyms[token].add(l.name())
        return tokens_synonyms

    def __get_query_synonyms_scores(self, query: str) -> Dict[str, int]:
        scores = defaultdict(lambda: 0)
        query_tokens = self.__get_query_tokens(query)
        tokens_synonyms = self.__get_query_tags_synonyms(query)
        for token in query_tokens:
            for synonym in tokens_synonyms[token]:
                for tag, maps in self.__tags_mapping.items():
                    ratio = difflib.SequenceMatcher(None, synonym, tag).ratio()
                    for map_name in maps:
                        scores[map_name] += ratio
        return scores

    def __get_best_matches(self, query: str, maps: List[str]) -> List[str]:
        matches = []
        query_tags_scores = self.__get_query_tags_scores(query)
        maps_names_scores = self.__get_maps_names_scores(query)
        synonyms_scores = self.__get_query_synonyms_scores(query)
        for map_name in maps:
            map_name_score = maps_names_scores[map_name]
            query_tags_score = query_tags_scores[map_name]
            synonyms_score = synonyms_scores[map_name]
            map_score = (
                (0.6 * map_name_score)
                + (0.4 * query_tags_score)
                + (0.1 * synonyms_score)
            )
            matches.append((map_name, map_score))

        matches.sort(key=operator.itemgetter(1), reverse=True)
        matches = [map_name for map_name, _ in matches]
        return matches

    def search(self, query: str, n: int = -1) -> List[str]:
        if n < 0:
            n = self.__n

        if query.strip() == "":
            return self.__maps_names

        query = query.strip().lower()
        matches = self.__get_best_matches(query, self.__maps_names)
        return matches[:n]


class ScoredTokenSearchingStrategy(SearchingStrategy):
    def __init__(self, tokens_manager: TokensManager) -> None:
        self.__tokens_manager = tokens_manager
        self.__tokens_names = self.__tokens_manager.tokens_names
        self.__n = len(self.__tokens_names)

    def __get_query_tokens(self, query: str) -> List[str]:
        return word_tokenize(query)

    def __get_query_tokens_synonyms(self, query: str) -> Dict[str, Set[str]]:
        query_tokens = self.__get_query_tokens(query)
        tokens_synonyms = defaultdict(set)
        for token in query_tokens:
            for syn in wordnet.synsets(token):
                for l in syn.lemmas():
                    tokens_synonyms[token].add(l.name())
        return tokens_synonyms

    def __get_query_synonyms_scores(self, query: str) -> Dict[str, int]:
        scores = defaultdict(lambda: 0)
        query_tokens = self.__get_query_tokens(query)
        tokens_synonyms = self.__get_query_tokens_synonyms(query)
        for token in query_tokens:
            for synonym in tokens_synonyms[token]:
                for token_name in self.__tokens_names:
                    ratio = difflib.SequenceMatcher(None, synonym, token_name).ratio()
                    scores[token_name] += ratio
        return scores

    def __get_tokens_names_scores(self, query: str) -> Dict[str, int]:
        scores = defaultdict(lambda: 0)
        query_tokens = self.__get_query_tokens(query)
        # sum the ratios of each token to each token name
        for token_name in self.__tokens_names:
            score = 0
            for token in query_tokens:
                ratio = difflib.SequenceMatcher(None, token, token_name).ratio()
                score += ratio
            scores[token_name] = score
        return scores

    def __get_best_matches(self, query: str, tokens: List[str]) -> List[str]:
        matches = []
        tokens_names_scores = self.__get_tokens_names_scores(query)
        synonyms_scores = self.__get_query_synonyms_scores(query)
        for token_name in tokens:
            token_name_score = tokens_names_scores[token_name]
            synonyms_score = synonyms_scores[token_name]
            token_score = (0.9 * token_name_score) + (0.1 * synonyms_score)
            matches.append((token_name, token_score))

        matches.sort(key=operator.itemgetter(1), reverse=True)
        matches = [token_name for token_name, _ in matches]
        return matches

    def search(self, query: str, n: int = -1) -> List[str]:
        if n < 0:
            n = self.__n

        if query.strip() == "":
            return self.__tokens_names

        query = query.strip().lower()
        matches = self.__get_best_matches(query, self.__tokens_names)
        return matches[:n]


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


if __name__ == "__main__":
    # config = Config("maps.json")
    # strategy = ScoredMapSearchingStrategy(config)
    # searcher = MapSearcher(strategy)
    # print(searcher.search("ships", 5))

    # strategy_old = BasicMapSearchingStrategy(config)
    # searcher_old = MapSearcher(strategy_old)
    # print(searcher_old.search("ships", 5))

    tokens_manager = TokensManager("assets/tokens")
    strategy = ScoredTokenSearchingStrategy(tokens_manager)
    searcher = TokenSearcher(strategy)
    print(searcher.search("dragon", 5))
