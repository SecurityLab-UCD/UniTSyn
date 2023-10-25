from tree_sitter import Language, Parser, Tree
from tree_sitter.binding import Node
from returns.maybe import Maybe, Nothing, Some
from unitsyncer.common import UNITSYNCER_HOME
from frontend.parser.langauges import JAVA_LANGUAGE

ASTLoc = tuple[int, int]


class ASTUtil:
    def __init__(self, source_code: str) -> None:
        self.src = source_code

    def tree(self, lang: Language) -> Tree:
        parser = Parser()
        parser.set_language(lang)
        return parser.parse(bytes(self.src, "utf8"))

    def get_source_from_node(self, node: Node) -> str:
        match node.type:
            case "method_declaration":
                start = node.start_point[0]
                end = node.end_point[0]
                src_lines = self.src.splitlines()[start : end + 1]
                src_lines = remove_leading_spaces(src_lines)
                return "\n".join(src_lines)
            case _:
                start = node.start_byte
                end = node.end_byte
                return self.src[start:end]

    def get_method_name(self, method_node: Node) -> Maybe[str]:
        if method_node.type != "method_declaration":
            return Nothing

        # for a method decl, its name is the first identifier
        for child in method_node.children:
            if child.type == "identifier":
                return Some(self.get_source_from_node(child))

        return Nothing

    def get_method_modifiers(self, method_node: Node) -> Maybe[list[str]]:
        if method_node.type != "method_declaration":
            return Nothing

        modifiers = []
        for child in method_node.children:
            if child.type == "modifiers":
                for modifier_child in child.children:
                    modifiers.append(self.get_source_from_node(modifier_child))
        return Some(modifiers)

    def get_all_nodes_of_type(self, root: Node, type: str, max_level=50) -> list[Node]:
        nodes = []
        if max_level == 0:
            return nodes

        for child in root.children:
            if child.type == type:
                nodes.append(child)
            nodes += self.get_all_nodes_of_type(child, type, max_level=max_level - 1)
        return nodes


def remove_leading_spaces(lines: list[str]) -> list[str]:
    """remove leading spaces from each line"""
    space_idx = len(lines[0]) - len(lines[0].lstrip())
    return [s[space_idx:] for s in lines]
