# REA architecture review: functions and interfaces

Subject: [morluto/rea](https://github.com/morluto/rea) at commit `4b961e3715375971aee6dec848827c9c072d947b`
(rea-agents 6.8.0, MIT), read only on 2026-11-03.
Detailed line-by-line evidence: [REA_STATIC_REVIEW_4b961e3.md](REA_STATIC_REVIEW_4b961e3.md).

Labels:

* **[F:REA]**: confirmed in REA source.
* **[F:local]**: confirmed on the owner's machine (Ghidra 12.1.4 install, files read only).
* **[A]**: assumption.
* **[O]**: open question.

## 1. What REA is

REA is a TypeScript CLI and MCP server (~234 tools, ~180 CLI commands). It sits on top of local engines: Ghidra, Hopper, IDA, JEB,
Kuna, JADX, Frida, gdb/LLDB, Rizin, Binwalk/Unblob, Playwright and others [F:REA].

Its own value lies in:

* uniform contracts
* an evidence model
* process and lifecycle hygiene
* agent instructions
* very broad target coverage (native, JS/Electron, .NET, Android, web, WASM, EVM and more)

It has no public API, plugin loader or provider interface [F:REA]. It changes very fast: 4.0 → 6.8 in 20 days [F:REA].

## 2. Interfaces

| Interface | Shape | Usable by L2A? |
| --- | --- | --- |
| MCP (stdio; optional `--http` without auth/TLS) | ~234 tools in families; `REA_MCP_TOOL_FAMILIES` restricts them; no read-only mode [F:REA] | Not in the MVP (owner rule: no MCP before review; too large a surface) |
| CLI (`incur`) | `--json`/`jsonl`/`md`, `--snapshot`; not 1:1 with MCP [F:REA] | Possible later as a subprocess, only for lanes REA supports on Windows (PE) |
| Evidence/unknowns data model | Zod schemas in `src/domain/evidence.ts`, `residualUnknown.ts` [F:REA] | **Yes, as a vocabulary** (§5) |
| Ghidra bridge | Java `HeadlessScript` + authenticated loopback socket on Windows [F:REA] | No. PyGhidra gives the same API directly |
| Agent skills | Markdown; recommends `npx -y rea-agents@latest` [F:REA] | No. L2A writes its own skills |

## 3. REA functions versus existing tool APIs

Most of REA's Ghidra lane is a thin, contract-wrapped layer over the Ghidra API. With PyGhidra, L2A can call that API directly.

| REA function [F:REA] | Direct equivalent | Label for the equivalent |
| --- | --- | --- |
| `open_binary` (fresh import, ephemeral project) | `pyghidra.open_program(...)` or `analyzeHeadless -import … -deleteProject` | [F:local] `analyzeHeadless` options; PyGhidra API [A, per its README] |
| Raw import (fixed language list, base = entry) | `BinaryLoader` with `-loader-baseAddr` and **any** `-processor`, for example `ARM:LE:32:Cortex` | [F:local] |
| List functions, names, segments | `FunctionManager`, `SymbolTable`, `Memory.getBlocks()` | [F:local] (Base/SoftwareModeling jars) |
| Strings | Ghidra defined data / string search | [A] |
| `procedure_pseudo_code` (decompile) | `DecompInterface.decompileFunction` | [F:local] class present |
| `procedure_assembly`, `read_function_instructions` | `Listing.getInstructions(body)` | [A] |
| Callers, callees, xrefs | `Function.getCalledFunctions/getCallingFunctions`, `ReferenceManager` | [A] |
| `read_bytes`, masked `search_bytes` | `Memory.getBytes`, `Memory.findBytes(…, mask, …)` | [A] |
| `inspect_native_instruction` (operand immediates) | `Instruction.getOpObjects` / `Scalar` | [A] |
| `match_native_functions` (build comparison) | Ghidra VersionTracking / BSim | [F:local] features present |
| Evidence export | L2A JSON + Ghidra Sarif export if useful | [F:local] Sarif feature present |
| Firmware container parsers (HEX, S-record, UF2, DfuSe, ESP, FIT/uImage) | `arm-none-eabi-objcopy` for HEX/S-record; others only when a case needs them | [F:repo] toolchain; [A] |
| Byte entropy | A few lines of Python | – |
| Binwalk/Unblob extraction (Linux-only in REA) | Not needed for own firmware; for vendor installers, static unpacking (for example 7-Zip) when a case requires it | [O] |
| Frida, debuggers, process capture (dynamic analysis) | Use Frida, x64dbg/WinDbg/Visual Studio and plugin hosts directly, on demand ([concept §2](L2A_Concept_v0.3.md)) | [A] |
| (not in REA) single-function emulation | Ghidra `EmulatorHelper` via PyGhidra | [F:local] class present |
| Browser/Electron/Android/.NET lanes | Use those tools directly if a case ever needs them | [A] |

**Things REA does not provide, so no API saves us from building them** [F:REA, by absence]:

* Cortex-M/Thumb raw import
* vector-table seeding
* memory maps or SVD
* constant or float search by value
* typed array reads
* instruction-mix metrics
* any DSP or audio knowledge

## 4. What L2A must build itself (minimal)

1. DSP skills (`method/`): the main deliverable.
2. `l2a open`: a small profile with loader, language and base. Cortex-M profiles also seed from the vector table with the Thumb bit.
3. `l2a query`: targeted retrieval. Output is compact by default; long results come in sections or as a file. It covers:
   * an overview with FP instruction counts
   * decompile and disassemble
   * xrefs and callers/callees
   * constants used by a function
   * typed reads and value search
4. A `case.md` template (`templates/case.md`) that serves as the case's working memory.

All of this is a small Python layer on top of PyGhidra that duplicates nothing in REA's infrastructure ([concept §3](L2A_Concept_v0.3.md)).

## 5. Selective REA adoption

| Candidate | Benefit | Decision | Conditions |
| --- | --- | --- | --- |
| Evidence vocabulary: observed / derived / inferred; open vs resolved unknowns | Direct fit for "proof vs assumption" | **Adopt the words** in the skills and the `case.md` template. No code or schema is copied | Credit REA (MIT) in a short note |
| `untrusted_content` marking of target-derived text | Prompt-injection hygiene | **Adopt the idea** | None |
| Ghidra isolation pattern (temporary project, private HOME/APPDATA/TEMP, `-readOnly`, bounded heap) | Run hygiene | **Adopt the idea** in the PyGhidra launcher | None |
| `ReaGhidraNoReturnFix.java`, `ReaGhidraPrepareRaw.java` and similar | Edge-case knowledge | **Read as reference only** | Licence check if any line is ever copied |
| Firmware container parsers (`src/domain/firmware/*`) | DfuSe/UF2/ESP parsing | **Later, only if a case needs one** | Independent security and licence review; port to Python |
| Objective-C/Swift metadata, Mach-O thinning | AU plugins on macOS | Later | Same |
| `WindowsBatchCommand.ts` metacharacter guard | Safe `.bat` calls | **Not needed**: PyGhidra avoids `.bat` | – |
| MCP server, setup, plugin launcher, shipped skills | – | **Never** | – |

## 6. Security observations relevant to L2A

* **Never run** `rea setup` (writes global agent configs) or `npx rea-agents@latest` (unpinned). Never use `mcp --http` (no auth) [F:REA].
* **No consent gate:** 16 REA tools execute foreign code, and REA itself does not gate them [F:REA].
* **Weak native-addon check:** the prebuilt Windows native addon is checked only against a manifest in the same package [F:REA].
* **Agent-directed text:** REA's `AGENTS.md` contains text addressed to AI agents (a Turborepo block) [F:REA]. All REA files stay untrusted study objects.
* **Not reviewed:** submodules, the full dependency tree, and the npm tarball versus the commit [O]. This is irrelevant as long as nothing is installed.

## 7. Conclusion

L2A is a Windows-first, DSP-focused analysis platform for many targets: Daisy/Cortex-M, ESP32 (Xtensa), VST3 PE, logue SDK
ARM ELF and others. For such a platform, REA's runtime adds little that Ghidra, PyGhidra and the standard dynamic tools don't
already provide directly. On Windows, REA would even block two of these target classes, ELF and raw ARM [F:REA].

REA's main reusable asset is its evidence discipline. L2A should stay independent:

* adopt that evidence vocabulary
* build a thin PyGhidra query layer and the DSP skills
* treat REA as a reference to consult when a new target class or format appears (Mach-O, vendor containers)
