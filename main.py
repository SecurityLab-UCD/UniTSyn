from unitsyncer.sync import Synchronizer
from pylspclient.lsp_structs import LANGUAGE_IDENTIFIER
from returns.maybe import Maybe, Nothing, Some
from unitsyncer.util import parallel_starmap as starmap


def get_source_in(workspace, lang):
    def get_source(file_path, line, col):
        syncer = Synchronizer(workspace, lang)
        syncer.initialize()
        rnt = syncer.get_source_of_call(file_path, line, col)
        syncer.stop()
        return rnt

    return get_source


def main():
    focal_funcs = [
        ("tests/test_python_example.py", 5, 13),
        ("tests/test_python_example.py", 10, 17),
    ]

    f = get_source_in("./data/repos/py_example", LANGUAGE_IDENTIFIER.PYTHON)
    rnt = starmap(f, focal_funcs, jobs=4)
    print(rnt)


if __name__ == "__main__":
    main()
