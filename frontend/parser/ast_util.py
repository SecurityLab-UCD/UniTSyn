from tree_sitter import Language, Parser, Tree
from tree_sitter.binding import Node, Range
from returns.maybe import Maybe, Nothing, Some
from unitsyncer.common import UNITSYNCER_HOME
from frontend.parser.langauges import JAVA_LANGUAGE


def get_source_from_node(source_code: str, node: Node) -> str:
    start = node.start_byte
    end = node.end_byte
    return source_code[start:end]


def get_method_name(source_code: str, method_node: Node) -> Maybe[str]:
    if method_node.type != "method_declaration":
        return Nothing

    # for a method decl, its name is the first identifier
    for child in method_node.children:
        if child.type == "identifier":
            return Some(get_source_from_node(source_code, child))

    return Nothing


def tree_walker(source_code: str):
    def walk_tree(node):
        if node.type == "method_declaration":
            print(get_method_name(source_code, node).value_or(None))
            # print(extract_source_from_node(node, src))
        for child in node.children:
            walk_tree(child)

    return walk_tree


def get_all_nodes_of_type(root: Node, type: str) -> list[Node]:
    nodes = []
    for child in root.children:
        if child.type == type:
            nodes.append(child)
        nodes += get_all_nodes_of_type(child, type)
    return nodes


def main():
    file_path = f"{UNITSYNCER_HOME}/data/repos/spring-cloud-spring-cloud-netflix/spring-cloud-spring-cloud-netflix-630151f/spring-cloud-netflix-eureka-client/src/test/java/org/springframework/cloud/netflix/eureka/http/AbstractEurekaHttpClientTests.java"
    with open(file_path) as f:
        src = f.read()
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    walk_tree = tree_walker(src)

    tree = parser.parse(bytes(src, "utf8"))
    root_node = tree.root_node
    walk_tree(root_node)


if __name__ == "__main__":
    main()
