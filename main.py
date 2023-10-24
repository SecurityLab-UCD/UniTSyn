from tqdm import tqdm
from unitsyncer.sync import Synchronizer
from pylspclient.lsp_structs import LANGUAGE_IDENTIFIER, Location, Position, Range
from returns.maybe import Maybe, Nothing, Some
from returns.result import Result, Success, Failure
from unitsyncer.util import parallel_starmap as starmap, path2uri
from unitsyncer.common import CORES
import math
from unitsyncer.source_code import get_function_code
import json
import jsonlines
import os
from pathos.multiprocessing import ProcessPool
import logging
import fire


def id2path(id):
    return id.split("::")[0]


def java_workdir_dict(objs: list[dict]) -> dict[str, list[dict]]:
    """split a list of test ids into a dict of workdir to file path
    this solves the LSP TimeoutError for JAVA with too much subdirectories

    Args:
        objs (list[dict]): [focal_ids parsed into dict]

    Returns:
        dict[str, list[dict]]: {workdir: [corresponding focal objects, ...], ...}
    """
    workdir_dict = {}
    for obj in objs:
        test_id = obj["test_id"]
        file_path = id2path(test_id)
        workdir = file_path.split("/test")[0]
        if workdir not in workdir_dict.keys():
            workdir_dict[workdir] = []
        workdir_dict[workdir].append(obj)
    return workdir_dict


def focal2result(syncer: Synchronizer, repos_root, obj):
    p = id2path(obj["test_id"])
    file_path = os.path.join(repos_root, p)
    src_lineno, src_col_offset = obj["focal_loc"]
    test_lineno, test_col_offset = obj["test_loc"]

    langID = syncer.langID

    # only python ast is 1-indexed, tree-sitter and LSP are 0-indexed
    match langID:
        case LANGUAGE_IDENTIFIER.PYTHON:
            src_lineno -= 1
            test_lineno -= 1

    # since the test's delc node is already capture by frontend, it can store the test code
    if "test" in obj.keys():
        test = obj["test"]
    else:
        fake_loc = Location(
            path2uri(file_path),
            Range(
                Position(test_lineno, test_col_offset),
                Position(test_lineno, test_col_offset + 1),
            ),
        )
        test, _ = get_function_code(fake_loc, syncer.langID).value_or((None, None))

    if "focal_id" in obj.keys():
        code_id = obj["focal_id"]
    else:
        code_id = None

    result = {
        "test_id": obj["test_id"],
        "test": test,
        "code_id": code_id,
    }

    # todo: conform return format when Failure
    match syncer.get_source_of_call(file_path, src_lineno, src_col_offset):
        case Success((code, docstring)):
            result["code"] = code
            result["docstring"] = docstring
        case Failure(e):
            logging.debug(e)
            result["error"] = str(e)

    return result


def process_one_focal_file(
    focal_file="./data/focal/ageitgey-face_recognition.jsonl",
    repos_root="data/repos",
    language="python",
):
    with open(focal_file) as f:
        objs = [json.loads(line) for line in f.readlines()]

    n_focal = len(objs)
    match language:
        case LANGUAGE_IDENTIFIER.PYTHON:
            first_test_id = objs[0]["test_id"]
            workdir = "/".join(id2path(first_test_id).split("/")[:2])
            wd = {
                workdir: objs,
            }
        case LANGUAGE_IDENTIFIER.JAVA:
            wd = java_workdir_dict(objs)
        case _:
            logging.debug(f"language {language} not supported")
            return n_focal, 0

    results = []
    logging.debug(f"number of workdir_dict: {len(wd.keys())}")
    repos_root = os.path.abspath(repos_root)
    for workdir, workdir_objs in wd.items():
        try:
            full_workdir = os.path.join(repos_root, workdir)
            logging.debug(f"workdir: {full_workdir}")

            syncer = Synchronizer(full_workdir, language)
            syncer.start_lsp_server(timeout=60)
            syncer.initialize()

            results += [focal2result(syncer, repos_root, obj) for obj in workdir_objs]

            syncer.stop()
        except Exception as e:
            logging.debug(e)
            continue

    with jsonlines.open(focal_file.replace("focal", "source"), "w") as f:
        f.write_all(results)

    return n_focal, sum(1 for r in results if "code" in r)


def main(
    repos_root="data/repos_tarball",
    focal_path="data/focal",
    language="python",
    jobs=CORES,
):
    all_focal_files = []
    if os.path.isdir(focal_path):
        focal_dir = focal_path
        for root, dirs, files in os.walk(os.path.abspath(focal_dir)):
            for file in files:
                if file.endswith(".jsonl"):
                    all_focal_files.append(os.path.join(root, file))
    elif os.path.isfile(focal_path):
        all_focal_files.append(focal_path)
    else:
        logging.error(f"{focal_path} is not a valid file or directory")
        exit(1)

    logging.info(f"Processing {len(all_focal_files)} focal files")
    os.makedirs("./data/source", exist_ok=True)

    # starting jobs / 2 since each job will spawn 2 processes (main and LSP)
    with ProcessPool(math.ceil(jobs / 2)) as pool:
        rnt = list(
            tqdm(
                pool.imap(
                    lambda f: process_one_focal_file(
                        f, repos_root=repos_root, language=language
                    ),
                    all_focal_files,
                ),
                total=len(all_focal_files),
            )
        )
    nfocal, ncode = zip(*rnt)
    logging.info(
        f"Processed {sum(ncode)} have source code in {sum(nfocal)} focal functions"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
