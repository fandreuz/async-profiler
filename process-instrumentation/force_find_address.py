import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
from proc_map_utils import find_function_name, read_proc_map

if __name__ == "__main__":
    _address = sys.argv[1]
    proc_map = read_proc_map(pathlib.Path(sys.argv[2]))
    for address_start, lib_path in zip(proc_map.address_starts, proc_map.lib_paths):
        if ".so" in lib_path:
            name = find_function_name(
                address=_address, base_address_int=address_start, lib_path=lib_path
            )
            print(f"{lib_path} -> {name}")
