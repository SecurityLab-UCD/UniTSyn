import tempfile
from typing import Optional
import os
import subprocess
from os.path import join as pjoin
import json
import ast


def get_ext(lang: str) -> str:
    ext: str

    match lang.lower():
        case "python":
            ext = ".py"
        case "java":
            ext = ".java"
        case "cpp":
            ext = ".cpp"
        case "javascript":
            ext = ".js"
        case "go":
            ext = ".go"
        case _:
            ext = ""

    return ext


def extract_function_name(func: str, lang: str) -> Optional[str]:
    match lang.lower():
        case "python":

            class FunctionNameExtractor(
                ast.NodeVisitor
            ):  # pylint: disable=missing-class-docstring
                def __init__(self):
                    self.name = None

                def visit_FunctionDef(self, node):  # pylint: disable=invalid-name
                    self.name = node.name

            tree = ast.parse(func)
            extractor = FunctionNameExtractor()
            extractor.visit(tree)

            return extractor.name

        case _:
            return None


def get_coverage(code: str, test: str, lang: str = "python") -> Optional[float]:
    """compute branch coverage of `test` on `code`

    Args:
        code (str): source code of focal function to be tested
        test (str): test function code
        lang (str, optional): language used. Defaults to "python".

    Returns:
        Optional[float]: branch coverage rate
    """
    cov: float | None = None
    test_name = extract_function_name(test, lang)
    if not test_name:
        return None

    tmp_dir = tempfile.TemporaryDirectory()
    ext = get_ext(lang)

    focal_file_name = "focal" + ext
    test_file_name = "test" + ext
    test_file = os.path.join(tmp_dir.name, test_file_name)

    with open(os.path.join(tmp_dir.name, focal_file_name), "w") as f:
        f.write(code)

    match lang.lower():
        case "python":
            with open(test_file, "w") as fp:
                fp.write("from focal import *\n")
                fp.write(test)
                fp.write(f"\n{test_name}()\n")
            subprocess.run(
                ["coverage", "run", "--branch", "test.py"],
                cwd=tmp_dir.name,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["coverage", "json"],
                cwd=tmp_dir.name,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with open(os.path.join(tmp_dir.name, "coverage.json")) as cov_fp:
                j = json.load(cov_fp)
            try:
                cov = j["files"][focal_file_name]["summary"]["percent_covered"]
            except KeyError:
                return None
        case _:
            return None

    tmp_dir.cleanup()
    return cov


def main():
    focal = """
def add(x: int, y: int) -> int:
    match x:
        case 1:
            return 1 + y
        case 2:
            return 2 + y
        case 3:
            return 3 + y
        case _:
            return x + y
"""
    test = """
def test_add():
    assert add(1, 2) == 3
"""
    # 31.25
    print(get_coverage(focal, test, "python"))


if __name__ == "__main__":
    main()
