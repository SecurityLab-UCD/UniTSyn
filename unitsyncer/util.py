import threading
from returns.maybe import Maybe, Nothing, Some
from pathos.multiprocessing import ProcessPool


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
