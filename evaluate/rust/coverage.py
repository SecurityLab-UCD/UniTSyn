import json
from typing import Iterable
import fire
import os
from tree_sitter.binding import Node
from frontend.parser import RUST_LANGUAGE
from frontend.parser.ast_util import ASTUtil
from unitsyncer.util import replace_tabs
import json
import subprocess
from unitsyncer.common import UNITSYNCER_HOME
from returns.maybe import Maybe, Some, Nothing


def clean_workspace(workspace_dir: str):
    subprocess.run(["rm", "rust_test_coverage.sh"], cwd=workspace_dir)
    subprocess.run(["rm", "-r", "target"], cwd=workspace_dir)

def init_workspace(workspace_dir: str):
    cov_script_path = f"{UNITSYNCER_HOME}/evaluate/rust/rust_test_coverage.sh"
    subprocess.run(["cp", cov_script_path, workspace_dir])

def get_coverage(workspace_dir: str, test_target: str, clean_run: bool=False) -> Maybe[float]:
    if clean_run:
        clean_workspace(workspace_dir)


    init_workspace(workspace_dir)

    subprocess.run(
            ["./rust_test_coverage.sh", test_target], 
            cwd=workspace_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
    )

    try:
        cov_path = f"{workspace_dir}/target/debug/coverage/{test_target}/coverage.json"
        cov_obj = json.load(open(cov_path))
    except FileNotFoundError:
        return Nothing

    if cov_obj["label"] != "coverage" or "message" not in cov_obj:
        return Nothing
    return Some(float(cov_obj["message"][:-1]))

def main():
    workspace_dir = os.path.abspath("data/rust_repos//marshallpierce-rust-base64/marshallpierce-rust-base64-4ef33cc")

    cov = get_coverage(workspace_dir, "encode_all_ascii").unwrap()
    assert cov == 3.94
    
    cov = get_coverage(workspace_dir, "encode_all_bytes").unwrap()
    assert cov == 4.95


if __name__ == "__main__":
    fire.Fire(main)
