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
import logging
import fire


def id2path(id):
    return id.split("::")[0]


def focal2result(syncer, repos_root, obj):
    file_path = os.path.join(repos_root, id2path(obj["test_id"]))
    src_lineno, src_col_offset = obj["focal_loc"]
    test_lineno, test_col_offset = obj["test_loc"]

    code, docstring = syncer.get_source_of_call(
        file_path, src_lineno - 1, src_col_offset
    ).value_or((None, None))

    # since the test's delc node is already capture by frontend, it can store the test code
    if "test" in obj.keys():
        test = obj["test"]
    else:
        fake_loc = Location(
            path2uri(file_path),
            Range(
                Position(test_lineno - 1, test_col_offset),
                Position(test_lineno - 1, test_col_offset + 1),
            ),
        )
        test, _ = python_get_function_code(fake_loc).value_or((None, None))

    return {
        "test_id": obj["test_id"],
        "test": test,
        "code_id": obj["focal_id"],
        "code": code,
        "docstring": docstring,
    }


def main(focal_file="./data/focal/ageitgey-face_recognition.jsonl"):
    repos_root = os.path.abspath("./data/repos")

    with open(focal_file) as f:
        objs = [json.loads(line) for line in f.readlines()]

    proj_id = "/".join(id2path(objs[0]["test_id"]).split("/")[:2])
    print(proj_id)

    syncer = Synchronizer(
        os.path.join(repos_root, proj_id),
        LANGUAGE_IDENTIFIER.PYTHON,
    )
    syncer.start_lsp_server()
    syncer.initialize()

    results = [focal2result(syncer, repos_root, obj) for obj in objs]

    syncer.stop()

    os.makedirs("./data/source", exist_ok=True)
    with jsonlines.open(focal_file.replace("focal", "source"), "w") as f:
        f.write_all(results)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
