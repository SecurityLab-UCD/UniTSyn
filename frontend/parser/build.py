"""script to build languages.so lib with UniTSyncer supported languages"""
from tree_sitter import Language, Parser
import subprocess
import os
import logging
import tqdm
import fire

SUPPORTED = ["java", "javascript", "rust", "go", "cpp"]


def main(force=False, language="all"):
    lang_list = SUPPORTED if language == "all" else [language]
    tree_sitter_dirs = [f"tree-sitter-{lang}" for lang in lang_list]
    if force:
        logging.info("Removing languages.so")
        os.remove("languages.so")

    if not os.path.exists("languages.so"):
        logging.info("Downloading tree-sitter to build languages.so")

        for tree_sitter in tree_sitter_dirs:
            if not os.path.exists(tree_sitter):
                subprocess.run(
                    ["git", "clone", f"https://github.com/tree-sitter/{tree_sitter}"]
                )

        logging.info("Building languages.so")
        Language.build_library(
            "languages.so",
            # Include one or more languages
            tree_sitter_dirs,
        )

        logging.info("Removing tree-sitter directories")
        for tree_sitter in tree_sitter_dirs:
            subprocess.run(["rm", "-rf", tree_sitter])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fire.Fire(main)
