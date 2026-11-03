"""Repository guard: L2A is public, so no target binaries or dumps may be tracked.

Fails if a tracked file matches a .gitignore pattern (for example *.bin, *.dll,
Ghidra projects) or is larger than the size limit. Standard library only.
"""

import subprocess
import sys
from pathlib import Path

MAX_BYTES = 1024 * 1024


def git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line]


def main() -> int:
    root = Path(git("rev-parse", "--show-toplevel")[0])
    problems = [f"tracked but matches .gitignore: {p}" for p in git("ls-files", "-ci", "--exclude-standard")]
    for p in git("ls-files"):
        path = root / p
        if path.is_file() and path.stat().st_size > MAX_BYTES:
            problems.append(f"larger than {MAX_BYTES // 1024} KiB: {p}")
    for line in problems:
        print(f"ERROR: {line}")
    if not problems:
        print("repo guard: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
