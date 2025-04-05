from __future__ import annotations

import multiprocessing
import sys
import warnings
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
from data import TrieNode
from utils import find_function_name


_base_address = int(sys.argv[1], base=16)
_lib_path = "./build/lib/libasyncProfiler.so"


def _process_line(line: str, last_trie_node: TrieNode) -> TrieNode:
    enter_exit, partial_time_s, partial_time_ns, caller_address, callee_address = (
        line.split(",")
    )

    time_ns = int(partial_time_ns) + int(partial_time_s) * int(1e9)

    caller_name = find_function_name(
        address=caller_address, base_address_int=_base_address, lib_path=_lib_path
    )
    if not caller_name:
        caller_name = caller_address

    callee_name = find_function_name(
        address=callee_address, base_address_int=_base_address, lib_path=_lib_path
    )
    if not callee_name:
        callee_name = callee_address

    if enter_exit == "E":
        if last_trie_node.name != caller_name:
            warnings.warn(f"Last node is '{last_trie_node.name}', got {caller_name}")

        if callee_name in last_trie_node.children:
            if last_trie_node.children[callee_name].last_entry_time_ns != -1:
                raise RuntimeError(f"last_entry_time_ns for {callee_name} is not -1")
        else:
            last_trie_node.children[callee_name] = TrieNode(
                name=callee_name, parent=last_trie_node
            )

        last_trie_node.children[callee_name].last_entry_time_ns = time_ns
        return last_trie_node.children[callee_name]

    if enter_exit == "X":
        if last_trie_node.name != callee_name:
            warnings.warn(
                f"The active node is {last_trie_node.name}, not {callee_name}, ignoring"
            )
            return

        if last_trie_node.last_entry_time_ns == -1:
            raise RuntimeError(f"last_entry_time_ns for {callee_name} is -1")

        if last_trie_node.parent is None:
            raise RuntimeError(f"Can't exit from root")

        last_trie_node.time_ns = time_ns - last_trie_node.last_entry_time_ns
        last_trie_node.last_entry_time_ns = -1
        return last_trie_node.parent

    raise RuntimeError(f"Unexpected value for enter_exit={enter_exit}")


def _process_path(path: pathlib.Path) -> TrieNode:
    root = last_trie_node = TrieNode(name=path.name)
    with open(path) as file:
        for line in file:
            last_trie_node = _process_line(line, last_trie_node)

    return root


def _dfs(node: TrieNode, tree: list[str]) -> int:
    tree.append(node.name)
    children_duration_ns = 0
    for child in node.children.values():
        children_duration_ns += _dfs(child, tree)

    print(f"{';'.join(tree)} {node.time_ns - children_duration_ns}")

    tree.pop()
    return node.time_ns - children_duration_ns


with multiprocessing.Pool(processes=4) as pool:
    roots = pool.map(_process_path, tuple(pathlib.Path(".").glob("traces*.txt")))


for root_node in roots:
    _dfs(root_node, [])
