from typing import Iterable
from tree_sitter.binding import Node
from frontend.parser.langauges import RUST_LANGUAGE
from frontend.parser.ast_util import ASTUtil, ASTLoc
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


# todo
def get_focal_call(ast_util: ASTUtil, test_func: Node):
    return None, None


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

    # focal = list(filter(is_call_to_test, call_exprs))[0]
    # test_name, test_func = js_get_test_args(ast_util, focal).unwrap()
    # print(test_name)
    # print(ast_util.get_source_from_node(test_func))

    # print(get_focal_call(ast_util, test_func))


if __name__ == "__main__":
    main()
