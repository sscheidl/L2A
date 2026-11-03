"""`l2a query` commands. Each takes a read-only program and parsed arguments and returns (title, lines).

Everything in the returned lines may be target-derived text; the CLI wraps it in untrusted-data markers.
"""

from __future__ import annotations

import argparse
import re

from . import values
from .case import CaseError
from .ghidra import loaded_blocks, monitor
from .profiles import parse_addr

HEX = re.compile(r"^(0x)?[0-9a-fA-F]+$")


# --- helpers -------------------------------------------------------------------------------------------------

def _space(program):
    return program.getAddressFactory().getDefaultAddressSpace()


def resolve_address(program, spec: str):
    """`0x...` is always an address; otherwise a symbol name, falling back to bare hex."""
    if not spec.lower().startswith("0x"):
        syms = list(program.getSymbolTable().getSymbols(spec))
        addrs = sorted({str(s.getAddress()) for s in syms})
        if len(addrs) == 1:
            return syms[0].getAddress()
        if len(addrs) > 1:
            raise CaseError(f"symbol {spec!r} is ambiguous: {', '.join(addrs[:10])}; give the address")
        if not HEX.match(spec):
            raise CaseError(f"no symbol named {spec!r}")
    try:
        return _space(program).getAddress(parse_addr(spec))
    except CaseError:
        raise
    except Exception as e:
        raise CaseError(f"bad address {spec!r}: {e}") from None


def resolve_function(program, spec: str):
    addr = resolve_address(program, spec)
    fn = program.getFunctionManager().getFunctionContaining(addr)
    if fn is None:
        raise CaseError(f"no function contains {addr}")
    return fn


def read_bytes(program, addr, length: int) -> bytes:
    import jpype

    arr = jpype.JArray(jpype.JByte)(length)
    n = program.getMemory().getBytes(addr, arr)
    return bytes(memoryview(arr))[:n]


def _where(program, addr) -> str:
    fn = program.getFunctionManager().getFunctionContaining(addr)
    if fn is not None:
        return f"in {fn.getName()}"
    sym = program.getSymbolTable().getPrimarySymbol(addr)
    return f"at {sym.getName()}" if sym is not None else ""


def _float_opcodes() -> frozenset[int]:
    from ghidra.program.model.pcode import PcodeOp

    return frozenset(i for i in range(PcodeOp.PCODE_MAX) if str(PcodeOp.getMnemonic(i)).startswith("FLOAT_"))


# --- commands ------------------------------------------------------------------------------------------------

def q_info(program, args, ctx):
    lang = program.getLanguage()
    lines = [
        f"program:   {program.getName()}",
        f"format:    {program.getExecutableFormat()}",
        f"language:  {program.getLanguageID()} ({'big' if lang.isBigEndian() else 'little'} endian), "
        f"compiler {program.getCompilerSpec().getCompilerSpecID()}",
        f"functions: {program.getFunctionManager().getFunctionCount()}",
        "blocks:",
    ]
    for b in program.getMemory().getBlocks():
        flags = ("r" if b.isRead() else "-") + ("w" if b.isWrite() else "-") + ("x" if b.isExecute() else "-")
        lines.append(f"  {str(b.getStart()):>24}-{str(b.getEnd()):<10} {b.getSize():>10}  {flags} "
                     f"{'init' if b.isInitialized() else 'uninit'}  {b.getName()}")
    rec = ctx.get("record")
    if rec:
        lines.append(f"import:    profile {rec['profile']}, base {rec.get('base') or '-'}, sha256 {rec['sha256']}, "
                     f"imported {rec['imported_at']}")
    return "info", lines


def q_functions(program, args, ctx):
    fp_ops = _float_opcodes()
    listing = program.getListing()
    rows = []
    for fn in program.getFunctionManager().getFunctions(True):
        name = str(fn.getName())
        if args.name and args.name.lower() not in name.lower():
            continue
        body = fn.getBody()
        size = int(body.getNumAddresses())
        if size < args.min_size:
            continue
        fp = 0
        if not args.no_fp:
            for insn in listing.getInstructions(body, True):
                if any(op.getOpcode() in fp_ops for op in insn.getPcode()):
                    fp += 1
        rows.append((fn.getEntryPoint().getOffset(), str(fn.getEntryPoint()), size, fp, name))
    key = {"addr": lambda r: r[0], "size": lambda r: -r[2], "fp": lambda r: (-r[3], -r[2]), "name": lambda r: r[4]}
    rows.sort(key=key[args.sort])
    lines = [f"{'entry':>10} {'bytes':>7} {'fpops':>6}  name"]
    lines += [f"{e:>10} {s:>7} {'-' if args.no_fp else f:>6}  {n}" for _, e, s, f, n in rows]
    return f"functions: {len(rows)} (sorted by {args.sort}; fpops = instructions with floating-point p-code)", lines


