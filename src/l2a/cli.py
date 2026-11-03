"""Command line: `l2a open` imports and analyses a target once; `l2a query` reads the saved project.

    l2a open  <case> <target> --profile cortex-m --base 0x24000000 [--reimport]
    l2a query <case> [-p program] functions --sort size --then decompile main --max-lines 0 --out main.c
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, case as casemod, output, profiles
from .case import Case, CaseError

TEMPLATE = Path(__file__).resolve().parents[2] / "templates" / "case.md"
THEN = "--then"


def _log(msg: str) -> None:
    print(f"[l2a] {msg}", flush=True)


# --- open ----------------------------------------------------------------------------------------------------

def open_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="l2a open", description="Import a target into the case's Ghidra project and analyse it once.")
    p.add_argument("case", help="case folder (created if missing; must be outside every git checkout)")
    p.add_argument("target", help="target file; copied into <case>/target/ if it is outside the case")
    p.add_argument("--profile", required=True, choices=list(profiles.PROFILES),
                   help="; ".join(f"{n}: {pr.help}" for n, pr in profiles.PROFILES.items()))
    p.add_argument("--base", help="load address for raw images (hex), for example 0x24000000")
    p.add_argument("--language", help="Ghidra language ID, for example ARM:LE:32:Cortex")
    p.add_argument("--compiler", help="Ghidra compiler spec ID (default: 'default' when a language is given)")
    p.add_argument("--name", help="program name in the project (default: the file name)")
    p.add_argument("--reimport", action="store_true", help="import again; the old project is kept as a backup")
    return p


def _place_target(case: Case, target: Path) -> Path:
    if casemod.is_within(target, case.root):
        return target
    dest = case.target_dir / target.name
    if dest.exists():
        if casemod.sha256_file(dest) != casemod.sha256_file(target):
            raise CaseError(f"{dest} exists with different content; rename the target or remove the old copy")
        return dest
    case.target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, dest)
    _log(f"copied target to {dest}")
    return dest


def cmd_open(argv: list[str]) -> int:
    a = open_parser().parse_args(argv)
    settings = profiles.resolve(a.profile, a.language, a.compiler, a.base)
    case = Case.at(a.case)
    case.check_not_in_git()
    src = Path(a.target).resolve()
    if not src.is_file():
        raise CaseError(f"target not found: {src}")
    case.root.mkdir(parents=True, exist_ok=True)
    target = _place_target(case, src)
    sha = casemod.sha256_file(target)
    name = a.name or target.name
    records = case.load_records()
    rec = records.get(name)

    if case.project_file.exists() and rec and rec["sha256"] == sha and not a.reimport:
        _log(f"{name} is already imported (SHA-256 matches); nothing to do. Use --reimport to import again.")
        return 0
    if case.project_file.exists() and (rec or a.reimport):
        backup = case.root / f"ghidra-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        shutil.copytree(case.ghidra_dir, backup)
        reason = "--reimport" if a.reimport else "target SHA-256 changed"
        _log(f"{reason}: old project kept as {backup}")

    from . import ghidra

    t0 = time.perf_counter()
    env = ghidra.start()
    t_start = time.perf_counter() - t0
    project = ghidra.open_project(case, create=True)
    try:
        t = time.perf_counter()
        results = ghidra.load(project, target, name, settings)
        try:
            program = results.getPrimaryDomainObject()
            problems = ghidra.verify(program, settings, target.stat().st_size)
            if problems:
                raise CaseError("import does not match the requested settings, nothing saved:\n  " + "\n  ".join(problems))
            old = ghidra.domain_file(project, name)
            if old is not None:
                old.delete()
            results.save(ghidra.monitor())
            t_import = time.perf_counter() - t
            vt = None
            if settings.profile.vector_table:
                vt = ghidra.apply_vector_table(program, settings.base)
                _log(f"vector table: {vt['slots']} slots, {vt['handlers']} handler functions, reset {vt['reset']}")
            t = time.perf_counter()
            _log(f"analysing {name} (default analysis options) ...")
            ghidra.analyze(program)
            t_analyze = time.perf_counter() - t
            program.getDomainFile().save(ghidra.monitor())
            rec = {
                "target": str(target.relative_to(case.root)),
                "sha256": sha,
                "size": target.stat().st_size,
                "profile": settings.profile.name,
                "loader": settings.profile.loader,
                "format": str(program.getExecutableFormat()),
                "language": str(program.getLanguageID()),
                "compiler": str(program.getCompilerSpec().getCompilerSpecID()),
                "base": hex(settings.base) if settings.base is not None else None,
                "loader_args": [list(x) for x in settings.loader_args()],
                "analysis": "Ghidra defaults",
                "vector_table": vt,
                "function_count": program.getFunctionManager().getFunctionCount(),
                "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "timings_s": {"start": round(t_start, 2), "import": round(t_import, 2), "analyze": round(t_analyze, 2)},
                "tools": {**env, "l2a": __version__},
            }
        finally:
            results.close()
    finally:
        project.close()

    records[name] = rec
    case.save_records(records)
    text = case.case_md.read_text(encoding="utf-8") if case.case_md.exists() else casemod.initial_case_md(case.name, TEMPLATE)
    case.case_md.write_text(casemod.update_case_md(text, casemod.imports_block(records)), encoding="utf-8")
    _log(f"imported {name}: {rec['format']}, {rec['language']}, {rec['function_count']} functions; "
         f"import {rec['timings_s']['import']} s, analysis {rec['timings_s']['analyze']} s")
    _log(f"project {case.project_file}; record {case.record_file}; case.md updated")
    return 0


# --- query ---------------------------------------------------------------------------------------------------

def split_query_argv(argv: list[str]) -> tuple[str, str | None, list[list[str]]]:
    """`<case> [-p program] <query> [--then <query>] ...` -> (case, program, queries)."""
    if not argv or argv[0] in ("-h", "--help"):
        raise CaseError("usage: l2a query <case> [-p program] <command> [args] [--then <command> [args]] ...\n"
                        "commands: info, functions, decompile, disasm, xrefs, calls, consts, table, search "
                        "(`l2a query <case> <command> -h` for details)")
    case, rest, program = argv[0], argv[1:], None
    if rest[:1] and rest[0] in ("-p", "--program"):
        if len(rest) < 2:
            raise CaseError("-p needs a program name")
        program, rest = rest[1], rest[2:]
    queries, cur = [], []
    for tok in rest:
        if tok == THEN:
            queries.append(cur)
            cur = []
        else:
            cur.append(tok)
    queries.append(cur)
    if any(not q for q in queries):
        raise CaseError("empty query (check the use of --then)")
    return case, program, queries


def cmd_query(argv: list[str]) -> int:
    from . import queries as q

    case_arg, program_name, raw_queries = split_query_argv(argv)
    parser = q.build_parser()
    parsed = [parser.parse_args(x) for x in raw_queries]  # fail on bad arguments before starting Ghidra
    case = Case.at(case_arg)
    case.require_project()
    outs = [case.resolve_out(p.out, p.allow_outside) if p.out else None for p in parsed]
    records = case.load_records()

    from . import ghidra

    ghidra.start()
    project = ghidra.open_project(case, create=False)
    try:
        names = ghidra.program_names(project)
        if program_name is None:
            if len(names) != 1:
                raise CaseError(f"the project has {len(names)} programs; choose one with -p: {', '.join(names)}")
            program_name = names[0]
        rec = records.get(program_name)
        if rec:
            tpath = case.root / rec["target"]
            if tpath.is_file() and casemod.sha256_file(tpath) != rec["sha256"]:
                print(f"[l2a] WARNING: {tpath} changed since the import; run `l2a open` again", file=sys.stderr)
        with ghidra.read_program(project, program_name) as program:
            for p, out in zip(parsed, outs):
                title, lines = q.COMMANDS[p.cmd](program, p, {"record": rec})
                if out is not None:
                    print(output.write_full(out, title, lines))
                else:
                    max_lines = output.DEFAULT_MAX_LINES if p.max_lines is None else p.max_lines
                    print(output.render(title, lines, p.offset, max_lines))
    finally:
        project.close()
    return 0


# --- main ----------------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if argv[0] in ("-V", "--version"):
        print(f"l2a {__version__}")
        return 0
    commands = {"open": cmd_open, "query": cmd_query}
    if argv[0] not in commands:
        print(f"l2a: unknown command {argv[0]!r}; use open or query", file=sys.stderr)
        return 2
    try:
        return commands[argv[0]](argv[1:])
    except CaseError as e:
        print(f"l2a: error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
