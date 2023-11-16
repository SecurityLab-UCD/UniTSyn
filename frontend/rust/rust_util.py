from typing import Iterable
from tree_sitter.binding import Node
from frontend.parser import RUST_LANGUAGE
from frontend.parser.ast_util import ASTUtil, ASTLoc, flatten_postorder
from returns.maybe import Maybe, Nothing, Some
from unitsyncer.util import replace_tabs


def get_test_functions(ast_util: ASTUtil, root_node: Node) -> list[Node]:
    if root_node.type != "source_file":
        return []

    def has_test_annotation(idx: int):
        if root_node.children[idx].type != "attribute_item":
            return False

        # check if the attributes have #[test]
        for child in root_node.children[idx].children:
            for node in ast_util.get_all_nodes_of_type(child, "identifier"):
                if ast_util.get_source_from_node(node) == "test":
                    return True
        return False

    function_items = []
    for idx, child in enumerate(root_node.children):
        if child.type == "function_item" and has_test_annotation(idx - 1):
            function_items.append(child)
    return function_items


def get_first_assert(ast_util: ASTUtil, test_func: Node) -> Maybe[Node]:
    macro_invocations = ast_util.get_all_nodes_of_type(test_func, "macro_invocation")

    for macro_invocation in macro_invocations:
        if (
            ast_util.get_name(macro_invocation)
            .map(lambda name: "assert" in name)
            .value_or(False)
        ):
            return Some(macro_invocation)
    return Nothing


def get_focal_call(
    ast_util: ASTUtil, test_func: Node, is_fuzz: bool = False
) -> Maybe[tuple[str, ASTLoc]]:
    """Get the focal call from the given test function

    Heuristic:
        1. find the first assert macro
        2. expand the macro and find the first call expression in the macro
        3. if no call expression in the macro, back track to find the last call before assert

        if is_fuzz but has no assert, then find the last call in the test function instead of assert
    """

    def expand_assert_and_get_call(assert_macro: Node) -> Maybe[tuple[str, ASTLoc]]:
        token_tree = ast_util.get_all_nodes_of_type(assert_macro, "token_tree")[0]
        code = ast_util.get_source_from_node(token_tree)
        assert_ast_util = ASTUtil(code)
        assert_ast = assert_ast_util.tree(RUST_LANGUAGE)
        assert_root = assert_ast.root_node

        match assert_ast_util.get_all_nodes_of_type(assert_root, "call_expression"):
            case []:
                # todo: no call expression in assert macro,
                # back track to find the last call before assert
                return Nothing
            case [call, *_]:
                name = assert_ast_util.get_source_from_node(call)
                lineno = call.start_point[0] + assert_macro.start_point[0]
                col = call.start_point[1]
                return Some((name, (lineno, col)))

        return Nothing

    first_assert = get_first_assert(ast_util, test_func)
    if first_assert != Nothing:
        return first_assert.bind(expand_assert_and_get_call)
    else:
        if not is_fuzz:
            return Nothing
        match flatten_postorder(test_func, "call_expression"):
            case []:
                return Nothing
            case [call, *_]:
                name = ast_util.get_source_from_node(call)
                return Some((name, call.start_point))

    return Nothing


def main():
    code = """
#[test]
fn encode_all_bytes_url() {
    let bytes: Vec<u8> = (0..=255).collect();

    assert_eq!(
        "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0\
         -P0BBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWltcXV5fYGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6e3x9fn\
         -AgYKDhIWGh4iJiouMjY6PkJGSk5SVlpeYmZqbnJ2en6ChoqOkpaanqKmqq6ytrq\
         -wsbKztLW2t7i5uru8vb6_wMHCw8TFxsfIycrLzM3Oz9DR0tPU1dbX2Nna29zd3t_g4eLj5OXm5-jp6uvs7e7v8PHy\
         8_T19vf4-fr7_P3-_w==",
        &engine::GeneralPurpose::new(&URL_SAFE, PAD).encode(bytes)
    );
}
"""
    ast_util = ASTUtil(replace_tabs(code))
    tree = ast_util.tree(RUST_LANGUAGE)
    root_node = tree.root_node

    test_funcs = get_test_functions(ast_util, root_node)
    func = test_funcs[0]
    print(ast_util.get_source_from_node(func))

    focal_call = get_focal_call(ast_util, func)
    print(focal_call)


if __name__ == "__main__":
    main()
