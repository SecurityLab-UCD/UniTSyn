import ast
from pylspclient.lsp_structs import Location, LANGUAGE_IDENTIFIER
from unitsyncer.util import uri2path
from returns.maybe import Maybe, Nothing, Some
from frontend.parser.ast_util import ASTUtil
from frontend.parser.langauges import JAVA_LANGUAGE
from tree_sitter.binding import Node


def get_function_code(
    func_location: Location, lang: str
) -> Maybe[tuple[str, str | None]]:
    """Extract the source code of a function from a Location LSP response

    Args:
        func_location (Location): location of function responsed by LS
        lang (str): language of the file as in LANGUAGE_IDENTIFIER

    Returns:
        Maybe[tuple[str, str | None]]: source code of function, its docstring
    """
    lineno = func_location.range.start.line
    col_offset = func_location.range.start.character

    def get_function_code(file_path) -> Maybe[tuple[str, str | None]]:
        with open(file_path, "r") as file:
            code = file.read()
            ast_util = ASTUtil(code)

        match lang:
            case LANGUAGE_IDENTIFIER.PYTHON:
                node = ast.parse(code, filename=file_path)
                return py_get_def(node, lineno).map(
                    lambda node: (ast.unparse(node), ast.get_docstring(node))
                )
            case LANGUAGE_IDENTIFIER.JAVA:
                tree = ast_util.tree(JAVA_LANGUAGE)
                return java_get_def(tree.root_node, lineno, ast_util).map(
                    lambda node: (ast_util.get_source_from_node(node), None)
                )
            case _:
                return Nothing

    return uri2path(func_location.uri).bind(get_function_code)


def py_get_def(node: ast.AST, lineno: int) -> Maybe[ast.FunctionDef]:
    for child in ast.iter_child_nodes(node):
        if (
            isinstance(child, ast.FunctionDef)
            # AST is 1-indexed, LSP is 0-indexed
            and child.lineno == lineno + 1
            # AST count from def, LSP count from function name
            # and child.col_offset == col_offset - 4
        ):
            return Some(child)
        result = py_get_def(child, lineno)
        if result != Nothing:
            return result

    return Nothing


def java_get_def(node: Node, lineno: int, ast_util: ASTUtil) -> Maybe[Node]:
    for defn in ast_util.get_all_nodes_of_type(node, "method_declaration"):
        if defn.start_point[0] == lineno + 1:
            return Some(defn)
    return Nothing
