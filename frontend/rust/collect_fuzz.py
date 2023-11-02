import logging
from typing import Optional
import fire
import os
from frontend.util import wrap_repo, parallel_subprocess
import subprocess


def transform_repos(repos: list[str], jobs: int):
    def transform_one_repo(repo_path: str):
        return subprocess.Popen(
            ["rust-fuzzer-gen", repo_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    logging.info(f"Running rust-fuzz-gen on {len(repos)} repos")
    parallel_subprocess(repos, jobs, transform_one_repo, on_exit=None)


def main(
    repo_id: str = "marshallpierce/rust-base64",
    repo_root: str = "data/rust_repos/",
    timeout: int = 120,
    nprocs: int = 0,
    limits: Optional[int] = None,
    pipeline: str = "transform",
):
    try:
        repo_id_list = [
            ll for l in open(repo_id, "r").readlines() if len(ll := l.strip()) > 0
        ]
    except:
        repo_id_list = [repo_id]
    if limits is not None:
        repo_id_list = repo_id_list[:limits]
    logging.info(f"Loaded {len(repo_id_list)} repos to be processed")

    logging.info(f"Collecting all rust repos")
    repos = []
    for repo_id in repo_id_list:
        repo_path = os.path.join(repo_root, wrap_repo(repo_id))
        if os.path.exists(repo_path) and os.path.isdir(repo_path):
            subdirectories = [
                os.path.join(repo_path, d)
                for d in os.listdir(repo_path)
                if os.path.isdir(os.path.join(repo_path, d))
            ]
            repos.append(subdirectories[0])

    match pipeline:
        case "transform":
            transform_repos(repos, nprocs)
        case _:
            logging.error(f"Unknown pipeline {pipeline}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
