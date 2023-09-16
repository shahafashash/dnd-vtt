from typing import Iterable, Any, Generator


def cycle(iterable: Iterable[Any]) -> Generator[Any, None, None]:
    """Cycle through an iterable infinitely.

    Args:
        iterable (Iterable[Any]): An iterable object.

    Yields:
        Generator[Any, None, None]: The next item in the iterable.
    """
    iterator = iter(iterable)
    while True:
        try:
            yield next(iterator)
        except StopIteration:
            iterator = iter(iterable)
            yield next(iterator)
