import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
from utils import find_function_name

_address = sys.argv[1]

with open("proc_maps.txt") as file:
    for line in file:
        if ".so" in line:
            address_range, *_, lib_path = line.split(" ")
            address_start = int(address_range.split("-")[0].strip(), base=16)
            lib_path = lib_path.strip()

            name = find_function_name(
                address=_address, base_address_int=address_start, lib_path=lib_path
            )
            print(f"{lib_path} -> {name}")
