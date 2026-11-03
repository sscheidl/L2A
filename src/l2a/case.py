"""Case folder layout, import records and path guards. Standard library only (no Ghidra)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

RECORD_NAME = "l2a-imports.json"
IMPORTS_BEGIN = "<!-- l2a:imports:begin -->"
IMPORTS_END = "<!-- l2a:imports:end -->"


class CaseError(Exception):
    """A user-facing error: printed without a traceback."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_checkout_of(path: Path) -> Path | None:
    """The git checkout containing `path` (a directory with `.git`), or None."""
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

    def require_project(self) -> None:
        if not self.project_file.exists():
            raise CaseError(f"no Ghidra project in {self.ghidra_dir}; run `l2a open {self.root} <target> --profile ...` first")

    def load_records(self) -> dict:
        if not self.record_file.exists():
            return {}
        return json.loads(self.record_file.read_text(encoding="utf-8"))

    def save_records(self, records: dict) -> None:
        self.ghidra_dir.mkdir(parents=True, exist_ok=True)
        self.record_file.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def resolve_out(self, out: str, allow_outside: bool = False) -> Path:
        """Resolve a `--out` path. Relative paths go to `<case>/out/`.

        Paths outside the case folder, or inside any git checkout, are refused unless `allow_outside` is set.
        """
        p = Path(out)
        path = (p if p.is_absolute() else self.out_dir / p).resolve()
        if not allow_outside:
            if not is_within(path, self.root):
                raise CaseError(f"--out {path} is outside the case folder {self.root}; use --allow-outside to override")
            checkout = git_checkout_of(path.parent)
            if checkout is not None:
                raise CaseError(f"--out {path} is inside the git checkout {checkout}; use --allow-outside to override")
        return path


def imports_block(records: dict) -> str:
    """Markdown block for case.md describing every import (written by `l2a open`)."""
    lines = [IMPORTS_BEGIN, "## Ghidra imports (written by `l2a open`)", "",
             "| Program | SHA-256 | Profile | Loader / language / compiler | Base | Imported | Functions |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for name in sorted(records):
        r = records[name]
        lines.append(f"| `{name}` | `{r['sha256']}` | {r['profile']} | {r['format']} / `{r['language']}` / "
                     f"`{r['compiler']}` | {r.get('base') or '-'} | {r['imported_at']} | {r['function_count']} |")
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
