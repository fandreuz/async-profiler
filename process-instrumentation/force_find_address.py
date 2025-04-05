import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
from proc_map_utils import find_function_name, read_proc_map

if __name__ == "__main__":
    _address = int(sys.argv[1], base=16)
    proc_map = read_proc_map(pathlib.Path(sys.argv[2]))
    for address_start, lib_path in zip(proc_map.address_starts, proc_map.lib_paths):
        shifted_address = _address - address_start
        if shifted_address > 0 and lib_path and pathlib.Path(lib_path).exists():
            try:
                name = find_function_name(address=shifted_address, lib_path=lib_path)
                print(f"{lib_path} -> {name}")
            except Exception as e:
                print(f"{lib_path} -> {e}")
