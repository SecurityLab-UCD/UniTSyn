import threading
from returns.maybe import Maybe, Nothing, Some
from pathos.multiprocessing import ProcessPool
import sys
import io
from itertools import chain
from typing import Callable, Iterable, TypeVar, Iterator


class ReadPipe(threading.Thread):
    """source:
    https://github.com/yeger00/pylspclient/blob/master/examples/python-language-server.py#L10
    """

    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode("utf-8")
        while line:
            line = self.pipe.readline().decode("utf-8")


def uri2path(uri: str) -> Maybe[str]:
    if uri.startswith("file://"):
        return Some(uri[7:])
    return Nothing


def path2uri(path: str) -> str:
    """
    Args:
        path (str): absolute path to file

    Returns:
        str: uri format of path
    """
    return "file://" + path


def parallel_starmap(f, args, jobs=1):
    with ProcessPool(jobs) as p:
        rnt = p.map(lambda x: f(*x), args)
    return rnt


def replace_tabs(text: str, n_space=4) -> str:
    """replace each tab with 4 spaces"""
    return text.replace("\t", " " * n_space)


def silence(func):
    """Execute a function with suppressed stdout."""

    def wrapper(*args, **kwargs):
        original_stdout = sys.stdout
        try:
            # Redirect stdout to a dummy file-like object
            sys.stdout = io.StringIO()
            return func(*args, **kwargs)
        finally:
            # Restore original stdout
            sys.stdout = original_stdout

    return wrapper


T = TypeVar("T")
U = TypeVar("U")


def concatMap(func: Callable[[T], Iterable[U]], iterable: Iterable[T]) -> Iterator[U]:
    """creates a list from a list generating function by application of this function
    on all elements in a list passed as the second argument


    Args:
        func: T -> [U]
        iterable: [T]

    Returns: [U]
    """
    return chain.from_iterable(map(func, iterable))
