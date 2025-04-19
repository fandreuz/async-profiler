from __future__ import annotations

import sys
import pathlib
import functools
import itertools
import typing
import json
import dataclasses

sys.path.append(str(pathlib.Path(__file__).parent))
from proc_map_utils import (
    find_lib_load_location,
    read_proc_map,
    find_function_name,
    ProcMap,
    keep_only_base_address,
)

@dataclasses.dataclass(frozen=True)
class ParsedLine:
    tree: str
    value: int
    count: int

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

def _process_line(line: str, proc_map: ProcMap) -> ParsedLine:
    if "Thread:" in line:
        return None
    addrs = line.split(";")

    addrs[-1], value, count = addrs[-1].split(" ", maxsplit=3)
    names = []
    for addr in addrs:
        names.append(_find_function_name(addr, proc_map))
    return ParsedLine(tree=";".join(names), value=int(value), count=int(count))

def _process_path(path: pathlib.Path, proc_map: ProcMap) -> dict[str, ParsedLine]:
    data: dict[str, typing.Numeric] = dict()
    with open(path) as file:
        for line in file:
            entry = _process_line(
                line=line.strip(),
                proc_map=proc_map,
            )
            if not entry:
                if "Compiler" in line:
                    break
            else:
                data[entry.tree] = entry
    return data


def _aggregate(old_roots: list[dict[str, ParsedLine]]) -> dict[str, int]:
    new_root: dict[str, ParsedLine] = dict()
    for root in old_roots:
        for name, total in root.items():
            if name not in new_root:
                new_root[name] = ParsedLine(name, 0, 0)
            new_root[name] = ParsedLine(name, new_root[name].value + root[name].value, new_root[name].count + root[name].count)

    return {name: entry.value / entry.count for name, entry in new_root.items()}

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
