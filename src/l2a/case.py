"""Case folder layout, import records and path guards. Standard library only (no Ghidra)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

GIT_TIMEOUT_S = 15
CASES_FOLDER = "L2A-cases"
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


def git_excludes(checkout: Path, path: Path) -> bool:
    """True only if git confirms that `path`, below `checkout`, is deliberately kept out of that checkout.

    The deciding rule must come from the checkout's own `info/exclude`, which is local and never pushed. A `.gitignore`
    match does not count: those patterns catch cases created in a checkout by mistake. Nothing below `path` may be
    tracked. Every failure counts as "not excluded": no git, a broken `.git`, a timeout, unexpected output.
    """
    rel = path.relative_to(checkout).as_posix()
    if rel == "." or rel.startswith(":"):  # a leading ":" would be pathspec magic; check-ignore cannot turn that off
        return False
    # An explicit --git-dir stops git from walking up to an outer repository when this `.git` is not valid.
    git = ["git", f"--git-dir={checkout / '.git'}", f"--work-tree={checkout}", "-c", "core.fsmonitor=false"]
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    def run(*args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([*git, *args], cwd=checkout, env=env, input=stdin, capture_output=True,
                              timeout=GIT_TIMEOUT_S)

    try:
        ignored = run("check-ignore", "-v", "-z", "--no-index", "--stdin", stdin=os.fsencode(rel) + b"\0")
        tracked = run("ls-files", "-z", "--", rel)
    except (OSError, subprocess.SubprocessError):
        return False
    fields = ignored.stdout.split(b"\0")
    if ignored.returncode != 0 or tracked.returncode != 0 or tracked.stdout or len(fields) < 3:
        return False
    source, pattern = fields[0].replace(b"\\", b"/"), fields[2]
    return source.endswith(b"info/exclude") and not pattern.startswith(b"!")


def blocking_checkout(path: Path) -> Path | None:
    """The first git checkout around `path` that does not deliberately exclude it, or None."""
    for p in [path, *path.parents]:
        if (p / ".git").exists() and not git_excludes(p, path):
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
        checkout = blocking_checkout(self.root)
        if checkout is not None:
            raise CaseError(f"case folder {self.root} is inside the git checkout {checkout}; cases must live outside "
                            "every checkout, or in a folder listed in that checkout's .git/info/exclude")
        inner = git_checkout_of(self.root)
        if inner is not None and (self.root.parent != inner / CASES_FOLDER or self.root.name.startswith(("_", "."))):
            raise CaseError(f"case folder {self.root} is not a case: inside a checkout, a case is a direct subfolder of "
                            f"{inner / CASES_FOLDER} whose name starts with neither _ nor .")

    def check_layout(self) -> None:
        """Before any write: the case is outside every checkout or deliberately excluded from it, and none of the
        folders or files l2a writes is a link, a junction, or a nested checkout that would redirect the write."""
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
        overwritten. Paths outside the case folder, or in a git checkout that does not exclude them, need
        `allow_outside`.
        """
        p = Path(out)
        path = (p if p.is_absolute() else self.out_dir / p).resolve()
        if is_within(path, self.root):
            if not is_within(path, self.out_dir) or path == self.out_dir:
                raise CaseError(f"--out {path} is inside the case folder but not in {self.out_dir}")
        elif not allow_outside:
            raise CaseError(f"--out {path} is outside the case folder {self.root}; use --allow-outside to override")
        if not allow_outside:
            checkout = blocking_checkout(path.parent)
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
