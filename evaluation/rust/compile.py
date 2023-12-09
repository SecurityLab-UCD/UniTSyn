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
from frontend.rust.rust_util import get_test_functions
from frontend.rust.collect_all import collect_test_files
from functools import reduce
from operator import add


def flatten_use_delc(use_delc_code: str) -> list[str]:
    """flatten a nested use declaration line to multiple use declarations

    e.g.

    from:
        use rand::{Rng, SeedableRng};
    to:
        use rand::Rng;\n
        use rand::SeedableRng;


    Args:
        use_delc_code (str): code of a use delc

    Returns:
        list[str]: flattened use declarations
    """
    ast_util = ASTUtil(use_delc_code)
    tree = ast_util.tree(RUST_LANGUAGE)
    root = tree.root_node
    use_delc_nodes = ast_util.get_all_nodes_of_type(root, "use_declaration")
    if len(use_delc_nodes) != 1:
        return []

    delc_node = use_delc_nodes[0]
    scoped_use_list_nodes = ast_util.get_all_nodes_of_type(delc_node, "scoped_use_list")
    if len(scoped_use_list_nodes) == 0:
        # example: use base64::*;
        wildcard_nodes = ast_util.get_all_nodes_of_type(delc_node, "use_wildcard")
        if len(wildcard_nodes) >= 1:
            return [use_delc_code]
        return []

    node = scoped_use_list_nodes[0]

    def fold_nodes(nodes: list[Node]) -> str:
        return reduce(add, map(ast_util.get_source_from_node, nodes))

    def get_use_src(node: Node) -> str | None:
        match node.type:
            case "identifier" | "use_wildcard" | "use_as_clause":
                return ast_util.get_source_from_node(node)
            case "scoped_identifier":
                return fold_nodes(node.children)
            case _:
                return None

    match node.children:
        case []:
            return []
        case [*base_nodes, use_list_node]:
            if use_list_node.type != "use_list":
                return []

            base = fold_nodes(base_nodes)
            use_list = map(get_use_src, use_list_node.children)
            return [f"use {base + u};" for u in use_list if u]
        case _:
            return []


def main():
    code = "use base64::{engine::general_purpose::STANDARD, Engine as _};"
    print(flatten_use_delc(code))


if __name__ == "__main__":
    fire.Fire(main)
