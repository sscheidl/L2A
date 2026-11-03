"""Case folder layout, import records and path guards. Standard library only (no Ghidra)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

RECORD_NAME = "l2a-imports.json"
IMPORTS_BEGIN = "<!-- l2a:imports:begin -->"
IMPORTS_END = "<!-- l2a:imports:end -->"
PROGRAM_NAME_EXTRA = set(" ._+-()[]")


class CaseError(Exception):
    """A user-facing error: printed without a traceback."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_checkout_of(path: Path) -> Path | None:
    """The git checkout containing `path` (a directory with `.git`, folder or file), or None."""
    for p in [path, *path.parents]:
        if (p / ".git").exists():
            return p
    return None


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def is_link(path: Path) -> bool:
    """A symbolic link or an NTFS junction (both redirect writes elsewhere)."""
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def write_text_atomic(path: Path, text: str) -> None:
    """Write a new file and swap it in. An existing hard link to the old file is never written through."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def check_program_name(name: str) -> str:
    """A program name must be one plain path component: letters, digits and ` ._+-()[]`, not starting with a dot."""
    if not name or len(name) > 128 or name.startswith(".") or not all(c.isalnum() or c in PROGRAM_NAME_EXTRA
                                                                       for c in name):
        raise CaseError(f"unsupported program name {json.dumps(name)}; use --name with letters, digits and ' ._+-()[]'")
    return name


@dataclass(frozen=True)
class Case:
    root: Path

    @classmethod
    def at(cls, path: str | Path) -> "Case":
        return cls(Path(path).resolve())

    @property
    def name(self) -> str:
        # Ghidra project names may not contain some characters; keep it simple and safe.
        return re.sub(r"[^A-Za-z0-9._-]", "_", self.root.name)

    @property
    def ghidra_dir(self) -> Path:
        return self.root / "ghidra"

    @property
    def project_file(self) -> Path:
        return self.ghidra_dir / f"{self.name}.gpr"

    @property
    def out_dir(self) -> Path:
        return self.root / "out"

    @property
    def target_dir(self) -> Path:
        return self.root / "target"

    @property
    def record_file(self) -> Path:
        return self.ghidra_dir / RECORD_NAME

    @property
    def case_md(self) -> Path:
        return self.root / "case.md"

    def check_not_in_git(self) -> None:
        checkout = git_checkout_of(self.root)
        if checkout is not None:
            raise CaseError(f"case folder {self.root} is inside the git checkout {checkout}; "
                            "cases must live outside every checkout (default D:\\L2A-cases\\)")

    def check_layout(self) -> None:
        """Before any write: the case is outside every checkout, and none of the folders or files l2a writes is a
        link, a junction, or a nested checkout that would redirect the write."""
        self.check_not_in_git()
        for p in (self.target_dir, self.ghidra_dir, self.out_dir, self.case_md, self.record_file, self.project_file):
            if is_link(p):
                raise CaseError(f"{p} is a link or junction; l2a does not write through links")
            if p.exists() and not is_within(p.resolve(), self.root):
                raise CaseError(f"{p} resolves outside the case folder {self.root}")
            if p.is_dir() and (p / ".git").exists():
                raise CaseError(f"{p} contains a git checkout; l2a does not write into checkouts")

    def require_project(self) -> None:
        if not self.project_file.exists():
            raise CaseError(f"no Ghidra project in {self.ghidra_dir}; run `l2a open {self.root} <target> --profile ...` first")

    def load_records(self) -> dict:
        if not self.record_file.exists():
            return {}
        return json.loads(self.record_file.read_text(encoding="utf-8"))

    def save_records(self, records: dict) -> None:
        write_text_atomic(self.record_file, json.dumps(records, indent=2, sort_keys=True) + "\n")

    def resolve_out(self, out: str, allow_outside: bool = False) -> Path:
        """Resolve a `--out` path. Relative paths go to `<case>/out/`.

        Inside the case folder, only `<case>/out/` is allowed; the project, records, targets and case.md are never
        overwritten. Paths outside the case folder, or inside any git checkout, need `allow_outside`.
        """
        p = Path(out)
        path = (p if p.is_absolute() else self.out_dir / p).resolve()
        if is_within(path, self.root):
            if not is_within(path, self.out_dir) or path == self.out_dir:
                raise CaseError(f"--out {path} is inside the case folder but not in {self.out_dir}")
        elif not allow_outside:
            raise CaseError(f"--out {path} is outside the case folder {self.root}; use --allow-outside to override")
        if not allow_outside:
            checkout = git_checkout_of(path.parent)
            if checkout is not None:
                raise CaseError(f"--out {path} is inside the git checkout {checkout}; use --allow-outside to override")
        return path


def md_code(text: str) -> str:
    """Inline Markdown code for an untrusted name in a table cell: no raw controls, pipes or unbalanced backticks."""
    s = "".join(c if c.isprintable() else f"\\x{ord(c):02x}" for c in str(text)).replace("|", "\\|")
    run = max((len(m) for m in re.findall(r"`+", s)), default=0)
    fence = "`" * (run + 1)
    pad = " " if s.startswith("`") or s.endswith("`") else ""
    return f"{fence}{pad}{s}{pad}{fence}"


def imports_block(records: dict) -> str:
    """Markdown block for case.md describing every import (written by `l2a open`)."""
    lines = [IMPORTS_BEGIN, "## Ghidra imports (written by `l2a open`)", "",
             "| Program | SHA-256 | Profile | Loader / language / compiler | Base | Imported | Functions |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for name in sorted(records):
        r = records[name]
        cells = [md_code(name), md_code(r["sha256"]), md_code(r["profile"]),
                 f"{md_code(r['format'])} / {md_code(r['language'])} / {md_code(r['compiler'])}",
                 md_code(r.get("base") or "-"), md_code(r["imported_at"]), md_code(r["function_count"])]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "Settings, timings and tool versions: `ghidra\\" + RECORD_NAME + "`.", IMPORTS_END]
    return "\n".join(lines)


def update_case_md(text: str, block: str) -> str:
    """Replace the l2a imports block, or insert it before '## Findings' (else append)."""
    if IMPORTS_BEGIN in text and IMPORTS_END in text:
        start = text.index(IMPORTS_BEGIN)
        end = text.index(IMPORTS_END) + len(IMPORTS_END)
        return text[:start] + block + text[end:]
    marker = "\n## Findings"
    if marker in text:
        i = text.index(marker) + 1
        return text[:i] + block + "\n\n" + text[i:]
    return text.rstrip("\n") + "\n\n" + block + "\n"


def initial_case_md(case_name: str, template: Path | None) -> str:
    if template is not None and template.exists():
        return template.read_text(encoding="utf-8").replace("<short name>", case_name, 1)
    return f"# Case: {case_name}\n\nSee `templates/case.md` in the L2A repository for the full template.\n"