def q_decompile(program, args, ctx):
    from ghidra.app.decompiler import DecompInterface

    fn = resolve_function(program, args.target)
    ifc = DecompInterface()
    try:
        ifc.openProgram(program)
        res = ifc.decompileFunction(fn, args.timeout, monitor())
        if not res.decompileCompleted():
            raise CaseError(f"decompile of {fn.getEntryPoint()} failed: {res.getErrorMessage()}")
        c = str(res.getDecompiledFunction().getC())
    finally:
        ifc.dispose()
    return f"decompile {fn.getEntryPoint()}", c.strip("\n").splitlines()


def _unit_line(program, cu) -> list[str]:
    out = []
    sym = program.getSymbolTable().getPrimarySymbol(cu.getMinAddress())
    if sym is not None and not sym.isDynamic():
        out.append(f"{sym.getName()}:")
    raw = " ".join(f"{b & 0xFF:02x}" for b in cu.getBytes())
    out.append(f"  {cu.getMinAddress()}  {raw:<17} {cu}")
    return out


def q_disasm(program, args, ctx):
    listing = program.getListing()
    addr = resolve_address(program, args.target)
    fn = program.getFunctionManager().getFunctionContaining(addr)
    lines = []
    if fn is not None and not args.count:
        for cu in listing.getCodeUnits(fn.getBody(), True):
            lines += _unit_line(program, cu)
        return f"disasm {fn.getEntryPoint()} (function body)", lines
    it = listing.getCodeUnits(addr, True)
    for _ in range(args.count or 40):
        if not it.hasNext():
            break
        lines += _unit_line(program, it.next())
    return f"disasm {addr} ({args.count or 40} code units)", lines


def q_xrefs(program, args, ctx):
    rm = program.getReferenceManager()
    lines = []
    if args.from_:
        fn = resolve_function(program, args.target)
        for src in rm.getReferenceSourceIterator(fn.getBody(), True):
            for ref in rm.getReferencesFrom(src):
                to = ref.getToAddress()
                lines.append(f"{src} -> {to}  {ref.getReferenceType()}  {_where(program, to)}".rstrip())
        return f"xrefs from {fn.getEntryPoint()}", lines
    addr = resolve_address(program, args.target)
    for ref in rm.getReferencesTo(addr):
        src = ref.getFromAddress()
        lines.append(f"{src} -> {addr}  {ref.getReferenceType()}  {_where(program, src)}".rstrip())
    return f"xrefs to {addr}: {len(lines)}", lines


def q_calls(program, args, ctx):
    fn = resolve_function(program, args.target)
    callers = sorted(fn.getCallingFunctions(monitor()), key=lambda f: f.getEntryPoint().getOffset())
    callees = sorted(fn.getCalledFunctions(monitor()), key=lambda f: f.getEntryPoint().getOffset())
    lines = [f"callers ({len(callers)}):"] + [f"  {f.getEntryPoint()}  {f.getName()}" for f in callers]
    lines += [f"callees ({len(callees)}):"] + [f"  {f.getEntryPoint()}  {f.getName()}" for f in callees]
    return f"calls of {fn.getEntryPoint()}", lines


def q_consts(program, args, ctx):
    from ghidra.program.model.scalar import Scalar

    fn = resolve_function(program, args.target)
    mem = program.getMemory()
    found: dict[tuple, list] = {}
    for insn in program.getListing().getInstructions(fn.getBody(), True):
        ref_targets = set()
        for ref in insn.getReferencesFrom():
            to = ref.getToAddress()
            if not ref.getReferenceType().isData() or not to.isMemoryAddress():
                continue
            ref_targets.add(to.getOffset())
            block = mem.getBlock(to)
            if block is None or not block.isInitialized():
                where = "unmapped" if block is None else f"uninitialized ({block.getName()})"
                found.setdefault(("ram", str(to), where), []).append(insn.getAddress())
                continue
            raw = read_bytes(program, to, 4)
            w = values.read_word(raw, program.getLanguage().isBigEndian()) if len(raw) == 4 else 0
            hint = values.float_bits_hint(w)
            sym = program.getSymbolTable().getPrimarySymbol(to)
            desc = f"word {w:#010x}" + (f" float {hint}" if hint else "") + (f"  [{sym.getName()}]" if sym else "")
            found.setdefault(("data", str(to), desc), []).append(insn.getAddress())
        for i in range(insn.getNumOperands()):
            for obj in insn.getOpObjects(i):
                if not isinstance(obj, Scalar):
                    continue
                v = int(obj.getSignedValue())
                if (v & 0xFFFFFFFF) in ref_targets or (not args.all and -16 <= v <= 16):
                    continue
                hint = values.float_bits_hint(v) if abs(v) > 0xFFFF else ""
                found.setdefault(("scalar", f"{v & 0xFFFFFFFF:#x}", f"{v}" + (f" float {hint}" if hint else "")),
                                 []).append(insn.getAddress())
    order = {"data": 0, "scalar": 1, "ram": 2}  # values first; addresses without contents last
    lines = []
    for (kind, key, desc), where in sorted(found.items(), key=lambda kv: (order[kv[0][0]], kv[0][1])):
        more = f" (x{len(where)})" if len(where) > 1 else ""
        lines.append(f"{kind:<6} {key:>12}  {desc}  @{where[0]}{more}")
    return f"constants of {fn.getEntryPoint()}: {len(lines)} (scalars |v|<=16 hidden unless --all)", lines


