"""
Collects all the test functions from projects following
"Conventions for Python test discovery" in
https://docs.pytest.org/en/7.4.x/explanation/goodpractices.html#test-discovery
"""

import os
import re
import sys
import ast
import fire
import tarfile
from tqdm import tqdm
from multiprocessing import Pool

from frontend.python.utils import wrap_repo


def decompress(task):
    ipath, opath = task
    if not os.path.exists(ipath):
        return 1
    # if os.path.exists(opath): return 2
    try:
        tarfile.open(ipath).extractall(opath)
    except:
        return 2
    return 0


def main(
    repo_id_list: str = "ageitgey/face_recognition",
    timeout: int = -1,
    iroot: str = "data/repos_tarball/",
    oroot: str = "data/repos/",
):
    # if repo_id_list is a file then load lines
    # otherwise it is the id of a specific repo
    try:
        repo_id_list = [l.strip() for l in open(repo_id_list, "r").readlines()]
    except:
        repo_id_list = [repo_id_list]
    print(f"Loaded {len(repo_id_list)} repos to be processed")

    tasks = [
        (
            os.path.join(iroot, wrap_repo(repo_id)) + ".tar.gz",
            os.path.join(oroot, wrap_repo(repo_id)),
        )
        for repo_id in repo_id_list
    ]
    results = []
    with Pool(16) as p:
        with tqdm(total=len(tasks)) as pbar:
            for status in p.imap_unordered(decompress, tasks):
                results.append(status)
                pbar.update()
    failed = {"input": 0, "output": 0}
    failed["input"] = sum([i == 1 for i in results])
    failed["output"] = sum([i == 2 for i in results])
    if sum(failed.values()):
        print("Failed:", {key: val for key, val in failed.items() if val})
    print("Done!")


if __name__ == "__main__":
    fire.Fire(main)
