from unittest import result
from unitsyncer.sync import Synchronizer
from pylspclient.lsp_structs import LANGUAGE_IDENTIFIER, Location, Position, Range
from returns.maybe import Maybe, Nothing, Some
from unitsyncer.util import parallel_starmap as starmap, path2uri
from unitsyncer.source_code import python_get_function_code
import json
import jsonlines
import os
from pathos.multiprocessing import ProcessPool


def id2path(id):
    return id.split("::")[0]


def focal2result(syncer, repos_root, obj):
    file_path = os.path.join(repos_root, id2path(obj["test_id"]))
    src_lineno, src_col_offset = obj["focal_loc"]
    test_lineno, test_col_offset = obj["test_loc"]

    fake_loc = Location(
        path2uri(file_path),
        Range(
            Position(test_lineno - 1, test_col_offset),
            Position(test_lineno - 1, test_col_offset + 1),
        ),
    )

    code, docstring = syncer.get_source_of_call(
        file_path, src_lineno - 1, src_col_offset
    ).value_or((None, None))
    test, _ = python_get_function_code(fake_loc).value_or((None, None))

    return {
        "test_id": obj["test_id"],
        "test": test,
        "code_id": obj["focal_id"],
        "code": code,
        "docstring": docstring,
    }


def main():
    repos_root = os.path.abspath("./data/repos")
    proj_id = "ageitgey-face_recognition/ageitgey-face_recognition-59cff93"
    focal_file = "./data/focal/ageitgey-face_recognition.jsonl"

    # fix: dir with '?' is not supported by LSP
    syncer = Synchronizer(
        os.path.join(repos_root, proj_id),
        LANGUAGE_IDENTIFIER.PYTHON,
    )
    syncer.start_lsp_server()
    syncer.initialize()

    with jsonlines.open(focal_file) as reader:
        results = [focal2result(syncer, repos_root, obj) for obj in reader]

    syncer.stop()

    os.makedirs("./data/source", exist_ok=True)
    with jsonlines.open(f"./data/source/all.jsonl", "w") as f:
        f.write_all(results)


if __name__ == "__main__":
    main()