def q_table(program, args, ctx):
    addr = resolve_address(program, args.target)
    _, size, _ = values.type_info(args.type)
    stride = args.stride or size
    data = read_bytes(program, addr, stride * (args.count - 1) + size)
    vals = values.decode(data, args.type, program.getLanguage().isBigEndian(), stride)
    lines = [f"{addr.add(i * stride)}  [{i:>4}]  {v}" for i, v in enumerate(vals)]
    if len(vals) < args.count:
        lines.append(f"(only {len(vals)} of {args.count} values readable)")
    return f"table {addr} {args.type} x{args.count}", lines


def q_search(program, args, ctx):
    big = program.getLanguage().isBigEndian()
    rm = program.getReferenceManager()
    hits = []
    for block in loaded_blocks(program):
        data = read_bytes(program, block.getStart(), int(block.getSize()))
        start = block.getStart()
        if args.float is not None and args.tol:
            offs = values.find_floats(data, float(args.float), args.tol, start.getOffset() % 4, big)
        else:
            kind, text = next((k, v) for k, v in (("float", args.float), ("double", args.double), ("int32", args.int32),
                                                  ("int16", args.int16), ("bytes", args.bytes), ("string", args.string))
                              if v is not None)
            needle = values.pattern(kind, text, big)
            align = 1 if args.unaligned or kind in ("bytes", "string") else min(len(needle), 4)
            offs = [o for o in values.find_all(data, needle) if (start.getOffset() + o) % align == 0]
        for off in offs:
            hits.append(start.add(off))
            if len(hits) >= args.limit:
                break
        if len(hits) >= args.limit:
            break
    lines = []
    for a in hits:
        refs = [r.getFromAddress() for r in rm.getReferencesTo(a)]
        users = sorted({str(f.getName()) for f in (program.getFunctionManager().getFunctionContaining(r) for r in refs)
                        if f is not None})
        where = _where(program, a)
        lines.append(f"{a}  {where + '  ' if where else ''}refs {len(refs)}" + (f" from {', '.join(users[:3])}" if users else ""))
    more = f" (stopped at --limit {args.limit})" if len(hits) >= args.limit else ""
    return f"search: {len(hits)} hits{more}", lines


COMMANDS = {
    "info": q_info, "functions": q_functions, "decompile": q_decompile, "disasm": q_disasm, "xrefs": q_xrefs,
    "calls": q_calls, "consts": q_consts, "table": q_table, "search": q_search,
}


def build_parser() -> argparse.ArgumentParser:
    """Parser for one query (the part after the case and program, or after `--then`)."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--max-lines", type=int, default=None, help="lines to show (default 60; 0 = all)")
    common.add_argument("--offset", type=int, default=0, help="first line to show (for the next section)")
    common.add_argument("--out", help="write the complete result to this file (relative: <case>/out/)")
    common.add_argument("--allow-outside", action="store_true", help="allow --out outside the case folder")

    p = argparse.ArgumentParser(prog="l2a query <case> [-p program]", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info", parents=[common], help="program, language, memory blocks, import record")
    s = sub.add_parser("functions", parents=[common], help="function list with size and floating-point count")
    s.add_argument("--sort", choices=["addr", "size", "fp", "name"], default="addr")
    s.add_argument("--name", help="only names containing this text")
    s.add_argument("--min-size", type=int, default=0)
    s.add_argument("--no-fp", action="store_true", help="skip the floating-point count (faster)")
    s = sub.add_parser("decompile", parents=[common], help="pseudocode of one function")
    s.add_argument("target", help="function name or address")
    s.add_argument("--timeout", type=int, default=60)
    s = sub.add_parser("disasm", parents=[common], help="disassembly of a function, or N code units from an address")
    s.add_argument("target")
    s.add_argument("--count", type=int, default=0, help="code units from the address instead of the function body")
    s = sub.add_parser("xrefs", parents=[common], help="references to an address, or from a function (--from)")
    s.add_argument("target")
    s.add_argument("--from", dest="from_", action="store_true")
    s = sub.add_parser("calls", parents=[common], help="callers and callees of a function")
    s.add_argument("target")
    s = sub.add_parser("consts", parents=[common], help="scalars and referenced data constants of a function")
    s.add_argument("target")
    s.add_argument("--all", action="store_true", help="include small scalars (|v| <= 16)")
    s = sub.add_parser("table", parents=[common], help="typed table read")
    s.add_argument("target")
    s.add_argument("--type", default="float32", choices=sorted(values.TYPES))
    s.add_argument("--count", type=int, default=16)
    s.add_argument("--stride", type=int, default=0, help="bytes between values (default: type size)")
    s = sub.add_parser("search", parents=[common], help="value search in loaded memory")
    g = s.add_mutually_exclusive_group(required=True)
    for k in ("float", "double", "int32", "int16", "bytes", "string"):
        g.add_argument(f"--{k}")
    s.add_argument("--tol", type=float, default=0.0, help="tolerance for --float (scans aligned float32 words)")
    s.add_argument("--unaligned", action="store_true")
    s.add_argument("--limit", type=int, default=50)
    return p
