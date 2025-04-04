import functools
import subprocess
import re

normalization_pattern = re.compile("(?:\n+|\\(discriminator \\d+\\)|:\\d+)")


def _make_addr2line_cmd(address: str) -> tuple[str, ...]:
    return (
        "addr2line",
        address,
        "-e",
        "./build/lib/libasyncProfiler.so",
        "--functions",
        "--demangle",
        "--inlines",
    )


def _normalize_func_name(raw: str) -> str:
    return re.sub(normalization_pattern, "", raw).strip()


@functools.lru_cache(maxsize=100_000)
def find_function_name(address: str, base_address: int):
    normalized_address = int(address, 16) - base_address
    assert normalized_address > 0
    cmd = _make_addr2line_cmd(hex(normalized_address))
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr)
    return _normalize_func_name(out.stdout)
