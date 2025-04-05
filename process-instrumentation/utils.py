import functools
import subprocess
import re

_normalization_pattern = re.compile("(?:\n+|\\(discriminator \\d+\\)|:\\d+)")
unknown_label = "????"


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


@functools.lru_cache(maxsize=100_000)
def find_function_name(address: str, base_address_int: int, lib_path: str) -> str:
    normalized_address = int(address, 16) - base_address_int
    if normalized_address < 0:
        return None

    cmd = _make_addr2line_cmd(address=hex(normalized_address), lib_path=lib_path)
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr)

    function_name = _normalize_func_name(out.stdout)
    if function_name == unknown_label:
        return None
