from __future__ import annotations

import sys
import pathlib
import functools
import itertools
import typing
from collections import defaultdict
import json


sys.path.append(str(pathlib.Path(__file__).parent))
from proc_map_utils import (
    find_lib_load_location,
    read_proc_map,
    find_function_name,
    ProcMap,
    keep_only_base_address,
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

    try:
        function_name = find_function_name(
            address=shifted_address, lib_path=load_location.lib_path
        )
    except:
        function_name = None
    return function_name if function_name else address


def _process_line(line: str, root: dict[str, tuple[list[int], int]], proc_map: ProcMap):
    enter_exit, time_s, callee_address = line.split(",")

    time = int(time_s)
    callee_name = _find_function_name(address=callee_address, proc_map=proc_map)

    last_times, total = root[callee_name]
    if enter_exit == "E":
        last_times.append(time)

    elif enter_exit == "X":
        last_entry_time = last_times.pop()
        root[callee_name] = (last_times, total + (time - last_entry_time))

    else:
        RuntimeError(f"Unexpected value for enter_exit={enter_exit}")


def _process_path(path: pathlib.Path, proc_map: ProcMap) -> dict[str, int]:
    root: dict[str, tuple[list[int], int]] = defaultdict(lambda: ([], 0))
    with open(path) as file:
        for line in file:
            _process_line(
                line=line.strip(),
                root=root,
                proc_map=proc_map,
            )
    return {name: total for name, (_, total) in root.items()}


def _aggregate(old_roots: list[dict[str, int]]) -> dict[str, int]:
    new_root: dict[str, int] = defaultdict(lambda: 0)
    for root in old_roots:
        for name, total in root.items():
            new_root[name] += total
    return new_root


if __name__ == "__main__":
    proc_map = keep_only_base_address(read_proc_map(sys.argv[1]))
    paths = tuple(pathlib.Path(".").glob(sys.argv[2]))

    roots = itertools.starmap(_process_path, ((p, proc_map) for p in paths))
    root = _aggregate(old_roots=roots)
    print(json.dumps(root, indent=3, sort_keys=True))
