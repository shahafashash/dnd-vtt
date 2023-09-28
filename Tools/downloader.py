from typing import overload, List
import sys
from pathlib import Path
from pytube import YouTube
import cv2
from nltk.tokenize import word_tokenize

sys.path.append(str(Path(__file__).parent.parent.absolute()))
from backend.config import Map


class MapsDownloader:
    def __generate_default_tags(map_name: str) -> List[str]:
        # clean map name from unicode characters, special characters and spaces
        map_name = map_name.encode("ascii", "ignore").decode("ascii")
        map_name.strip().lower()
        tags = word_tokenize(map_name)
        return tags

    def __on_progress(stream: YouTube, chunk: bytes, bytes_remaining: int) -> float:
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size
        percentage_of_completion = round(percentage_of_completion, 2)
        print(f"{percentage_of_completion*100}% downloaded", end="\r")
        return percentage_of_completion

    def __on_complete(stream: YouTube, file_path: str) -> None:
        print("Download completed")

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
        yt = YouTube(
            url,
            on_progress_callback=MapsDownloader.__on_progress,
            on_complete_callback=MapsDownloader.__on_complete,
        )
        stream = yt.streams.filter(file_extension="mp4").get_highest_resolution()
        filename = stream.default_filename
        map_name = Path(filename).stem.title()
        assets_path = Path(__file__).parent.parent.absolute().joinpath("assets")
        maps_path = assets_path.joinpath("maps")
        thumbnails_path = assets_path.joinpath("thumbnails")
        map_path = maps_path.joinpath(filename)
        stream.download(output_path=maps_path, filename=filename)
        cap = cv2.VideoCapture(str(map_path))
        success, frame = cap.read()
        while not success and cap.isOpened():
            success, frame = cap.read()

        cap.release()

        if not success:
            # remove corrupted file
            map_path.unlink()
            raise Exception("Map is corrupted")

        # save thumbnail
        thumbnail_path = thumbnails_path.joinpath(f"{map_name}.jpg")
        cv2.imwrite(str(thumbnail_path), frame)

        tags = MapsDownloader.__generate_default_tags(map_name)
        map_obj = Map(map_name, str(map_path), tags, str(thumbnail_path), url)
        return map_obj


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
    map_obj = MapsDownloader.download(url)
    config = Config(str(Path(__file__).parent.parent.absolute().joinpath("maps.json")))
    config.add_map(map_obj)
