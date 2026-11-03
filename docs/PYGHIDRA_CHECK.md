# PyGhidra check (roadmap step 3)

Run by Claude on 2026-11-03 on the owner's Windows 11 machine. All results are **MEASURED 2026-11-03**, one run each.
Target: the owner's own build `PhysicalModeling-v0.1.0` (`.bin` and `.elf`) from the Daisy-Seed project. The case files
are kept outside the repository, in `D:\L2A-cases\pyghidra-check\`.

## Results

| Check | Result | Note |
| --- | --- | --- |
| Offline install | **Pass** | `pip install --no-index --find-links C:\Tools\ghidra_12.1.4_PUBLIC\Ghidra\Features\PyGhidra\pypkg\dist pyghidra==3.1.0` into the venv `D:\L2A-cases\_toolchain\pyghidra-venv`. Installed pyghidra 3.1.0, Jpype1 1.5.2 and packaging 25.0 |
| Raw import with explicit options | **Pass, after a fix** | `ProgramLoader` with `BinaryLoader`, `ARM:LE:32:Cortex`, `-loader-baseAddr 0x24000000`. Result: one block at `0x24000000–0x24021a37` |
| Language | **Pass** | `ARM:LE:32:Cortex`, compiler `default` |
| Reset vector | **Pass** | Word at `0x24000004` = `0x24000749`, Thumb bit set. The target `0x24000748` lies in the executable block, is disassembled in Thumb mode (TMode = 1) and equals the ELF symbol `Reset_Handler` |
| ELF import | **Pass** | `ElfLoader`, 27 memory blocks, 694 functions after analysis |
| Persistence | **Pass** | A second process reopened the project with `open_project` and `program_context`. Without calling `analyze()`, both programs kept their function counts (bin 506, ELF 694) and their domain file version; `isChanged()` was false |
| Decompile from the reopened project | **Pass** | `main` at `0x240009d4` (ELF) and the same address in the raw import both decompile completely |

## Lessons for `l2a open` (step 4)

1. **Loader arguments need the `-loader-` prefix** (`-loader-baseAddr`, `-loader-blockName`). Ghidra skips unknown names
   silently, logging only a warning in `%APPDATA%\ghidra\ghidra_12.1.4_PUBLIC\application.log`. The first run used
   `-baseAddr` and imported at `0x00000000` without any error (source: `ProgramLoader.java`, lines 620–642).
   So `l2a open` must check the imported program (block start, language) and fail on a mismatch.
2. For the binary loader, `getImageBase()` stays `0x00000000`. Check the first memory block, not the image base.
3. The auto-analysis of a raw image does **not** create a function at the reset target. The Cortex-M profile has to read the
   vector table and create the entry functions itself, as the concept already plans.
4. Set `GHIDRA_INSTALL_DIR` and `JAVA_HOME` explicitly and run Python with `-I`. Otherwise PyGhidra falls back to a "lastrun" file.

## Timings

| Step | bin | ELF |
| --- | --- | --- |
| JVM and Ghidra start (per process) | 4.4–4.8 s | |
| Import | 2.6 s | 1.0 s |
| Auto-analysis (defaults) | 16.9 s | 18.5 s |
| Save | 0.1 s | 0.2 s |
| Reopen: open the project | 0.3 s | |
| Reopen: open the program | 0.03 s | 2.95 s (first program loaded in the process) |
| Reopen: decompile `main` | 0.18 s | 0.46 s |

Total time per process: 44.6 s for the import (both targets) and 9.5 s for the reopen with two decompiles.
Reopening therefore costs about the JVM start-up plus a few seconds, which confirms the "import once, query many times" design.

## Not checked

* Using the project from the Ghidra GUI and `l2a` together, including the project lock.
* Repeated timing runs. Each value comes from a single run.
* Analysis options other than the defaults.
