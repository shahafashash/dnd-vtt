from typing import Iterable, Any, Callable, Generator


def cycle(
    iterable: Iterable[Any] | Callable[[], Generator[Any, None, None]]
) -> Generator[Any, None, None]:
    """Cycle through an iterable or a generator infinitely.

    Args:
        iterable (Iterable[Any] | Callable[[], Generator[Any, None, None]]): The iterable or generator to cycle through.

    Yields:
        Generator[Any, None, None]: The next item in the iterable.
    """
    if callable(iterable):
        iterator = iterable()
    else:
        iterator = iter(iterable)
    while True:
        try:
            yield next(iterator)
        except StopIteration:
            if callable(iterable):
                iterator = iterable()
            else:
                iterator = iter(iterable)
            yield next(iterator)
