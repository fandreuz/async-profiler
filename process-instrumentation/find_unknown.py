import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent))
from proc_map_utils import find_function_name

_asprof_lib_path = "./build/lib/libasyncProfiler.so"
_known_addresses: set[str] = set()


def _process_address(address: str):
    if address not in _known_addresses:
        _known_addresses.add(address)
        function_name = find_function_name(
            address=address, base_address_int=_base_address, lib_path=_asprof_lib_path
        )
        if not function_name:
            print(f"'{address}'")


def _process_line(line: str):
    *_, caller, callee = line.split(",")
    _process_address(caller)
    _process_address(callee)


def _process_path(path: pathlib.Path):
    with open(path) as file:
        for line in file:
            _process_line(line.strip())


if __name__ == "__main__":
    _base_address = int(sys.argv[1], 16)
    for path in pathlib.Path(".").glob("traces*.txt"):
        _process_path(path)
