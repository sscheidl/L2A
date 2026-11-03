"""Ghidra access through PyGhidra: start-up, project, import with verification, Cortex-M vector table.

Only this module and `queries.py` import Ghidra classes; they do so after `start()`.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from importlib.metadata import version as pkg_version
from pathlib import Path

from . import vectors
from .case import Case, CaseError
from .output import quote
from .profiles import FORMAT_RAW, ImportSettings

# Pinned tools (docs/TOOLCHAIN.md). Environment variables may point elsewhere, but versions are enforced.
PINNED_GHIDRA = "12.1.4"
PINNED_JDK = "21.0.12.1"
DEFAULT_GHIDRA = r"C:\Tools\ghidra_12.1.4_PUBLIC"
DEFAULT_JDK = r"C:\Tools\jdk-21.0.12.1+1"
# Opt-ins for a deliberate deviation from the reviewed tool set.
ALLOW_UNPINNED = "L2A_ALLOW_UNPINNED"
ALLOW_EXTENSIONS = "L2A_ALLOW_EXTENSIONS"
ENTRY_POINT_GROUPS = ("pyghidra.setup", "pyghidra.pre_launch")

_env: dict | None = None


def _properties(path: Path, key: str) -> str:
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return "unknown"


def _user_extension_dirs(install: Path) -> list[Path]:
    """Ghidra's per-user Extensions folders for this install ([user settings]/Extensions)."""
    props = install / "Ghidra" / "application.properties"
    name = (f"ghidra_{_properties(props, 'application.version')}_"
            f"{_properties(props, 'application.release.name')}")
    bases = [os.environ.get("XDG_CONFIG_HOME"), os.environ.get("APPDATA")]
    return [Path(b) / "ghidra" / name / "Extensions" for b in bases if b]


def tool_trust_problems(ghidra_version: str, jdk_version: str, extensions: list[str], entry_points: list[str],
                        allow_unpinned: bool, allow_extensions: bool) -> list[str]:
    """Why the selected tool set is not the reviewed one (empty list: it is)."""
    problems = []
    if not allow_unpinned:
        if ghidra_version != PINNED_GHIDRA:
            problems.append(f"Ghidra {ghidra_version} is not the pinned {PINNED_GHIDRA}")
        if jdk_version != PINNED_JDK:
            problems.append(f"JDK {jdk_version} is not the pinned {PINNED_JDK}")
    if not allow_extensions:
        problems += [f"installed Ghidra user extension {e}" for e in extensions]
        problems += [f"PyGhidra start-up entry point {e}" for e in entry_points]
    return problems


def start() -> dict:
    """Start the JVM and Ghidra once per process. Returns the tool versions in use."""
    global _env
    if _env is not None:
        return _env
    from importlib.metadata import entry_points

    install = Path(os.environ.get("GHIDRA_INSTALL_DIR") or DEFAULT_GHIDRA)
    jdk = os.environ.get("JAVA_HOME_OVERRIDE") or (DEFAULT_JDK if Path(DEFAULT_JDK).is_dir() else os.environ.get("JAVA_HOME"))
    if not (install / "Ghidra" / "application.properties").is_file():
        raise CaseError(f"Ghidra not found at {install}; set GHIDRA_INSTALL_DIR")
    if not jdk or not Path(jdk).is_dir():
        raise CaseError("JDK 21 not found; set JAVA_HOME_OVERRIDE or JAVA_HOME")
    ghidra_version = _properties(install / "Ghidra" / "application.properties", "application.version")
    jdk_version = _properties(Path(jdk) / "release", "JAVA_VERSION")
    extensions = sorted(str(p) for d in _user_extension_dirs(install) if d.is_dir() for p in d.iterdir())
    eps = sorted(f"{g}:{ep.name}={ep.value}" for g in ENTRY_POINT_GROUPS for ep in entry_points(group=g))
    allow_unpinned = os.environ.get(ALLOW_UNPINNED) == "1"
    allow_extensions = os.environ.get(ALLOW_EXTENSIONS) == "1"
    problems = tool_trust_problems(ghidra_version, jdk_version, extensions, eps, allow_unpinned, allow_extensions)
    if problems:
        raise CaseError("the tool set differs from the reviewed one (docs/TOOLCHAIN.md):\n  " + "\n  ".join(problems)
                        + f"\nSet {ALLOW_UNPINNED}=1 or {ALLOW_EXTENSIONS}=1 only for a deliberate deviation.")
    if allow_unpinned or allow_extensions:
        print(f"[l2a] WARNING: tool-trust opt-in active ({ALLOW_UNPINNED}={int(allow_unpinned)}, "
              f"{ALLOW_EXTENSIONS}={int(allow_extensions)}); extensions: {len(extensions)}, entry points: {len(eps)}",
              file=sys.stderr)
    # JAVA_HOME_OVERRIDE makes PyGhidra use this JDK instead of searching for one.
    os.environ["GHIDRA_INSTALL_DIR"] = str(install)
    os.environ["JAVA_HOME_OVERRIDE"] = str(jdk)
    import pyghidra

    pyghidra.start(install_dir=install)
    from java.lang import System

    _env = {"ghidra": ghidra_version, "ghidra_dir": str(install), "java": str(System.getProperty("java.version")),
            "java_home": str(jdk), "pyghidra": pkg_version("pyghidra"),
            "trust": {"allow_unpinned": allow_unpinned, "allow_extensions": allow_extensions,
                      "extensions": extensions, "entry_points": eps}}
    return _env


def monitor():
    import pyghidra

    return pyghidra.task_monitor()


