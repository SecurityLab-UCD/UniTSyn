"""
coverage evaluation script for LLM generated code-test pairs
"""

import tempfile
from typing import Optional
import os
import subprocess
import json
import csv
import fire
from tqdm import tqdm


def get_ext(lang: str) -> str:
    ext: str
    if lang == "python":
        ext = ".py"
    elif lang == "java":
        ext = ".java"
    elif lang == "cpp":
        ext = ".cpp"
    elif lang == "js":
        ext = ".js"
    elif lang == "go":
        ext = ".go"
    else:
        ext = ""

    return ext


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
    java_lib_path: str = os.path.join(os.getcwd(), "lib"),
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
    lang = lang.lower()
    java_lib_path = os.path.abspath(java_lib_path)

    tmp_dir = tempfile.TemporaryDirectory()
    tmp_dir_path = tmp_dir.name
    run_cmd = run_command_in(tmp_dir_path)
    ext = get_ext(lang)

    focal_file_name = "focal" + ext
    test_file_name = "test" + ext
    test_file = os.path.join(tmp_dir_path, test_file_name)

    focal_file = os.path.join(tmp_dir_path, focal_file_name)
    with open(focal_file, "w") as f:
        f.write(code)

    if lang == "python":
        with open(test_file, "w") as fp:
            fp.write("from focal import *\n")
            fp.write(test)
        run_cmd("coverage run --branch test.py")
        run_cmd("coverage json")
        with open(os.path.join(tmp_dir_path, "coverage.json")) as cov_fp:
            j = json.load(cov_fp)
        try:
            cov = j["files"][focal_file_name]["summary"]["percent_covered"]
        except KeyError:
            return None

    elif lang == "cpp":
        with open(test_file, "w") as fp:
            fp.write('#include "focal.cpp"\n')
            fp.write(test)
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
        j = json.loads(llvm_cov_proc.stdout)
        try:
            for d in j["data"]:
                for f in d["files"]:
                    if f["filename"] == os.path.abspath(focal_file):  # type: ignore
                        branch_cnt = f["summary"]["branches"]["count"]  # type: ignore
                        percentage = f["summary"]["branches"]["percent"]  # type: ignore
                        cov = 100.0 if branch_cnt == 0 else percentage
        except KeyError:
            return None
    elif lang == "java":
        main_file = "Main.java"
        main_file_path = os.path.join(tmp_dir_path, main_file)
        with open(main_file_path, "w") as f:
            f.write(code)
            f.write(test)
        run_cmd("javac Main.java -d bin/")
        run_cmd(
            f"java -javaagent:{java_lib_path}/jacocoagent.jar=destfile=jacoco.exec -cp bin Main"
        )
        run_cmd(
            f"java -jar {java_lib_path}/jacococli.jar report jacoco.exec"
            " --classfiles bin --sourcefiles Main.java --csv coverage.csv"
        )
        coverage_file = os.path.join(tmp_dir_path, "coverage.csv")
        with open(coverage_file, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["CLASS"] == "Solution":
                    covered = int(row["BRANCH_COVERED"])
                    missed = int(row["BRANCH_MISSED"])
                    total = covered + missed
                    cov = 100.0 * (covered / total if total != 0 else 1)
                    break
    elif lang == "js":
        with open(focal_file, "a") as f:
            f.write(test)
        run_cmd("nyc --reporter=json-summary node focal.js")
        coverage_file = os.path.join(tmp_dir_path, "coverage", "coverage-summary.json")
        with open(coverage_file) as cov_fp:
            j = json.load(cov_fp)
        try:
            cov = j[focal_file]["branches"]["pct"]
        except KeyError:
            return None

    elif lang == "go":
        mod_file = os.path.join(tmp_dir_path, "go.mod")
        with open(mod_file, "w") as mod_fp:
            mod_fp.write("module go_cov\ngo 1.16\n")

        test_file_name = "focal_test.go"
        test_file = os.path.join(tmp_dir_path, test_file_name)
        with open(test_file, "w") as test_fp:
            test_fp.write("package main\n")
            test_fp.write('import "testing"\n')
            test_fp.write('import "github.com/stretchr/testify/assert"\n')
            test_fp.write(test)
        with open(focal_file, "w") as focal_fp:
            focal_fp.write("package main\n")
            focal_fp.write(code)

        run_cmd("go get github.com/stretchr/testify/assert")
        run_cmd("go test -coverprofile=coverage.out")
        cov_result: str = run_cmd(
            "go tool cover -func=coverage.out", stdout=subprocess.PIPE
        ).stdout
        try:
            line = cov_result.splitlines()[0]
            elems = line.split("\t")
            cov = float(elems[-1][:-1])  # str 100.0% -> float 100.0
        except IndexError:
            return None

    else:
        return None

    tmp_dir.cleanup()
    return cov


def main(
    jsonl_path: str,
    change_go_proxy: bool = False,
    java_lib_path: str = os.path.join(os.getcwd(), "lib"),
):
    if change_go_proxy:
        subprocess.run(["go", "env", "-w", "GOPROXY=https://goproxy.cn"])

    with open(jsonl_path, "r") as fp:
        j_lines = fp.readlines()

    with open(f"results_{jsonl_path}", "w") as fp:
        for j_line in tqdm(j_lines):
            j = json.loads(j_line)
            focal = j["focal"]
            test = j["test"]
            lang = j["lang"]
            cov = get_coverage(focal, test, lang=lang, java_lib_path=java_lib_path)
            j["coverage"] = cov
            fp.write(json.dumps(j))


if __name__ == "__main__":
    fire.Fire(main)
