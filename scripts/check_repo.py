"""Repository guard: L2A is public, so no target binaries, dumps or case results may be tracked.

Fails if a tracked file
* matches a .gitignore pattern (for example *.bin, *.dll, Ghidra projects),
* belongs to a case layout (case.md outside templates/, l2a-imports.json, ghidra-backup-*/, target-backup-*/),
* lies in the local case folder L2A-cases/,
* or is larger than the size limit in the index (what would be committed).

Paths are read NUL-separated, so unusual or non-ASCII file names cannot slip past. Standard library only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MAX_BYTES = 1024 * 1024
CASE_FILES = {"case.md", "l2a-imports.json"}
ALLOWED_CASE_FILES = {"templates/case.md"}
BACKUP_PREFIXES = ("ghidra-backup-", "target-backup-")


def git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(["git", *args], cwd=root, input=stdin, check=True, capture_output=True).stdout


def paths(root: Path, *args: str) -> list[str]:
    raw = git(root, "ls-files", "-z", *args)
    return [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]


def index_sizes(root: Path) -> dict[str, int]:
    """Size of every tracked file as staged in the index."""
    entries = [e for e in git(root, "ls-files", "-z", "--stage").split(b"\0") if e]
    objects, names = [], []
    for e in entries:
        meta, name = e.split(b"\t", 1)
        mode, sha, _stage = meta.split()
        if mode == b"160000":  # submodule: no blob
            continue
        objects.append(sha)
        names.append(name.decode("utf-8", "surrogateescape"))
    if not objects:
        return {}
    out = git(root, "cat-file", "--batch-check=%(objectsize)", stdin=b"\n".join(objects) + b"\n")
    return dict(zip(names, (int(x) for x in out.split())))


def problems(root: Path) -> list[str]:
    found = [f"tracked but matches .gitignore: {p!r}" for p in paths(root, "-ci", "--exclude-standard")]
    for p in paths(root):
        parts = p.split("/")
        if parts[0].casefold() == "l2a-cases":  # NTFS does not tell the spellings apart
            found.append(f"local case folder tracked: {p!r}")
        if parts[-1] in CASE_FILES and p not in ALLOWED_CASE_FILES:
            found.append(f"case file tracked: {p!r}")
        if any(part.startswith(BACKUP_PREFIXES) for part in parts):
            found.append(f"case backup tracked: {p!r}")
    for p, size in index_sizes(root).items():
        if size > MAX_BYTES:
            found.append(f"larger than {MAX_BYTES // 1024} KiB: {p!r}")
    return found


def main() -> int:
    root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    found = problems(root)
    for line in found:
        print(f"ERROR: {line}")
    if not found:
        print("repo guard: ok")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
