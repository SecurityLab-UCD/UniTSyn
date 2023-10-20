import ast
from tokenize import maybe
from typing import Iterable, Optional
import fire
import os
from pathlib import Path
import re
from requests import get
from frontend.python.utils import wrap_repo
from tree_sitter.binding import Node
from frontend.parser.langauges import JAVA_LANGUAGE
from frontend.parser.ast_util import ASTUtil, ASTLoc
from returns.maybe import Maybe, Nothing, Some, maybe
from fuzzywuzzy import process


@maybe
def closest_match(name: str, strings: list[str]) -> Optional[str]:
    match process.extractOne(name, strings):
        case (best_match, score):
            return best_match
        case None:
            return None


def fuzzy_focal_name(test_func_name: str) -> str:
    patterns = [r"test_(\w+)", r"(\w+)_test", r"Test(\w+)", r"(\w+)Test"]

    for pattern in patterns:
        match = re.search(pattern, test_func_name, re.IGNORECASE)
        if match:
            return match.group(1)

    return test_func_name


def get_focal_call(ast_util: ASTUtil, func: Node) -> Maybe[tuple[str, ASTLoc]]:
    """Find the focal call in the given function

    Args:
        ast_util (ASTUtil): ASTUtil for the file
        func (Node): a method_declaration node

    Returns:
        Maybe[tuple[str, ASTLoc]]: focal call and its location
    """

    # todo: find better heuristic to match object on imports
    """get the focal call from the given function"""
    calls = ast_util.get_all_nodes_of_type(func, "method_invocation")
    # reverse for postorder
    func_calls = [ast_util.get_source_from_node(call) for call in calls]
    test_func_name = fuzzy_focal_name(ast_util.get_method_name(func).value_or(""))
    calls_before_assert = []
    for call in reversed(func_calls):
        if "assert" in call:
            break
        calls_before_assert.append(call)

    def get_loc(call: str) -> tuple[str, ASTLoc]:
        idx = func_calls.index(call)
        node = calls[idx]
        lineno, col = node.start_point
        match call.split("."):
            case [obj_name, *_, method_name]:
                offset = len(call) - len(method_name)
                return method_name, (lineno, col + offset)
            case _:
                return call, (lineno, col)

    return closest_match(test_func_name, calls_before_assert).map(get_loc)


def main():
    test_f = "data/repos/spring-cloud-spring-cloud-netflix/spring-cloud-spring-cloud-netflix-630151f/spring-cloud-netflix-eureka-client-tls-tests/src/test/java/org/springframework/cloud/netflix/eureka/BaseCertTest.java"
    with open(test_f) as f:
        code = f.read()
    ast_util = ASTUtil(code)
    tree = ast_util.tree(JAVA_LANGUAGE)
    root_node = tree.root_node

    func_delcs = ast_util.get_all_nodes_of_type(root_node, "method_declaration")
    func = func_delcs[0]

    print(get_focal_call(ast_util, func))


if __name__ == "__main__":
    fire.Fire(main)
