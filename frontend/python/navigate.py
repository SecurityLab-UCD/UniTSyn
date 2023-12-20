"""util functions to navigate in python repo"""
import os
import sys
import ast
import jedi
from typing import Optional, Callable, List, Union


class ModuleNavigator:
    """provide utils function using ast"""

    def __init__(self, path: str):
        self.path = path
        self.ast = ast.parse(open(path, "r").read())
        self.nodes, self.parents = flatten(self.ast)

    def find_all(self, ntype: Union[type, Callable], root: Optional[ast.AST] = None):
        if root is None:
            root, nodes = self.ast, self.nodes
        else:
            nodes = None
        return find_all(root, ntype, nodes=nodes)

    def find_by_name(self, name: str, root: Optional[ast.AST] = None):
        if root is None:
            root, nodes = self.ast, self.nodes
        else:
            nodes = None
        return find_by_name(root, name, nodes=nodes)

    def get_path_to(self, node: ast.AST):
        return get_path_to(self.ast, node, nodes=self.nodes, parents=self.parents)

    def postorder(self, root: Optional[ast.AST] = None):
        nodes = []

        def walk(n):
            children = []
            for f in getattr(n, "_fields", []):
                field = getattr(n, f, [])
                if isinstance(field, (tuple, list)):
                    children.extend(field)
                else:
                    children.append(field)
            for child in children:
                walk(child)
            nodes.append(n)

        walk(root if root is not None else self.root)
        return nodes

    def __str__(self):
        return ast.dump(self.ast)


def flatten(root: ast.AST):
    """flatten an ast pre-order"""
    nodes, parents = [], []

    def walk(n, p=None):
        nidx = len(nodes)
        nodes.append(n)
        parents.append(p)
        children = []
        for f in getattr(n, "_fields", []):
            field = getattr(n, f, [])
            if isinstance(field, (tuple, list)):
                children.extend(field)
            else:
                children.append(field)
        for child in children:
            walk(child, nidx)

    walk(root)
    assert len(nodes) == len(parents)
    return nodes, parents


def find_all(
    root: ast.AST,
    condition: Union[type, Callable],
    nodes: Optional[List[ast.AST]] = None,
):
    """return all nodes of the desired type"""
    if nodes is None:
        nodes, _ = flatten(root)
    if isinstance(condition, type):
        _filter = lambda x: isinstance(x, condition)
    else:
        _filter = condition
    return [node for node in nodes if _filter(node)]


def find_by_name(root: ast.AST, name: str, nodes: Optional[List[ast.AST]] = None):
    """find node by name, return the first one if duplicated"""
    if nodes is None:
        nodes, _ = flatten(root)
    for node in nodes:
        if getattr(node, "name", None) == name:
            return node
    return None


def get_path_to(
    root: ast.AST,
    target: ast.AST,
    nodes: Optional[List[ast.AST]] = None,
    parents: Optional[List[int]] = None,
):
    if None not in (nodes, parents):
        nodes, parents = flatten(root)
    else:
        assert len(nodes) == len(parents), "nodes and parents should have the same size"
    # find the path to target bottom-up
    try:
        target_idx = nodes.index(target)
    except ValueError:
        return None
    path = []
    while target_idx is not None:
        path.append(nodes[target_idx])
        target_idx = parents[target_idx]
    return path[::-1]


def dump_ast_func(
    func: ast.AST,
    path: str,
    nav: Optional[ModuleNavigator] = None,
    ancestors: Optional[List[ast.AST]] = None,
    return_nav: Optional[bool] = False,
):
    """converts an ast node of function into string"""
    if nav is None and ancestors is None:
        nav = ModuleNavigator(path)
    if ancestors is None:
        ancestors = nav.get_path_to(func)
    classes = [n.name for n in ancestors if isinstance(n, ast.ClassDef)]
    func_id = "::".join([path] + classes + [func.name])
    if not return_nav:
        return func_id
    return func_id, nav


def load_ast_func(
    func_id: str,
    nav: Optional[ModuleNavigator] = None,
    return_nav: Optional[bool] = False,
):
    """convert a string to an ast node of function"""
    ancestors, node = func_id.split("::"), None
    path = ancestors.pop(0)
    if nav is None:
        nav = ModuleNavigator(path)
    while ancestors:
        node_id = ancestors.pop(0)
        node = nav.find_by_name(node_id, root=node)
    if not return_nav:
        return node
    return node, nav


def is_assert(node: ast.AST):
    """tell if a node is an assertion"""
    if isinstance(node, ast.Assert):
        return True
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id.startswith("assert"):
            return True
        if isinstance(func, ast.Attribute) and func.attr.startswith("assert"):
            return True
    return False
