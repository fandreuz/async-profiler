from __future__ import annotations

import pathlib
import dataclasses
import bisect
import typing
import sys
import subprocess
import re

# Remove new lines, (...), line numbers, exceeding spaces
_normalization_pattern = re.compile("(?:\n+|\\s{2,})")


@dataclasses.dataclass(frozen=True)
class ProcMapEntry:
    address_start: int
    lib_path: str


@dataclasses.dataclass(frozen=True)
class ProcMap:
    address_starts: tuple[int]
    lib_paths: tuple[str]


def _make_addr2line_cmd(address: str, lib_path: str) -> tuple[str, ...]:
    return (
        "addr2line",
        address,
        "-e",
        lib_path,
        "--functions",
        "--demangle",
        "--inlines",
    )


def _normalize_func_name(raw: str) -> str:
    return re.sub(_normalization_pattern, "", raw).strip()


def find_function_name(address: int, lib_path: str) -> str:
    cmd = _make_addr2line_cmd(address=hex(address), lib_path=lib_path)
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    if "??" in out.stdout:
        return None

    return _normalize_func_name(out.stdout)


def _process_line(line: str) -> tuple[int, str]:
    line = line.strip()
    address_range, *_, lib_path = line.split(" ")
    address_start = int(address_range.split("-")[0], base=16)
    return address_start, lib_path


def read_proc_map(path: pathlib.Path) -> ProcMap:
    with open(path) as file:
        sorted_data = sorted(_process_line(line.strip()) for line in file)
        addresses, lib_paths = zip(*sorted_data)
        return ProcMap(address_starts=addresses, lib_paths=lib_paths)


def keep_only_base_address(proc_map: ProcMap) -> ProcMap:
    known: set[str] = set()
    filtered_addrs = []
    filtered_paths = []
    for addr, lib_path in zip(proc_map.address_starts, proc_map.lib_paths):
        if lib_path not in known:
            filtered_addrs.append(addr)
            filtered_paths.append(lib_path)
            known.add(lib_path)
    return ProcMap(
        address_starts=tuple(filtered_addrs), lib_paths=tuple(filtered_paths)
    )


def find_lib_load_location(
    address: int, proc_map: ProcMap
) -> typing.Optional[ProcMapEntry]:
    idx = bisect.bisect_right(proc_map.address_starts, address) - 1
    if idx < 0 or idx >= len(proc_map.address_starts):
        return None
    return ProcMapEntry(
        address_start=proc_map.address_starts[idx], lib_path=proc_map.lib_paths[idx]
    )


if __name__ == "__main__":
    proc_map = read_proc_map(pathlib.Path(sys.argv[2]))
    print(find_lib_load_location(address=sys.argv[1], proc_map=proc_map))
