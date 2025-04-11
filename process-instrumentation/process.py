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
    keep_only_base_address,
)

last_time: int = -1


@functools.lru_cache(maxsize=100_000)
def _find_function_name(address: str, proc_map: ProcMap) -> typing.Optional[str]:
    address_int = int(address, base=16)
    load_location = find_lib_load_location(address=address_int, proc_map=proc_map)
    if load_location is None:
        return address

    shifted_address = address_int - load_location.address_start
    if shifted_address < 0:
        raise ValueError(f"{load_location}, {address}")

    try:
        function_name = find_function_name(
            address=shifted_address, lib_path=load_location.lib_path
        )
    except:
        function_name = None
    return function_name if function_name else address


def _process_line(
    line: str, last_trie_node: TrieNode, proc_map: ProcMap, current_time: int
) -> tuple[TrieNode, int]:
    enter_exit, time_s, caller_address, callee_address = line.split(",")

    time = int(time_s)
    if time < last_time:
        raise ValueError(
            f"Expected monotonically increasing time, offending line: {line}"
        )
    current_time += time
    # Make sure it's not used anymore
    del time

    caller_name = _find_function_name(address=caller_address, proc_map=proc_map)
    callee_name = _find_function_name(address=callee_address, proc_map=proc_map)

    if enter_exit == "E":
        if not last_trie_node.is_root and last_trie_node.name != caller_name:
            warnings.warn(
                f"Last node is '{last_trie_node.name}', got '{caller_name}', line: '{line}'"
            )
        # Let's just assume that the address points to a different line in the same function

        if callee_name in last_trie_node.children:
            if last_trie_node.children[callee_name].last_entry_time != -1:
                raise RuntimeError(f"last_entry_time for {callee_name} is not -1")
        else:
            last_trie_node.children[callee_name] = TrieNode(
                name=callee_name, parent=last_trie_node
            )

        node = last_trie_node.children[callee_name]
        node.last_entry_time = current_time
        return node, current_time

    elif enter_exit == "X":
        if last_trie_node.name != callee_name:
            raise RuntimeError(
                f"The current trie node is {last_trie_node.name}, not {callee_name}"
            )

        if last_trie_node.last_entry_time == -1:
            raise RuntimeError(f"last_entry_time for {callee_name} is -1")

        if last_trie_node.is_root:
            raise RuntimeError(f"Can't exit from root")

        last_trie_node.time_total += current_time - last_trie_node.last_entry_time
        last_trie_node.last_entry_time = -1
        return last_trie_node.parent, current_time

    raise RuntimeError(f"Unexpected value for enter_exit={enter_exit}")


def _process_path(path: pathlib.Path, proc_map: ProcMap) -> TrieNode:
    root = last_trie_node = TrieNode(name=path.name)

    with open(path) as file:
        current_time = 0
        for line in file:
            last_trie_node, current_time = _process_line(
                line=line.strip(),
                last_trie_node=last_trie_node,
                proc_map=proc_map,
                current_time=current_time,
            )

    if last_trie_node is not root:
        raise RuntimeError(
            f"The stack for {path} did not come back to the root: {last_trie_node}"
        )

    for child in root.children.values():
        root.time_total += child.time_total

    return root


def _dfs(node: TrieNode, tree: list[str]) -> int:
    tree.append(node.name)
    children_duration_ns = 0
    for child_name in sorted(node.children.keys()):
        children_duration_ns += _dfs(node.children[child_name], tree)

    print(f"{';'.join(tree)} {node.time_total - children_duration_ns}")
    tree.pop()

    non_cum_time = node.time_total - children_duration_ns
    if non_cum_time < 0:
        warnings.warn(f"Non-cumulative time for {node.name} is negative")
        return 0

    return non_cum_time


def _into_new_root(root: TrieNode, old_root: TrieNode):
    root.time_total += old_root.time_total
    for child_name, old_child in old_root.children.items():
        if child_name not in root.children:
            root.children[child_name] = TrieNode(name=child_name, parent=root)
        _into_new_root(root.children[child_name], old_child)


def _aggregate(root: TrieNode, old_roots: list[TrieNode]) -> TrieNode:
    new_root = TrieNode(name="root")
    for root in old_roots:
        _into_new_root(root=new_root, old_root=root)
    return new_root


if __name__ == "__main__":
    proc_map = keep_only_base_address(read_proc_map(sys.argv[1]))
    paths = tuple(pathlib.Path(".").glob(sys.argv[2]))

    with multiprocessing.Pool(processes=len(paths) // 4) as pool:
        roots = pool.starmap(_process_path, ((p, proc_map) for p in paths))

    root = TrieNode(name="root")
    if len(sys.argv) == 4 and bool(sys.argv[3]):
        root = _aggregate(root=root, old_roots=roots)
    else:
        for old_root in roots:
            root.children[old_root.name] = old_root
            old_root.parent = root

    _dfs(root, [])
