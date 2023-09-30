from abc import ABC, abstractmethod
from backend.config import Config, Map
from backend.searchers import Searcher, MapSearcher, BasicSearchingStrategy
from backend.loader import Loader
from backend.settings import Settings
from tools.downloader import MapsDownloader


class AbstractFactory(ABC):
    @staticmethod
    @abstractmethod
    def create_config(config_file: str) -> Config:
        raise NotImplementedError("Must implement create_config method")

    @staticmethod
    @abstractmethod
    def create_loader(config: Config) -> Loader:
        raise NotImplementedError("Must implement create_loader method")

    @staticmethod
    @abstractmethod
    def create_searcher(config: Config) -> Searcher:
        raise NotImplementedError("Must implement create_searcher method")

    @staticmethod
    @abstractmethod
    def create_settings(settings_file: str) -> Settings:
        raise NotImplementedError("Must implement create_settings method")

    @staticmethod
    @abstractmethod
    def create_downloader() -> MapsDownloader:
        raise NotImplementedError("Must implement create_downloader method")


class SimpleFactory(AbstractFactory):
    @staticmethod
    def create_config(config_file: str) -> Config:
        return Config(config_file)

    @staticmethod
    def create_loader(config: Config) -> Loader:
        return Loader(config)

    @staticmethod
    def create_searcher(config: Config) -> Searcher:
        strategy = BasicSearchingStrategy(config)
        return MapSearcher(strategy)

    @staticmethod
    def create_settings(settings_file: str) -> Settings:
        return Settings(settings_file)

    @staticmethod
    def create_downloader() -> MapsDownloader:
        return MapsDownloader()
