import logging
from typing import Optional
import fire
import os
from frontend.util import wrap_repo, parallel_subprocess
import subprocess
from os.path import join as pjoin, basename, splitext as psplitext, abspath
from tqdm import tqdm
from frontend.rust.rust_util import format_rust
from multiprocessing import Pool
from unitsyncer.common import CORES


def transform_repos(repos: list[str], jobs: int):
    def transform_one_repo(repo_path: str):
        return subprocess.Popen(
            ["rust-fuzzer-gen", repo_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    logging.info(f"Running rust-fuzz-gen on {len(repos)} repos")
    parallel_subprocess(repos, jobs, transform_one_repo, on_exit=None)


def get_target_list(p: subprocess.Popen):
    match p.stdout:
        case None:
            return []
        case _:
            return p.stdout.read().decode("utf-8").split("\n")


def fuzz_one_target(target: tuple[str, str], timeout):
    repo_path, target_name = target
    with open(pjoin(repo_path, "fuzz_inputs", target_name), "w") as f:
        return subprocess.Popen(
            # todo: find out why -max_total_time doesn't work
            # ["cargo", "fuzz", "run", target_name, "--", f"-max_total_time={timeout}"],
            [
                "bash",
                "-c",
                f"timeout {timeout} cargo fuzz run {target_name}",
            ],
            cwd=repo_path,
            stdout=f,
            stderr=subprocess.DEVNULL,
        )


def fuzz_repos(repos: list[str], jobs: int, timeout: int = 60):
    logging.info(f"Initializing fuzzing targets in {len(repos)} repos")
    parallel_subprocess(
        repos,
        jobs,
        lambda path: subprocess.Popen(
            ["cargo", "fuzz", "init"],
            cwd=path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        on_exit=None,
    )
    logging.info(f"Building fuzzing targets in {len(repos)} repos")
    parallel_subprocess(
        repos,
        jobs,
        lambda path: subprocess.Popen(
            ["cargo", "fuzz", "build"],
            cwd=path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        on_exit=None,
    )

    logging.info("Collecting all fuzz targets")

    target_map = parallel_subprocess(
        repos,
        jobs,
        lambda path: subprocess.Popen(
            ["cargo", "fuzz", "list"], cwd=path, stdout=subprocess.PIPE
        ),
        on_exit=get_target_list,
    )
    targets: list[tuple[str, str]] = [
        (k, v) for k, vs in target_map.items() for v in vs if len(v) > 0
    ]
    for repo in repos:
        os.makedirs(pjoin(repo, "fuzz_inputs"), exist_ok=True)

    logging.info(f"Running cargo fuzz on {len(targets)} targets for {timeout} seconds")
    parallel_subprocess(
        targets, jobs, lambda p: fuzz_one_target(p, timeout), on_exit=None
    )


def substitute_input(template: str, input_data: str) -> str:
    lines = template.splitlines()
    for i in range(len(lines)):
        line = lines[i].strip()
        if "let data = []" in line:
            lines[i] = lines[i].replace("let data = []", f"let data = {input_data}")
    return "\n".join(lines)


def substitute_one_repo(repo: str, targets: list[str]):
    template_dir = pjoin(repo, "tests-gen")
    input_dir = pjoin(repo, "fuzz_inputs")
    for t in targets:
        if t == "":
            continue

        # format template befor loading
        template_path = pjoin(template_dir, t + ".rs")
        subprocess.run(["rustfmt", str(template_path)], check=True)
        with open(template_path) as f_template:
            template = format_rust(f_template.read())
        with open(pjoin(input_dir, t), "r") as f_input:
            inputs = [i for i in f_input.read().splitlines() if i != "[]"]

        tests = [substitute_input(template, input_data) for input_data in inputs]
        with open(pjoin(template_dir, f"{t}.inputs.rs"), "w") as f_template:
            f_template.write("\n".join(tests))


def testgen_repos(repos: list[str], jobs: int, num_gen: Optional[int] = None):
    """Generate tests from fuzz inputs

    Args:
        repos (list[str]): list of repo paths
        jobs (int): number of parallel jobs to use
        num_gen (Optional[int], optional): number of fuzz data to use. Defaults to None.
    """
    target_map = parallel_subprocess(
        repos,
        jobs,
        lambda path: subprocess.Popen(
            ["cargo", "fuzz", "list"], cwd=path, stdout=subprocess.PIPE
        ),
        on_exit=get_target_list,
        use_tqdm=False,
    )
    logging.info(f"Substitute fuzz data to test templates")
    # for repo, targets in tqdm(target_map.items()):
    with Pool(jobs) as p:
        list(tqdm(p.starmap(substitute_one_repo, target_map.items())))


def main(
    repo_id: str = "marshallpierce/rust-base64",
    repo_root: str = "data/rust_repos/",
    timeout: int = 60,
    jobs: int = CORES,
    limits: Optional[int] = None,
    pipeline: str = "transform",
):
    """collect fuzzing data from rust repos

    Args:
        repo_id (str, optional): repo id. Defaults to "marshallpierce/rust-base64".
        repo_root (str, optional): directory contains all the repos. Defaults to "data/rust_repos/".
        timeout (int, optional): max_total_time to fuzz. Defaults to 60.
        jobs (int, optional): number of parallel jobs to use. Defaults to CORES.
        limits (Optional[int], optional): number of fuzzing data, None if use all of them. Defaults to None.
        pipeline (str, optional): what to do. Defaults to "transform".
    """
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
            repos.append(abspath(subdirectories[0]))

    match pipeline:
        case "transform":
            transform_repos(repos, jobs)
        case "fuzz":
            fuzz_repos(repos, jobs, timeout=timeout)
        case "testgen":
            testgen_repos(repos, jobs, limits)
        case _:
            logging.error(f"Unknown pipeline {pipeline}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
