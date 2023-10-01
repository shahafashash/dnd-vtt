from typing import overload, List, Tuple
import sys
from pathlib import Path
from queue import Queue
from threading import Thread
from functools import partial
from pytube import YouTube
import cv2
from nltk.tokenize import word_tokenize
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent.absolute()))
from backend.config import Map


class MapsDownloader:
    def __init__(self) -> None:
        self.__threads = dict[str, Thread]()
        self.__downloads = Queue[Tuple[str, float]]()
        self.__finished = Queue[Tuple[str, Map]]()

    def __generate_default_tags(self, map_name: str) -> List[str]:
        # clean map name from unicode characters, special characters and spaces
        map_name = map_name.encode("ascii", "ignore").decode("ascii")
        map_name.strip().lower()
        tags = word_tokenize(map_name)
        return tags

    def __on_progress(
        self, stream: YouTube, chunk: bytes, bytes_remaining: int, pbar: tqdm
    ) -> None:
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size
        percentage_of_completion = round(percentage_of_completion, 2)
        map_name = self.__get_map_name(stream)
        self.__downloads.put((map_name, percentage_of_completion))
        pbar.update(percentage_of_completion * 100 - pbar.n)

    def __on_complete(self, stream: YouTube, file_path: str, pbar: tqdm) -> None:
        map_name = self.__get_map_name(stream)
        map_path = Path(file_path)
        thumbnail_path = self.__generate_thumbnail(map_path)
        tags = self.__generate_default_tags(map_name)
        map_obj = Map(map_name, map_path, tags, thumbnail_path, stream.url)
        self.__finished.put((map_obj.url, map_obj))
        pbar.close()

    def __generate_thumbnail(self, map_path: str) -> str:
        cap = cv2.VideoCapture(map_path)
        map_path = Path(map_path)
        success, frame = cap.read()
        while not success and cap.isOpened():
            success, frame = cap.read()

        cap.release()

        if not success:
            # remove corrupted file
            map_path.unlink()
            raise Exception("Map is corrupted")

        # save thumbnail
        thumbnail_path = self.__get_thumbnails_path()
        thumbnail_path = Path(thumbnail_path).joinpath(map_path.stem + ".png")
        cv2.imwrite(str(thumbnail_path), frame)
        return str(thumbnail_path)

    def __get_assets_path(self) -> Path:
        assets_path = Path(__file__).parent.parent.absolute().joinpath("assets")
        return assets_path

    def __get_maps_path(self) -> str:
        maps_path = self.__get_assets_path().joinpath("maps")
        return str(maps_path)

    def __get_thumbnails_path(self) -> str:
        thumbnails_path = self.__get_assets_path().joinpath("thumbnails")
        return str(thumbnails_path)

    def __get_map_name(self, stream: YouTube) -> str:
        filename = stream.default_filename
        map_name = Path(filename).stem.title()
        return map_name

    def __download_worker(self, input_: Map | str) -> None:
        if isinstance(input_, Map):
            url = input_.url
        else:
            url = input_

        pbar = tqdm(total=100, desc="Downloading map", unit="%", leave=False, ncols=80)
        on_progress = partial(self.__on_progress, pbar=pbar)
        on_complete = partial(self.__on_complete, pbar=pbar)

        yt = YouTube(
            url,
            on_progress_callback=on_progress,
            on_complete_callback=on_complete,
        )
        stream = yt.streams.filter(file_extension="mp4").get_highest_resolution()
        filename = stream.default_filename
        maps_path = self.__get_maps_path()

        stream.download(output_path=maps_path, filename=filename)

    @overload
    def download(self, map_obj: Map) -> None:
        ...

    @overload
    def download(self, url: str) -> None:
        ...

    def download(self, input_: Map | str) -> Map:
        if isinstance(input_, Map):
            url = input_.url
        else:
            url = input_

        thread = Thread(target=self.__download_worker, args=(input_,), daemon=True)
        self.__threads[url] = thread
        thread.start()

    def get_progress(self) -> List[Tuple[str, float]]:
        progress = []
        while not self.__downloads.empty():
            progress.append(self.__downloads.get())
        return progress

    def get_finished(self) -> List[Map]:
        finished = []
        while not self.__finished.empty():
            url, map_obj = self.__finished.get()
            self.__threads.pop(url)
            finished.append(map_obj)
        return finished

    def wait(self) -> None:
        for thread in self.__threads.values():
            thread.join()


if __name__ == "__main__":
    from argparse import ArgumentParser
    from backend.config import Config

    parser = ArgumentParser()
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        required=True,
        help="Youtube url of the map to download",
    )
    args = parser.parse_known_args()[0]
    url = args.url
    downloader = MapsDownloader()
    map_obj = downloader.download(url)
    downloader.wait()
    config = Config(str(Path(__file__).parent.parent.absolute().joinpath("maps.json")))
    config.add_map(map_obj)
