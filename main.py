from unitsyncer.sync import Synchronizer
from pylspclient.lsp_structs import LANGUAGE_IDENTIFIER
from returns.maybe import Maybe, Nothing, Some
from unitsyncer.util import parallel_starmap as starmap
import json


def get_source_in(workspace, lang):
    def get_source(file_path, line, col):
        syncer = Synchronizer(workspace, lang)
        syncer.start_lsp_server()
        syncer.initialize()
        rnt = syncer.get_source_of_call(file_path, line, col)
        syncer.stop()
        return rnt

    return get_source


def obj2triple(obj):
    file_path = obj["test"].split("::")[0]
    if obj["focal"] is not None:
        lineno, col = map(int, obj["focal"].split(":"))
        return file_path, lineno, col
    else:
        return None


def main():
    focal_file = "./data/focal/ageitgey?face_recognition.jsonl"
    with open(focal_file, "r") as f:
        lines = map(json.loads, f.readlines())
        focal_funcs = [f for f in map(obj2triple, lines) if f is not None]

    proj_id = "ageitgey?face_recognition"
    dir_w_commit = "ageitgey-face_recognition-59cff93"

    # fix: dir with '?' is not supported by LSP
    syncer = Synchronizer(
        f"./data/repos/{dir_w_commit}",
        LANGUAGE_IDENTIFIER.PYTHON,
    )
    syncer.start_lsp_server()
    syncer.initialize()

    for file_path, line, col in focal_funcs:
        print("====================================")
        file_path = file_path.split(dir_w_commit)[1][1:]
        print(file_path, line, col)
        match syncer.get_source_of_call(file_path, line - 1, col):
            case Some(source):
                print(source)
            case Nothing:
                print("not found")

    syncer.stop()


if __name__ == "__main__":
    main()
