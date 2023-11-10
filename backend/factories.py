from abc import ABC, abstractmethod
from backend.config import Config
from backend.database.dnd_db import DndDatabase
from backend.searchers.searchers import Searcher, MapSearcher, TokenSearcher, DBSearcher
from backend.searchers.strategies import (
    ScoredMapSearchingStrategy,
    ScoredTokenSearchingStrategy,
    DBSearchingStrategy,
)
from backend.loader import Loader
from backend.settings import Settings, Controls
from backend.tokens import TokensManager
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

    @staticmethod
    @abstractmethod
    def create_controls(settings: Settings) -> Controls:
        raise NotImplementedError("Must implement create_controls method")

    @staticmethod
    @abstractmethod
    def create_tokens_manager(tokens_dir: str) -> TokensManager:
        raise NotImplementedError("Must implement create_tokens_manager method")

    @staticmethod
    @abstractmethod
    def create_token_searcher(config: Config) -> TokenSearcher:
        raise NotImplementedError("Must implement create_token_searcher method")


class SimpleFactory(AbstractFactory):
    @staticmethod
    def create_config(config_file: str) -> Config:
        return Config(config_file)

    @staticmethod
    def create_loader(config: Config) -> Loader:
        return Loader(config)

    @staticmethod
    def create_searcher(config: Config) -> Searcher:
        strategy = ScoredMapSearchingStrategy(config)
        return MapSearcher(strategy)

    @staticmethod
    def create_settings(settings_file: str) -> Settings:
        return Settings(settings_file)

    @staticmethod
    def create_downloader() -> MapsDownloader:
        return MapsDownloader()

    @staticmethod
    def create_controls(settings: Settings) -> Controls:
        return Controls(settings)

    @staticmethod
    def create_tokens_manager(tokens_dir: str) -> TokensManager:
        return TokensManager(tokens_dir)

    @staticmethod
    def create_token_searcher(manager: TokensManager) -> TokenSearcher:
        strategy = ScoredTokenSearchingStrategy(manager)
        return TokenSearcher(strategy)

    @staticmethod
    def create_db_searcher() -> DBSearcher:
        db = DndDatabase()
        strategy = DBSearchingStrategy(db)
        return DBSearcher(strategy)
