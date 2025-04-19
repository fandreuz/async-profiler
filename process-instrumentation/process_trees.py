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

def _process_line(line: str, proc_map: ProcMap) -> tuple[str, typing.Numeric]:
    if "Thread:" in line:
        return None, None
    addrs = line.split(";")

    addrs[-1], value, count = addrs[-1].split(" ", maxsplit=3)
    names = []
    for addr in addrs:
        names.append(_find_function_name(addr, proc_map))
    return ";".join(names), int(int(value) / int(count))

def _process_path(path: pathlib.Path, proc_map: ProcMap) -> dict[str, typing.Numeric]:
    data: dict[str, typing.Numeric] = dict()
    with open(path) as file:
        for line in file:
            tree, value = _process_line(
                line=line.strip(),
                proc_map=proc_map,
            )
            if not tree:
                if "Compiler" in line:
                    break
            else:
                data[tree] = value
    return data


def _aggregate(old_roots: list[dict[str, typing.Numeric]]) -> dict[str, typing.Numeric]:
    new_root: dict[str, typing.Numeric] = defaultdict(lambda: 0)
    for root in old_roots:
        for name, total in root.items():
            new_root[name] += total
    return new_root

if __name__ == "__main__":
    proc_map = keep_only_base_address(read_proc_map(sys.argv[1]))
    paths = tuple(pathlib.Path(".").glob(sys.argv[2]))

    roots = itertools.starmap(_process_path, ((p, proc_map) for p in paths))
    root = _aggregate(old_roots=roots)
    output = []
    for tree, value in root.items():
        output.append(f"{tree} {value}")
    output.sort()
    for line in output:
        print(line)
