from __future__ import annotations

import multiprocessing
import sys
import warnings
import pathlib
import functools
import typing

sys.path.append(str(pathlib.Path(__file__).parent))
from data import TrieNode
from proc_map_utils import (
    find_lib_load_location,
    read_proc_map,
    find_function_name,
    ProcMap,
)


@functools.lru_cache(maxsize=100_000)
def _find_function_name(address: str, proc_map: ProcMap) -> typing.Optional[str]:
    address_int = int(address, base=16)
    load_location = find_lib_load_location(address=address_int, proc_map=proc_map)
    if load_location is None:
        return address

    shifted_address = address_int - load_location.address_start
    if shifted_address < 0:
        raise ValueError(f"{load_location}, {address}")
    return find_function_name(address=shifted_address, lib_path=load_location.lib_path)


def _process_line(line: str, last_trie_node: TrieNode, proc_map: ProcMap) -> TrieNode:
    enter_exit, partial_time_s, partial_time_ns, caller_address, callee_address = (
        line.split(",")
    )

    time_ns = int(partial_time_ns) + int(partial_time_s) * int(1e9)

    caller_name = _find_function_name(address=caller_address, proc_map=proc_map)
    if not caller_name:
        caller_name = caller_address

    callee_name = _find_function_name(address=callee_address, proc_map=proc_map)
    if not callee_name:
        callee_name = callee_address

    if enter_exit == "E":
        if last_trie_node.name != caller_name:
            warnings.warn(f"Last node is '{last_trie_node.name}', got '{caller_name}'")

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


def _process_path(path: pathlib.Path, proc_map: ProcMap) -> TrieNode:
    root = last_trie_node = TrieNode(name=path.name)
    with open(path) as file:
        for line in file:
            last_trie_node = _process_line(
                line=line.strip(), last_trie_node=last_trie_node, proc_map=proc_map
            )

    return root


def _dfs(node: TrieNode, tree: list[str]) -> int:
    tree.append(node.name)
    children_duration_ns = 0
    for child in node.children.values():
        children_duration_ns += _dfs(child, tree)

    print(f"{';'.join(tree)} {node.time_ns - children_duration_ns}")

    tree.pop()

    non_cum_time = node.time_ns - children_duration_ns
    if non_cum_time < 0:
        warnings.warn(f"Non-cumulative time for {node.name} is negative")
    return non_cum_time


if __name__ == "__main__":
    proc_map = read_proc_map(sys.argv[1])

    with multiprocessing.Pool(processes=4) as pool:
        paths = tuple(pathlib.Path(".").glob("traces*.txt"))
        roots = pool.starmap(_process_path, ((p, proc_map) for p in paths))

    for root_node in roots:
        _dfs(root_node, [])
