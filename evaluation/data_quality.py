"""script to reproduce plot in data quality analysis"""

import json
import matplotlib.pyplot as plt
import numpy as np
from multiprocessing import Pool
import random
import pandas as pd
from tqdm import tqdm
import dataclasses
from funcy import lmap, lfilter


plt.style.use("_mpl-gallery")


def repo_id(test_id: str) -> str:
    return test_id.split("/")[0]


@dataclasses.dataclass
class ProjStat:
    repo_id: str
    n_test_lines: int
    n_code_lines: int
    n_assert: int


def analyze(objs: list[dict]) -> pd.DataFrame:
    proj_map: dict[str, ProjStat] = {}
    for obj in tqdm(objs):
        repo = repo_id(obj["test_id"])
        test: str = obj["test"]
        code: str = obj["code"]
        n_test_lines = len(test.splitlines())
        n_code_lines = len(code.splitlines())

        lower_test = test.lower()
        n_assert = lower_test.count("assert")
        if obj["lang"] in ("js", "cpp"):
            n_expect = lower_test.count("expect")
            n_assert += n_expect
            if obj["lang"] == "js":
                n_test = lower_test.count("test")
                n_assert += n_test

        if repo in proj_map:
            proj_map[repo].n_test_lines += n_test_lines
            proj_map[repo].n_code_lines += n_code_lines
            proj_map[repo].n_assert += n_assert
        else:
            proj_map[repo] = ProjStat(repo, n_test_lines, n_code_lines, n_assert)
    return pd.DataFrame([o.__dict__ for o in proj_map.values()])


def test_to_code_ratio(df: pd.DataFrame):
    return df["n_test_lines"] / df["n_code_lines"]


def get_density(df: pd.DataFrame):
    return df["n_assert"] / df["n_test_lines"]


def main():

    with open("data/source/all.jsonl", "r") as fp:
        lines = fp.readlines()

    with Pool() as p:
        objs = p.map(json.loads, lines)

    langs = ["python", "java", "go", "cpp", "js"]

    objss = lmap(lambda l: lfilter(lambda o: o["lang"] == l, objs), langs)

    dfs = lmap(analyze, objss)

    np.random.seed(0)
    bins = np.linspace(0, 10, 100)

    ratios = lmap(test_to_code_ratio, dfs)
    ticks = list(range(10))
    for name, ratio in zip(langs, ratios):
        plt.figure(figsize=(12, 6))
        plt.hist(ratio, bins, alpha=0.5)
        plt.xticks(ticks)
        plt.xlabel("Test-to-code Ratio", fontsize=18)
        plt.ylabel("Per-project Frequency", fontsize=18)
        plt.rc("axes", labelsize=18)
        plt.savefig(f"{name}.pdf", dpi=500, bbox_inches="tight")

    with open("python_coverage.jsonl", "r") as fp:
        covs = list(map(json.loads, fp.readlines()))

    cov_df = pd.DataFrame(covs)
    cov_df.describe()

    plt.figure(figsize=(12, 4))
    plt.boxplot(
        cov_df["coverage"], patch_artist=True, vert=False, widths=0.5, notch=True
    )
    plt.xlabel("Coverage Percentage", fontsize=18)
    plt.rc("axes", labelsize=18)

    plt.savefig(f"coverage_box.pdf", dpi=500, bbox_inches="tight")

    ds = list(map(get_density, dfs))

    bins = np.linspace(0, 1, 100)
    for name, density in zip(langs, ds):
        print(name)
        plt.figure(figsize=(12, 6))
        plt.hist(density, bins, alpha=0.5)
        # plt.legend(loc='upper right', fontsize=18)
        # plt.yscale("log")
        plt.xlabel("Assertion density", fontsize=18)
        plt.ylabel("Per-project Frequency", fontsize=18)
        plt.rc("axes", labelsize=18)
        plt.savefig(f"density/{name}.pdf", dpi=500, bbox_inches="tight")


if __name__ == "__main__":
    main()
