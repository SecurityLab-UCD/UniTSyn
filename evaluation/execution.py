"""
coverage evaluation script for LLM generated code-test pairs
"""

import tempfile
from typing import Optional
import os
import subprocess
from os.path import join as pjoin
import json
import ast
import re


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
        case "cpp":
            pattern = r"\b[A-Za-z_][A-Za-z0-9_]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)"
            matches = re.findall(pattern, func)
            return str(matches[0]) if matches else None
        case _:
            return None


def run_command_in(cwd: str):
    """Create a helper function to run shell command in `cwd` directory

    Args:
        cwd (str): path to a directory
    """

    def subprocess_caller(
        command: str, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ) -> subprocess.CompletedProcess:
        cmd_list = command.split(" ")
        return subprocess.run(
            cmd_list, cwd=cwd, stdout=stdout, stderr=stderr, check=True, text=True
        )

    return subprocess_caller


def get_coverage(
    code: str,
    test: str,
    lang: str = "python",
) -> Optional[float]:
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
    run_cmd = run_command_in(tmp_dir.name)
    ext = get_ext(lang)

    focal_file_name = "focal" + ext
    test_file_name = "test" + ext
    test_file = os.path.join(tmp_dir.name, test_file_name)

    focal_file = os.path.join(tmp_dir.name, focal_file_name)
    with open(focal_file, "w") as f:
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

        case "cpp":
            with open(test_file, "w") as fp:
                fp.write('#include "focal.cpp"')
                fp.write(test)
                fp.write(
                    f"int main() \u007b {test_name}(); return 0; \u007d"
                )  # \u007b \u0007d is {}
            compile_result = run_cmd(
                "clang++ -fprofile-instr-generate -fcoverage-mapping test.cpp -o test"
            )
            if compile_result.returncode != 0:
                return None

            run_cmd("./test")
            run_cmd("llvm-profdata merge -sparse default.profraw -o test.profdata")
            llvm_cov_proc = run_cmd(
                "llvm-cov export ./test -instr-profile=test.profdata --format=text",
                stdout=subprocess.PIPE,
            )
            # print(llvm_cov_proc.stdout)
            j = json.loads(llvm_cov_proc.stdout)
            try:
                for d in j["data"]:
                    for f in d["files"]:
                        if f["filename"] == focal_file:  # type: ignore
                            branch_cnt = f["summary"]["branches"]["count"]  # type: ignore
                            percentage = f["summary"]["branches"]["percent"]  # type: ignore
                            cov = 100 if branch_cnt == 0 else percentage
            except KeyError:
                return None
        case _:
            return None

    tmp_dir.cleanup()
    return cov


def main():
    focal = """
int add(int x, int y) {
    switch(x){
        case 1:
            return 1 + y;
        case 2:
            return 2 + y;
        case 3:
            return 3 + y;
        default:
            return x + y;
    }
}
"""
    test = """
int test_add() {
  int z = add(1, 2);
  if (z == 3)
    return 0;

  return 1;
}
"""
    print(get_coverage(focal, test, "cpp"))


if __name__ == "__main__":
    main()
