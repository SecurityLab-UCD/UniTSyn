import threading


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
