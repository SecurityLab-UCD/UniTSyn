from pip._vendor import tomli
from os.path import join as pjoin, isfile, isdir, abspath
import os
from returns.maybe import Maybe, Nothing, Some
from returns.result import Result, Success, Failure
from frontend.parser.ast_util import ASTLoc, ASTUtil
from frontend.parser.langauges import RUST_LANGUAGE
from tree_sitter import Language, Parser, Tree
from tree_sitter.binding import Node
from pylspclient.lsp_structs import Location, LANGUAGE_IDENTIFIER, Range, Position
from unitsyncer.source_code import get_function_code
from unitsyncer.util import path2uri, uri2path
from returns.converters import maybe_to_result
from unitsyncer.sync import Synchronizer
from pylspclient.lsp_structs import LANGUAGE_IDENTIFIER


class RustSynchronizer(Synchronizer):
    def __init__(self, workspace_dir: str, language="rust") -> None:
        super().__init__(workspace_dir, LANGUAGE_IDENTIFIER.RUST)
        self.file_func_map: dict[str, list[tuple[str, Node]]] = {}

    def initialize(self, timeout: int = 10):
        """index all files and functions in the workdir/src"""
        src_dir = pjoin(self.workspace_dir, "src")
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".rs"):
                    file_path = pjoin(root, file)
                    funcs = self._get_file_functions(file_path)
                    self.file_func_map[file_path] = funcs

    def _get_file_functions(self, file_path: str) -> list[tuple[str, Node]]:
        """get all function items in the given file

        Args:
            file_path (str): path to source code file

        Returns:
            list[tuple[str, Node]]: [(function_name, function_node)]
        """
        ast_util = ASTUtil(open(file_path).read())
        tree = ast_util.tree(RUST_LANGUAGE)
        nodes = ast_util.get_all_nodes_of_type(tree.root_node, "function_item")
        names = [ast_util.get_name(node).value_or("") for node in nodes]
        return list(zip(names, nodes))

    # todo: align type with sync.py
    def get_source_of_call(
        self, focal_name: str
    ) -> Result[tuple[str, str | None, str | None], str]:
        match self.goto_definition(focal_name):
            case [] | None:
                return Failure("Not Definition Found")
            case [loc, *_]:
                # todo: find best match based on imports of test file

                def not_found_error(_):
                    file_path = uri2path(loc.uri).value_or("")
                    lineno = loc.range.start.line
                    col_offset = loc.range.start.character
                    return f"Source code not found: {file_path}:{lineno}:{col_offset}"

                return (
                    maybe_to_result(get_function_code(loc, LANGUAGE_IDENTIFIER.RUST))
                    .alt(not_found_error)
                    .bind(
                        lambda t: Failure("Empty Source Code")
                        if t[0] == ""
                        else Success(t)
                    )
                )
            case _:
                return Failure("Unexpected Error")

    def goto_definition(self, focal_name: str) -> list[Location]:
        """get the definition of the given function name

        Args:
            focal_name (str): name of the function

        Returns:
            list[Location]: all locations of function definition with focal_name
        """
        results = []
        for file_path, funcs in self.file_func_map.items():
            for name, node in funcs:
                if name == focal_name:
                    uri = path2uri(file_path)
                    range_ = Range(
                        Position(*node.start_point),
                        Position(*node.end_point),
                    )
                    results.append(Location(uri, range_))
        return results

    def stop(self):
        pass


def main():
    workdir = "data/repos/marshallpierce-rust-base64/marshallpierce-rust-base64-4ef33cc"
    lsp = RustSynchronizer(workdir)
    lsp.initialize()

    print(lsp.get_source_of_call("decode"))


if __name__ == "__main__":
    main()
