"""extract test def header for LLM to generate the body"""
import fire
import ast
from frontend.parser.ast_util import ASTUtil
from frontend.parser import (
    GO_LANGUAGE,
    JAVASCRIPT_LANGUAGE,
    CPP_LANGUAGE,
    JAVA_LANGUAGE,
)
from itertools import takewhile
from returns.maybe import Maybe, Nothing, Some


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


def cpp_get_def(code: str) -> str | None:
    ast_util = ASTUtil(code)
    tree = ast_util.tree(CPP_LANGUAGE)
    root = tree.root_node
    func_delcs = ast_util.get_all_nodes_of_type(root, "function_definition")
    if not func_delcs:
        return None

    test_delc = func_delcs[0]
    test_name_node = ast_util.get_all_nodes_of_type(test_delc, "identifier")[0]
    test_name = ast_util.get_source_from_node(test_name_node)
    test_params = ast_util.get_all_nodes_of_type(test_delc, "parameter_declaration")[:2]
    return f"{test_name}({', '.join(map(ast_util.get_source_from_node, test_params))}) {{\n"


def java_get_def(code: str) -> str | None:
    return "".join(takewhile(lambda c: c != "{", code)) + "{\n"


def get_def_header(code: str, lang: str) -> str | None:
    header: str | None = None
    if lang == "python":
        header = py_get_def(code)
    elif lang == "cpp":
        header = cpp_get_def(code)
    elif lang == "java":
        header = java_get_def(code)
    elif lang == "go":
        header = go_get_def(code)
    elif lang == "js":
        header = js_get_def(code)

    return header


def main():
    code = """
@Test
public void testBuildRecordsForUpdate() {
    TcMqMessage message =JsonUtil.jsonToPojo(updateMsg,TcMqMessage.class);
    TableMeta tableMeta=RuleConfigParser.RULES_MAP.getIfPresent("test");
    TableRecords tableRecords=TableRecords.buildRecords(tableMeta,message);
    System.out.println("testBuildRecordsForDelete:"+JsonUtil.objectToJson(tableRecords));
    Assert.assertTrue(StringUtils.isNotBlank(tableRecords.getTableName()));
    Assert.assertEquals(tableRecords.getFieldRows().size(),1);
    Assert.assertEquals(tableRecords.getWhereRows().size(),1);
    Assert.assertNotNull(tableRecords.getMqMessage());
    Assert.assertNotNull(tableRecords.getTableMeta());
    Assert.assertEquals(tableRecords.getFieldRows().get(0).getFields().get(0).getName(),"id");
    Assert.assertEquals(tableRecords.getFieldRows().get(0).getFields().get(0).getKeyType(),KeyType.PRIMARY_KEY);
    Assert.assertEquals(tableRecords.getWhereRows().get(0).getFields().get(0).getName(),"id");
    Assert.assertEquals(tableRecords.getWhereRows().get(0).getFields().get(0).getKeyType(),KeyType.PRIMARY_KEY);
}
"""
    print(java_get_def(code))


if __name__ == "__main__":
    fire.Fire(main)
