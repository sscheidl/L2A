# `l2a` command line (v0.1)

`l2a open` imports a target **once** into the case's Ghidra project and analyses it. `l2a query` then reads the saved
project without re-importing or re-analysing it. Background: [concept §3](L2A_Concept_v0.3.md#3-what-gets-built-v01);
PyGhidra facts: [PYGHIDRA_CHECK.md](PYGHIDRA_CHECK.md).

## Install (offline, once)

Use the PyGhidra venv from [TOOLCHAIN.md](TOOLCHAIN.md). From the repository root:

```bash
D='C:\Tools\ghidra_12.1.4_PUBLIC\Ghidra\Features\PyGhidra\pypkg\dist'
V=/d/L2A-cases/_toolchain/pyghidra-venv/Scripts
$V/python.exe -m pip install --no-index --find-links "$D" setuptools
$V/python.exe -m pip install --no-index --no-build-isolation -e .
```

The command is then `D:\L2A-cases\_toolchain\pyghidra-venv\Scripts\l2a.exe`. `l2a` uses the pinned Ghidra and JDK
paths from TOOLCHAIN.md. `GHIDRA_INSTALL_DIR` and `JAVA_HOME_OVERRIDE` can point elsewhere, but the tool set must still
be the reviewed one. `l2a` stops before starting Ghidra in any of these cases:
* the Ghidra version is not the pinned one;
* the JDK version (from its `release` file) is not the pinned one;
* Ghidra user extensions are installed (`%APPDATA%\ghidra\ghidra_<version>_PUBLIC\Extensions`, or the same folder
  below `XDG_CONFIG_HOME`);
* Python packages register PyGhidra start-up entry points (`pyghidra.setup`, `pyghidra.pre_launch`).

For a deliberate deviation, set `L2A_ALLOW_UNPINNED=1` or `L2A_ALLOW_EXTENSIONS=1`. `l2a` then prints a warning, and
the import record notes the opt-in.

## `l2a open`

```text
l2a open <case> <target> --profile <profile> [--base ADDR] [--language ID] [--compiler ID] [--name NAME] [--reimport]
```

| Profile | Loader | Language | Notes |
| --- | --- | --- | --- |
| `cortex-m` | BinaryLoader | `ARM:LE:32:Cortex` | Raw image; needs `--base`. Reads the vector table at the base, defines its slots and creates the handler functions (`reset_handler`, `irq5_handler`, …) before the analysis |
| `cortex-m-elf` | ElfLoader | `ARM:LE:32:Cortex` | Cortex-M ELF. The generic `elf` profile picks `ARM:LE:32:v8` for such files (MEASURED 2026-11-03) |
| `elf` | ElfLoader | from the file | Generic ELF |
| `pe` | PeLoader | from the file | Windows EXE or DLL, for example a VST3 binary |
| `raw` | BinaryLoader | `--language` | Any raw image; needs `--language` and `--base` |

* The case folder is created if it is missing. It must lie outside every git checkout.
* Before writing anything, `l2a open` and `l2a query` check that `target\`, `ghidra\`, `out\`, `case.md`, the import
  record and the project file are not links or junctions, do not resolve outside the case, and contain no nested
  checkout.
* A target outside the case is copied into `<case>\target\`.
* The program name is the file name or `--name`. It may contain only letters, digits and ` ._+-()[]`, must not start
  with a dot, and has at most 128 characters.
* `case.md`, the import record and the target copy are written as new files and swapped in. An existing hard link
  therefore never receives the content.
* After loading, `l2a open` checks the result: executable format, language, and for raw images the block start and size.
  On a mismatch it stops and saves nothing. This check exists because Ghidra skips loader arguments with a wrong name
  silently.
* The project is `<case>\ghidra\<case>.gpr`, and one project can hold several programs. Import settings, SHA-256, tool
  versions and timings go into `<case>\ghidra\l2a-imports.json`. A summary table is written into `case.md`; if `case.md`
  is missing, it is first created from `templates/case.md`.
* Running `l2a open` again with an unchanged target does nothing. A new import happens with `--reimport`, or automatically
  when the target's SHA-256 has changed, for example after a rebuild at the same path. In both cases the old project is
  first copied to `<case>\ghidra-backup-<time>\`, and an older target copy to `<case>\target-backup-<time>\`.
* The vector table and the analysis run before the new program is saved. If either fails, the previous program and its
  record stay as they were.
* When replacing, the previous program is first renamed to `<name>.l2a-old-<time>`, and deleted only after the new one
  is saved. If the save fails, the old program gets its name back.
* After a failed import of a rebuilt target, the case copy is already the new file. l2a says so and names the backup;
  `l2a query` then warns that the target changed since the import.
* Limit: the record is written after the save. If the record write itself fails, the project holds the new program
  next to the old record. The backup folder allows manual recovery.
* Analysis uses Ghidra's default options.

## `l2a query`

```text
l2a query <case> [-p PROGRAM] <command> [args] [--then <command> [args]] ...
```

Several queries can be chained with `--then` in one call. That way Ghidra starts once (about 5 s) for all of them.
`-p` is needed when the project holds more than one program. The program is opened **read-only**, so queries can never
change or save the project. If the target file has changed since the import, a warning is printed.

| Command | Output |
| --- | --- |
| `info` | Format, language, memory blocks, import record |
| `functions [--sort addr\|size\|fp\|name] [--name TEXT] [--min-size N] [--no-fp]` | Entry, size in bytes, count of instructions with floating-point p-code (`fpops`), name |
| `decompile <func>` | Pseudocode |
| `disasm <target> [--count N]` | The whole function body, or N code units from an address. An instruction with a data reference that Ghidra resolved (a PC-relative literal, an address constant) ends with `; [addr] word 0x… float …`, at most two per line. The word is the 32-bit word at that address, whatever the access width; the float reading is a hint |
| `xrefs <target> [--from]` | References to an address or function, or from a function's body. `xrefs <literal address>` lists every instruction that loads a literal |
| `calls <func>` | Callers and callees |
| `consts <func> [--all] [--uses]` | Data constants the function references (value, float32 reading, label), then scalars. Each line names the first user and a count; `--uses` lists every user. Small scalars (abs ≤ 16) are hidden unless `--all` is given. Only references and scalar operands that Ghidra found are listed |
| `table <addr> [--type T] [--count N] [--stride B]` | Typed read: `float32`, `float64`, `int8`–`uint32`, `q15`, `q31` |
| `search --float V [--tol T] \| --double V \| --int32 V \| --int16 V \| --bytes HEX \| --string S [--limit N] [--unaligned]` | Hits in loaded memory, with the referencing functions |

`<func>` and `<target>` take a symbol name or an address. Addresses are hexadecimal. `0x…` is always read as an address;
a bare hex string is used only when no symbol has that name.

**Output.**
* Every query prints at most 60 lines by default. `--max-lines N` changes the limit and `0` means everything;
  `--offset N` fetches the next section, and every shortened answer says how.
* Target-derived text is enclosed between `--- BEGIN TARGET DATA (untrusted …) ---` and `--- END TARGET DATA ---`.
  **Every data line starts with `| `.** Control characters, line separators and terminal escapes are shown as `\xNN` or
  `\uNNNN`. A marker inside the target text therefore always appears as `| --- END …` and never ends the block. It is
  data, never instructions (AGENTS.md).
* Names in error messages are JSON-quoted, and names in the `case.md` table are escaped.
* `--out FILE` writes the complete result to a file with the same framing, and prints only a one-line summary.
  * Relative paths go to `<case>\out\`.
  * Inside the case, only `<case>\out\` is allowed. The project, record, targets and `case.md` can never be
    overwritten, not even with `--allow-outside`.
  * Paths outside the case folder, or inside a git checkout, need `--allow-outside`.
  * The file is written new and swapped in, so a hard link never receives the content.
  * The path is checked again right before writing. This narrows a race with a concurrent change of the folder,
    but does not rule it out.

Example:

```text
l2a query D:\L2A-cases\pm -p PhysicalModeling-v0.1.0.bin functions --sort fp --max-lines 10 --then decompile 0x24001624 --out dsp.c --then search --float 48000
```

## Tests

* `python -m unittest discover -s tests` runs the unit tests without Ghidra, in under a second. The Quick CI runs them too.
* The Ghidra integration test needs `L2A_GHIDRA_IT=1` and the venv Python. It takes about a minute and uses our own Daisy
  build. Paths can be set with `L2A_IT_BIN` and `L2A_IT_ELF`; see `tests/test_integration_ghidra.py`.

## Limits of v0.1

* There is no write access: renames and comments are made in the Ghidra GUI. The GUI and `l2a` must not have the project
  open at the same time; a locked project gives a clear error.
* There is a vector-table reader for raw Cortex-M images only. Other profiles rely on Ghidra's own analysis.
* The analysis options cannot be set yet.
