from __future__ import annotations

import sys
import pathlib
import typing
import json
import dataclasses

@dataclasses.dataclass(frozen=True)
class ParsedLine:
    tree: str
    value: int
    count: int

def _process_line(line: str) -> ParsedLine:
    if "Thread:" in line:
        return None
    names, value, count = line.rsplit(" ", maxsplit=2)
    return ParsedLine(tree=names, value=int(value), count=int(count))

def _process_path(path: pathlib.Path) -> dict[str, ParsedLine]:
    data: dict[str, typing.Numeric] = dict()
    with open(path) as file:
        for line in file:
            entry = _process_line(
                line=line.strip(),
            )
            if entry:
                data[entry.tree] = entry
    return data


def _aggregate(old_roots: list[dict[str, ParsedLine]], normalize: bool) -> dict[str, int]:
    new_root: dict[str, ParsedLine] = dict()
    for root in old_roots:
        for name, total in root.items():
            if name not in new_root:
                new_root[name] = ParsedLine(name, 0, 0)
            new_root[name] = ParsedLine(name, new_root[name].value + root[name].value, new_root[name].count + root[name].count)

    if normalize:
        return {name: entry.value / entry.count for name, entry in new_root.items()}
    else:
        return {name: entry.value for name, entry in new_root.items()}

if __name__ == "__main__":
    roots = map(_process_path, pathlib.Path(".").glob(sys.argv[2]))
    root = _aggregate(old_roots=roots, normalize=sys.argv[3] != "false")
    output = []
    for tree, value in root.items():
        output.append(f"{tree} {value}")
    output.sort()
    for line in output:
        print(line)
