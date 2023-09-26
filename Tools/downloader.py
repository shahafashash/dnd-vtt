from typing import overload, List
from pathlib import Path
from pytube import YouTube
import cv2
from nltk.tokenize import word_tokenize
from ..backend.config import Map


class MapsDownloader:
    def __generate_default_tags(map_name: str) -> List[str]:
        # clean map name from unicode characters, special characters and spaces
        map_name = map_name.encode("ascii", "ignore").decode("ascii")
        map_name.strip().lower()
        tags = word_tokenize(map_name)
        return tags

    @staticmethod
    @overload
    def download(map_obj: Map) -> None:
        ...

    @staticmethod
    @overload
    def download(url: str) -> None:
        ...

    @staticmethod
    def download(input_: Map | str) -> Map:
        if isinstance(input_, Map):
            url = input_.url
        else:
            url = input_
        yt = YouTube(url)
        stream = yt.streams.filter(file_extension="mp4").get_highest_resolution()
        filename = stream.default_filename
        assets_path = Path(__file__).parent.parent.absolute().joinpath("assets")
        maps_path = assets_path.joinpath("maps")
        thumbnails_path = assets_path.joinpath("thumbnails")
        map_path = maps_path.joinpath(filename)
        stream.download(output_path=maps_path, filename=filename)
        cap = cv2.VideoCapture(map_path)
        success, frame = cap.read()
        while not success and cap.isOpened():
            success, frame = cap.read()

        cap.release()

        if not success:
            # remove corrupted file
            map_path.unlink()
            raise Exception("Map is corrupted")

        # save thumbnail
        thumbnail_path = thumbnails_path.joinpath(f"{filename}.jpg")
        cv2.imwrite(str(thumbnail_path), frame)

        tags = MapsDownloader.__generate_default_tags(filename)
        map_obj = Map(filename, map_path, tags, thumbnail_path, url)
        return map_obj
