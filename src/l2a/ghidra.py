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
from .profiles import FORMAT_RAW, ImportSettings

# Pinned tools (docs/TOOLCHAIN.md). Environment variables override the default paths.
PINNED_GHIDRA = "12.1.4"
DEFAULT_GHIDRA = r"C:\Tools\ghidra_12.1.4_PUBLIC"
DEFAULT_JDK = r"C:\Tools\jdk-21.0.12.1+1"

_env: dict | None = None


def _ghidra_version(install: Path) -> str:
    props = install / "Ghidra" / "application.properties"
    for line in props.read_text(encoding="utf-8").splitlines():
        if line.startswith("application.version="):
            return line.split("=", 1)[1].strip()
    return "unknown"


def start() -> dict:
    """Start the JVM and Ghidra once per process. Returns the tool versions in use."""
    global _env
    if _env is not None:
        return _env
    install = Path(os.environ.get("GHIDRA_INSTALL_DIR") or DEFAULT_GHIDRA)
    jdk = os.environ.get("JAVA_HOME_OVERRIDE") or (DEFAULT_JDK if Path(DEFAULT_JDK).is_dir() else os.environ.get("JAVA_HOME"))
    if not (install / "Ghidra" / "application.properties").is_file():
        raise CaseError(f"Ghidra not found at {install}; set GHIDRA_INSTALL_DIR")
    if not jdk or not Path(jdk).is_dir():
        raise CaseError("JDK 21 not found; set JAVA_HOME_OVERRIDE or JAVA_HOME")
    ghidra_version = _ghidra_version(install)
    if ghidra_version != PINNED_GHIDRA:
        print(f"[l2a] WARNING: Ghidra {ghidra_version} differs from the pinned {PINNED_GHIDRA} (docs/TOOLCHAIN.md)",
              file=sys.stderr)
    # JAVA_HOME_OVERRIDE makes PyGhidra use this JDK instead of searching for one.
    os.environ["GHIDRA_INSTALL_DIR"] = str(install)
    os.environ["JAVA_HOME_OVERRIDE"] = str(jdk)
    import pyghidra

    pyghidra.start(install_dir=install)
    from java.lang import System

    _env = {"ghidra": ghidra_version, "ghidra_dir": str(install), "java": str(System.getProperty("java.version")),
            "java_home": str(jdk), "pyghidra": pkg_version("pyghidra")}
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
            raise CaseError(f"project {case.project_file} is locked; close it in the Ghidra GUI first ({e})") from None
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
        raise CaseError(f"program {name!r} not in the project; programs: {', '.join(program_names(project)) or 'none'}")
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
        raise CaseError(f"{settings.profile.loader} could not load {target.name}: {e}") from None


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
