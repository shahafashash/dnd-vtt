from functools import wraps
from line_profiler import LineProfiler
from memory_profiler import profile as memory_profiler


def time_profiler(func):
    profiler = LineProfiler()

    @wraps(func)
    def wrapper(*args, **kwargs):
        result = profiler(func)(*args, **kwargs)
        profiler.print_stats()
        return result

    return wrapper


def memory_profiler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = memory_profiler(func)(*args, **kwargs)
        return result

    return wrapper
