import fire
import os
from pathlib import Path
from frontend.python.utils import wrap_repo
from tree_sitter import Language, Parser
from frontend.parser.langauges import JAVA_LANGUAGE
from frontend.parser.ast_util import get_all_nodes_of_type, tree_walker


def has_test(file_path):
    # follow TeCo to check for JUnit4 and JUnit5
    # todo: support different usage as in google/closure-compiler
    def has_junit4(code):
        return "@Test" in code and "import org.junit.Test" in code

    def has_junit5(code):
        return "@Test" in code and "import org.junit.jupiter.api.Test" in code

    with open(file_path, "r") as f:
        code = f.read()
    return has_junit4(code) or has_junit5(code)


def collect_test_files(root: str):
    """Get all files end with .java in the given root directory

    Args:
        root (str): path to repo root
    """
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".java"):
                if has_test(p := os.path.join(dirpath, filename)):
                    yield p


def collect_test_funcs(file_path: str):
    """collect testing functions from the target file"""
    test_funcs = []

    with open(file_path, "r") as f:
        src = f.read()

    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    walk_tree = tree_walker(src)

    tree = parser.parse(bytes(src, "utf8"))
    root_node = tree.root_node
    walk_tree(root_node)
    func_decls = get_all_nodes_of_type(root_node, "method_declaration")

    return test_funcs


def collect_from_repo(repo_id: str, repo_root: str, test_root: str):
    """collect all test functions in the given project
    return (status, nfile, ntest)
    status can be 0: success, 1: repo not found, 2: test not found, 3: skip when output file existed
    """
    repo_path = os.path.join(repo_root, wrap_repo(repo_id))
    if not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        return 1, 0, 0
    test_path = os.path.join(test_root, wrap_repo(repo_id) + ".txt")
    # skip if exist
    if os.path.exists(test_path):
        return 3, 0, 0
    # collect potential testing modules
    all_files = collect_test_files(repo_path)
    test_files, test_funcs = [], []
    for f in all_files:
        funcs = collect_test_funcs(f)
        if funcs is None or len(funcs) == 0:
            continue
        test_files.append(f)
        test_funcs.extend(funcs)
    if len(test_funcs) == 0:
        return 2, len(test_files), len(test_funcs)
    # save to disk
    with open(test_path, "w") as outfile:
        for func_id in test_funcs:
            parts = func_id.split("::")
            parts[0] = str(
                Path(os.path.abspath(parts[0])).relative_to(os.path.abspath(repo_root))
            )
            func_id = "::".join(parts)
            outfile.write(f"{func_id}\n")
    return 0, len(test_files), len(test_funcs)


def main(
    repo_id_list: str = "spring-cloud/spring-cloud-netflix",
    repo_root: str = "data/repos/",
    test_root: str = "data/tests/",
    timeout: int = 120,
    nprocs: int = 0,
    limits: int = -1,
):
    status, nfile, ntest = collect_from_repo(
        repo_id_list,
        repo_root,
        test_root,
    )
    print(status, nfile, ntest)


if __name__ == "__main__":
    fire.Fire(main)