def open_project(case: Case, create: bool):
    import pyghidra

    if create:
        case.ghidra_dir.mkdir(parents=True, exist_ok=True)
    else:
        case.require_project()
    try:
        return pyghidra.open_project(str(case.ghidra_dir), case.name, create=create)
    except Exception as e:  # Java exceptions arrive as Python exceptions
        if "Lock" in type(e).__name__ or "lock" in str(e).lower():
            raise CaseError(f"project {case.project_file} is locked; close it in the Ghidra GUI first ({quote(e)})") from None
        raise


def program_names(project) -> list[str]:
    return sorted(str(f.getName()) for f in project.getProjectData().getRootFolder().getFiles())


def domain_file(project, name: str):
    return project.getProjectData().getFile("/" + name)


@contextmanager
def read_program(project, name: str):
    """Open a program read-only: queries can never change or save the project."""
    from ghidra.framework.model import DomainFile
    from java.lang import Object

    df = domain_file(project, name)
    if df is None:
        raise CaseError(f"program {quote(name)} not in the project; programs: "
                        f"{', '.join(quote(n) for n in program_names(project)) or 'none'}")
    consumer = Object()
    program = df.getReadOnlyDomainObject(consumer, DomainFile.DEFAULT_VERSION, monitor())
    try:
        yield program
    finally:
        program.release(consumer)


def load(project, target: Path, name: str, settings: ImportSettings):
    """Import into memory (not yet saved). Returns Ghidra LoadResults."""
    import pyghidra

    b = (pyghidra.program_loader().project(project).source(str(target)).name(name).projectFolderPath("/")
         .loaders(settings.profile.loader).monitor(monitor()))
    if settings.language:
        b = b.language(settings.language)
    if settings.compiler:
        b = b.compiler(settings.compiler)
    for key, value in settings.loader_args():
        b = b.addLoaderArg(key, value)
    try:
        return b.load()
    except Exception as e:
        raise CaseError(f"{settings.profile.loader} could not load {quote(target.name)}: {quote(e)}") from None


def loaded_blocks(program) -> list:
    return [b for b in program.getMemory().getBlocks() if b.isInitialized() and b.isLoaded()]


def verify(program, settings: ImportSettings, target_size: int) -> list[str]:
    """Check that Ghidra really applied the requested settings (it skips unknown loader args silently)."""
    problems = []
    fmt = str(program.getExecutableFormat())
    if fmt != settings.profile.format:
        problems.append(f"format is {fmt!r}, expected {settings.profile.format!r}")
    lang = str(program.getLanguageID())
    if settings.language and lang != settings.language:
        problems.append(f"language is {lang}, expected {settings.language}")
    if settings.profile.format == FORMAT_RAW:
        blocks = loaded_blocks(program)
        if len(blocks) != 1:
            problems.append(f"expected one loaded block, found {len(blocks)}")
        else:
            start, size = blocks[0].getStart().getOffset(), blocks[0].getSize()
            if start != settings.base:
                problems.append(f"image starts at {start:#x}, expected {settings.base:#x}")
            if size != target_size:
                problems.append(f"block size {size} differs from the file size {target_size}")
    return problems


def apply_vector_table(program, base: int) -> dict:
    """Read the Cortex-M vector table at `base`, define its slots and create the handler functions."""
    import pyghidra
    from ghidra.app.cmd.disassemble import ArmDisassembleCommand
    from ghidra.app.cmd.function import CreateFunctionCmd
    from ghidra.program.model.data import DWordDataType
    from ghidra.program.model.listing import CommentType
    from ghidra.program.model.symbol import SourceType

    mem = program.getMemory()
    space = program.getAddressFactory().getDefaultAddressSpace()
    start = space.getAddress(base)
    block = mem.getBlock(start)
    if block is None:
        raise CaseError(f"no memory at the vector table address {base:#x}")
    n = min(vectors.MAX_ENTRIES, (block.getEnd().getOffset() - base + 1) // 4)
    words = [mem.getInt(start.add(4 * i)) & 0xFFFFFFFF for i in range(n)]

    def is_code(addr: int) -> bool:
        try:
            b = mem.getBlock(space.getAddress(addr))
        except Exception:
            return False
        return b is not None and b.isExecute() and b.isInitialized()

    try:
        table = vectors.decode(words, is_code)
    except ValueError as e:
        raise CaseError(f"no valid Cortex-M vector table at {base:#x}: {e}") from None

    listing = program.getListing()
    fm = program.getFunctionManager()
    slot_names = {i: n for i, n, _ in table.entries}
    with pyghidra.transaction(program, "l2a: Cortex-M vector table"):
        program.getSymbolTable().createLabel(start, "vector_table", SourceType.ANALYSIS)
        for i in range(table.length):
            a = start.add(4 * i)
            listing.createData(a, DWordDataType.dataType)
            what = "initial SP" if i == 0 else slot_names.get(i, vectors.vector_name(i) + " (unused)")
            listing.getCodeUnitAt(a).setComment(CommentType.EOL, f"vector {i}: {what}")
        for addr, names in table.targets().items():
            a = space.getAddress(addr)
            ArmDisassembleCommand(a, None, True).applyTo(program, monitor())
            name = vectors.handler_name(names, addr)
            fn = fm.getFunctionAt(a)
            if fn is None:
                CreateFunctionCmd(name, a, None, SourceType.ANALYSIS).applyTo(program, monitor())
                fn = fm.getFunctionAt(a)
            if fn is not None:
                shown = ", ".join(names[:8]) + (f", ... ({len(names)} vectors)" if len(names) > 8 else "")
                fn.setComment(f"Cortex-M vector target: {shown}")
    reset = table.entries[0][2]
    return {"initial_sp": f"{table.initial_sp:#010x}", "slots": table.length, "handlers": len(table.targets()),
            "reset": f"{reset:#010x}"}


def analyze(program) -> None:
    import pyghidra

    pyghidra.analyze(program, monitor())
