import ast
from typing import Iterable
import fire
import os
from pathlib import Path
from frontend.python.utils import wrap_repo
from tree_sitter.binding import Node
from frontend.parser.langauges import JAVA_LANGUAGE
from frontend.parser.ast_util import ASTUtil
from returns.maybe import Maybe, Nothing, Some


def get_focal_call(func: Node, ast_util: ASTUtil) -> str:
    """get the focal call from the given function"""
    calls = ast_util.get_all_nodes_of_type(func, "method_invocation")
    func_calls = [ast_util.get_source_from_node(call) for call in calls]

    # todo: add heuristic to find the focal call
    return func_calls[-1]


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

    print(get_focal_call(func, ast_util))


if __name__ == "__main__":
    fire.Fire(main)
