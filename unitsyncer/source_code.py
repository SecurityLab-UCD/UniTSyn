import ast
from pylspclient.lsp_structs import Location, LANGUAGE_IDENTIFIER
from unitsyncer.util import replace_tabs, uri2path
from returns.maybe import Maybe, Nothing, Some
from frontend.parser.ast_util import ASTUtil
from frontend.parser.languages import JAVA_LANGUAGE, JAVASCRIPT_LANGUAGE, RUST_LANGUAGE
from tree_sitter.binding import Node
from frontend.parser.ast_util import remove_leading_spaces


def get_function_code(
    func_location: Location, lang: str
) -> Maybe[tuple[str, str | None, str | None]]:
    """Extract the source code of a function from a Location LSP response

    Args:
        func_location (Location): location of function responsed by LS
        lang (str): language of the file as in LANGUAGE_IDENTIFIER

    Returns:
        Maybe[tuple[str, str | None, str | None]]: source code of function, its docstring, code_id
    """
    lineno = func_location.range.start.line
    col_offset = func_location.range.start.character

    def get_function_code(file_path) -> Maybe[tuple[str, str | None, str | None]]:
        with open(file_path, "r", errors="replace") as file:
            code = file.read()

        match lang:
            case LANGUAGE_IDENTIFIER.PYTHON:
                node = ast.parse(code, filename=file_path)
                return py_get_def(node, lineno).map(
                    lambda node: (ast.unparse(node), ast.get_docstring(node), None)
                )
            case LANGUAGE_IDENTIFIER.JAVA:
                ast_util = ASTUtil(replace_tabs(code))
                tree = ast_util.tree(JAVA_LANGUAGE)
                return java_get_def(tree.root_node, lineno, ast_util).map(
                    lambda node: (
                        ast_util.get_source_from_node(node),
                        None,
                        f"{file_path}::{ast_util.get_method_name(node).unwrap()}",
                    )
                )
            case LANGUAGE_IDENTIFIER.JAVASCRIPT:
                ast_util = ASTUtil(replace_tabs(code))
                tree = ast_util.tree(JAVASCRIPT_LANGUAGE)

                return js_get_def(tree.root_node, lineno, ast_util).map(
                    lambda node: (
                        ast_util.get_source_from_node(node),
                        None,
                        # js focal may not be a function, so directly unwrap may fail
                        f"{file_path}::{ast_util.get_name(node).value_or(None)}",
                    )
                )
            case LANGUAGE_IDENTIFIER.RUST:
                ast_util = ASTUtil(replace_tabs(code))
                tree = ast_util.tree(RUST_LANGUAGE)

                return rust_get_def(tree.root_node, lineno, ast_util).map(
                    lambda node: (
                        ast_util.get_source_from_node(node),
                        None,
                        # js focal may not be a function, so directly unwrap may fail
                        f"{file_path}::{ast_util.get_name(node).value_or(None)}",
                    )
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
    def in_modifier_range(method_node: Node, lineno: int) -> bool:
        n_modifier = ast_util.get_method_modifiers(method_node).map(len).value_or(0)
        defn_lineno = method_node.start_point[0]
        return defn_lineno + n_modifier >= lineno

    for defn in ast_util.get_all_nodes_of_type(node, "method_declaration"):
        # tree-sitter AST is 0-indexed
        defn_lineno = defn.start_point[0]
        if defn_lineno == lineno or in_modifier_range(defn, lineno):
            return Some(defn)
    return Nothing


def js_get_def(node: Node, lineno: int, ast_util: ASTUtil) -> Maybe[Node]:
    for defn in ast_util.get_all_nodes_of_type(node, None):
        # tree-sitter AST is 0-indexed
        defn_lineno = defn.start_point[0]
        if defn_lineno == lineno:
            return Some(defn)
    return Nothing


def rust_get_def(node: Node, lineno: int, ast_util: ASTUtil) -> Maybe[Node]:
    for defn in ast_util.get_all_nodes_of_type(node, "function_item"):
        # tree-sitter AST is 0-indexed
        defn_lineno = defn.start_point[0]
        if defn_lineno == lineno:
            return Some(defn)
    return Nothing
