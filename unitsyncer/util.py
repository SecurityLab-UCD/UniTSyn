"""util functions for UniTSyncer backend"""
import threading
from returns.maybe import Maybe, Nothing, Some
from pathos.multiprocessing import ProcessPool
import sys
import io


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


def convert_to_seconds(s: str) -> int:
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    return int(s[:-1]) * seconds_per_unit[s[-1]]
