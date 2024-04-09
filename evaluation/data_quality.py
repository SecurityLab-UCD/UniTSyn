import fire
import os
from multiprocessing import cpu_count
from pathos.multiprocessing import ProcessingPool
from frontend.parser.ast_util import ASTUtil
from unitsyncer.util import replace_tabs
from typing import Callable
from tree_sitter.binding import Node
from frontend.util import wrap_repo
from frontend.parser import (
    JAVA_LANGUAGE,
    JAVASCRIPT_LANGUAGE,
    CPP_LANGUAGE,
    GO_LANGUAGE,
)
from funcy import lfilter
from functools import reduce
import logging
from tqdm import tqdm
import csv

EXT = {
    "java": ["java"],
    "cpp": ["cc", "cpp", "c++"],
    "js": ["js"],
    "go": ["go"],
}

FN_NODE_TYPE = {
    "java": "method_declaration",
    "cpp": "function_definition",
    "js": "call_expression",
    "go": "function_declaration",
}

LANG = {
    "java": JAVA_LANGUAGE,
    "cpp": CPP_LANGUAGE,
    "js": JAVASCRIPT_LANGUAGE,
    "go": GO_LANGUAGE,
}


def test_checker(ast_util: ASTUtil, lang: str) -> Callable[[Node], bool]:
    match lang:
        case "java":
            from frontend.java.collect_focal import is_test_fn as is_java_test

            return lambda n: is_java_test(n, ast_util)
        case "cpp":
            from frontend.cpp.collect_focal import is_test_fn as is_cpp_test

            return lambda n: is_cpp_test(n, ast_util)
        case "go":
            from frontend.go.collect_focal import is_test_fn as is_go_test

            return lambda n: is_go_test(n, ast_util)
        case "js":
            from frontend.javascript.js_util import is_test_fn as is_js_test

            return lambda n: is_js_test(n, ast_util)
        case _:
            return lambda _: False


def collect_files(root: str, lang: str) -> list[str]:
    l = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            extension = filename.split(".")[-1]
            if extension in EXT[lang]:
                l.append(os.path.join(dirpath, filename))
    return l


def get_analyzer(lang: str):
    def tuple_add(p1, p2):
        return (p1[0] + p2[0], p1[1] + p2[1])

    def analyze_file(file_path: str) -> tuple[int, int]:

        with open(file_path, "r", errors="replace") as f:
            ast_util = ASTUtil(replace_tabs(f.read()))
        tree = ast_util.tree(LANG[lang])
        root_node = tree.root_node
        is_test = test_checker(ast_util, lang)

        functions = ast_util.get_all_nodes_of_type(root_node, FN_NODE_TYPE[lang])
        n_tests = len(lfilter(is_test, functions))
        n_funcs = len(functions) - n_tests
        return n_funcs, n_tests

    def _analyze(repo_root: str) -> dict | None:
        try:
            n_funcs, n_tests = reduce(
                tuple_add, map(analyze_file, collect_files(repo_root, lang)), (0, 0)
            )
        except Exception as e:
            logging.warning(e)
            return None

        return {
            "repo_id": repo_root,
            "#funcs": n_funcs,
            "#unit": n_tests,
            "ratio": n_tests / n_funcs if n_funcs != 0 else None,
        }

    return _analyze


def main(
    input_repo_list_path: str,
    root: str,
    lang: str,
    nproc: int = cpu_count(),
    output_csv_file: str = "output_ratio.csv",
):

    with open(input_repo_list_path, "r") as fp:
        repo_list = fp.read().splitlines()

    root = os.path.abspath(root)
    repo_roots = [os.path.join(root, wrap_repo(repo_id)) for repo_id in repo_list]
    analyze = get_analyzer(lang)

    logging.info(f"Processing {len(repo_roots)} repos.")
    with ProcessingPool(nproc) as pool:
        rows = list(tqdm(pool.imap(analyze, repo_roots), total=len(repo_roots)))

    valid_rows: list[dict] = lfilter(None, rows)
    with open(output_csv_file, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=valid_rows[0].keys())
        writer.writeheader()
        writer.writerows(valid_rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
