import ast
from pylspclient.lsp_structs import Location
from unitsyncer.util import uri2path
from returns.maybe import Maybe, Nothing, Some
import astunparse


def python_get_function_code(func_location: Location) -> Maybe[str]:
    """Extract the source code of a function from a Location LSP response

    Args:
        func_location (Location): location of function responsed by LSP

    Returns:
        Maybe[str]: source code of function
    """
    lineno = func_location.range.start.line
    col_offset = func_location.range.start.character

    def search_target_def(node: ast.AST) -> Maybe[ast.FunctionDef]:
        for child in ast.iter_child_nodes(node):
            if (
                isinstance(child, ast.FunctionDef)
                # AST is 1-indexed, LSP is 0-indexed
                and child.lineno == lineno + 1
                # AST count from def, LSP count from function name
                and child.col_offset == col_offset - 4
            ):
                return Some(child)
            result = search_target_def(child)
            if result != Nothing:
                return result

        return Nothing

    def get_function_code(file_path) -> Maybe[str]:
        with open(file_path, "r") as file:
            node = ast.parse(file.read(), filename=file_path)

        return search_target_def(node).map(astunparse.unparse)

    return uri2path(func_location.uri).bind(get_function_code)
