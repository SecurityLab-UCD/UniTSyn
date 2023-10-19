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
    # Using the extractOne method to find the best match
    return strings[0] if strings else None
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
    """get the focal call from the given function"""
    calls = ast_util.get_all_nodes_of_type(func, "method_invocation")
    # reverse for postorder
    func_calls = [ast_util.get_source_from_node(call) for call in calls]
    test_func_name = fuzzy_focal_name(ast_util.get_source_from_node(func))
    calls_before_assert = []
    for call in reversed(func_calls):
        if "assert" in call:
            break
        if test_func_name.lower() in call.lower():
            calls_before_assert.append(call)
    # todo: find better heuristic to match object on imports
    closest_name = closest_match(test_func_name, calls_before_assert)

    def get_loc(call: str) -> tuple[str, ASTLoc]:
        idx = func_calls.index(call)
        node = calls[idx]
        lineno, col = node.start_point
        obj_name = call.split(".")[0]
        print(ast_util.get_source_from_node(node))
        return call, (lineno, col + len(obj_name) + 1)

    return closest_match(test_func_name, calls_before_assert).map(get_loc)


def main():
    code = """
@Test
void testRegister() {
    assertThat(eurekaHttpClient.register(info).getStatusCode()).isEqualTo(HttpStatus.OK.value());
}
"""
    ast_util = ASTUtil(code)
    tree = ast_util.tree(JAVA_LANGUAGE)
    root_node = tree.root_node

    func_delcs = ast_util.get_all_nodes_of_type(root_node, "method_declaration")
    func = func_delcs[0]

    print(get_focal_call(ast_util, func))


if __name__ == "__main__":
    fire.Fire(main)
