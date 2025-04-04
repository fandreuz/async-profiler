import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent))
from utils import find_function_name

base_address = int(sys.argv[1], 16)
known_addresses: set[str] = set()


def _process_address(address: str):
    if address not in known_addresses:
        known_addresses.add(address)
        function_name = find_function_name(address, base_address)
        if function_name == "????":
            print(f"{address}")


def _process_line(line: str):
    *_, caller, callee = line.split(",")
    _process_address(caller)
    _process_address(callee)


def _process_path(path: pathlib.Path):
    with open(path) as file:
        for line in file:
            _process_line(line)


for path in pathlib.Path(".").glob("traces*.txt"):
    _process_path(path)
