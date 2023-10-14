from typing import Dict, List
import os
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import io
import pygame as pg
import cv2
import numpy as np


class Token:
    def __init__(self, name: str, path: str) -> None:
        current_dir = Path(__file__).parent.parent.absolute()

        self.__name = name.title()
        self.__path = str(current_dir.joinpath(path).resolve())
        self.__token = self.__load_token(self.__path)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def path(self) -> str:
        return self.__path

    @property
    def token(self) -> pg.Surface:
        return self.__token

    def __remove_background(self, path: str) -> io.BytesIO:
        img = cv2.imread(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)[1]
        mask = 255 - mask
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.GaussianBlur(
            mask, (0, 0), sigmaX=2, sigmaY=2, borderType=cv2.BORDER_DEFAULT
        )
        mask = (2 * (mask.astype(np.float32)) - 255.0).clip(0, 255).astype(np.uint8)
        result = img.copy()
        result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
        result[:, :, 3] = mask

        _, buffer = cv2.imencode(".png", result)
        io_buffer = io.BytesIO(buffer)
        io_buffer.seek(0)
        return io_buffer

    def __load_token(self, path: str) -> pg.Surface:
        token_bytes = self.__remove_background(path)
        token = pg.image.load(token_bytes, path)
        return token

    def to_dict(self) -> Dict[str, str]:
        content = {"name": self.name, "path": self.path}
        return content


class TokensManager:
    def __init__(self, tokens_dir: str) -> None:
        self.__tokens_dir = str(Path(tokens_dir).resolve())
        self.__tokens = self.__load_tokens(self.__tokens_dir)
        self.__tokens_names = sorted(self.__tokens.keys())

    @property
    def tokens_names(self) -> List[str]:
        return self.__tokens_names

    def __worker_load_tokens(self, chunk: List[str], result: Queue) -> None:
        for token_path in chunk:
            token_name = Path(token_path).stem.title()
            token = Token(token_name, token_path)
            result.put(token)

    def __load_tokens(self, tokens_dir: str) -> Dict[str, Token]:
        tokens_paths = list(Path(tokens_dir).glob("*.png"))
        tokens_paths = [str(path.resolve()) for path in tokens_paths]

        n = len(tokens_paths)
        workers = os.cpu_count()
        chunks = [tokens_paths[i::workers] for i in range(workers)]
        result = Queue(n)
        with ThreadPoolExecutor() as executor:
            for chunk in chunks:
                executor.submit(self.__worker_load_tokens, chunk, result)

        tokens = {}
        for _ in range(n):
            token = result.get()
            tokens[token.name] = token

        return tokens

    @lru_cache(maxsize=256)
    def get_token(self, token_name: str) -> Token:
        name = token_name.title()
        return self.__tokens[name]
