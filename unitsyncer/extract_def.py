"""extract test def header for LLM to generate the body"""
import fire
import ast
from frontend.parser.ast_util import ASTUtil
from frontend.parser import GO_LANGUAGE, JAVASCRIPT_LANGUAGE


def py_get_def(code: str) -> str | None:
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            args = [arg.arg for arg in node.args.args]
            return f"def {func_name}({', '.join(args)}):\n"

    return None


def go_get_def(code: str) -> str | None:
    ast_util = ASTUtil(code)
    tree = ast_util.tree(GO_LANGUAGE)
    root = tree.root_node
    func_delcs = ast_util.get_all_nodes_of_type(root, "function_declaration")
    if not func_delcs:
        return None

    test_delc = func_delcs[0]
    test_name_node = ast_util.get_all_nodes_of_type(test_delc, "identifier")[0]
    test_name = ast_util.get_source_from_node(test_name_node)
    return f"func {test_name}(t *testing.T) {{\n"


def js_get_def(code: str) -> str | None:
    ast_util = ASTUtil(code)
    tree = ast_util.tree(JAVASCRIPT_LANGUAGE)
    root = tree.root_node
    func_delcs = ast_util.get_all_nodes_of_type(root, "lexical_declaration")
    if not func_delcs:
        return None

    test_delc = func_delcs[0]
    test_name_node = ast_util.get_all_nodes_of_type(test_delc, "identifier")[0]
    test_name = ast_util.get_source_from_node(test_name_node)
    return f"const {test_name} = () => {{\n"


def get_def_header(code: str, lang: str) -> str | None:
    header: str | None = None
    if lang == "python":
        header = py_get_def(code)
    elif lang == "cpp":
        header = "#undef NDEBUG\n#include<assert.h>\nint main(){\n"
    elif lang == "java":
        header = "\n".join(
            [
                "public class Main {",
                "   public static void main(String[] args) {",
                "   Solution s = new Solution();\n",
            ]
        )
    elif lang == "go":
        header = go_get_def(code)
    elif lang == "js":
        header = js_get_def(code)

    return header


def main():
    code = "const testHasCloseElements = () => {\n  console.assert(hasCloseElements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) === true)\n  console.assert(\n    hasCloseElements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) === false\n  )\n  console.assert(hasCloseElements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) === true)\n  console.assert(hasCloseElements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) === false)\n  console.assert(hasCloseElements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) === true)\n  console.assert(hasCloseElements([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) === true)\n  console.assert(hasCloseElements([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) === false)\n}\n\ntestHasCloseElements()\n"
    print(js_get_def(code))


if __name__ == "__main__":
    fire.Fire(main)
