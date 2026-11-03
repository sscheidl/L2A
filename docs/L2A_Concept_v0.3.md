# L2A – Listen to Anything: concept v0.3

Status: **concept, not approved for implementation** (revision 2, 2026-11-03). This is a private hobby project, so the
concept stays deliberately small. It supersedes [SPEC_v0.2.md](SPEC_v0.2.md).

Labels: **[F]** fact checked in source or files (REA at `4b961e3`, the owner's machine, the owner's repos, or a cited web page),
**[A]** assumption, **[O]** open. Nothing has been run yet, so all Ghidra capabilities on this machine are **NOT MEASURED**.

## 1. Decisions

1. **Broad analysis platform.** Examples: Daisy Seed3, AMYboard, VST3 plugins, Korg logue SDK units, and other synthesiser and
   effects firmware. There is no restriction to ARM or Daisy.
2. **Analysis only.** L2A builds no synthesisers, effects or firmware; implementations happen in other projects.
3. **Static and dynamic analysis**, including on original vendor files, with dynamic work done when needed.
4. **Detailed DSP analysis** is the core function, through targeted retrieval of pseudocode, disassembly, constants and
   function relations. No mandatory full exports.
5. **Pragmatic security.** No OS sandbox. The rules in §5 apply, plus an independent Codex review.
6. **Simple Rings/Torus test.** Original sources are not consulted, and every finding rests on concrete binary evidence.
7. **Resource efficiency.** Spend tokens, CI and tests deliberately (§6).
8. **Freedom of method.** The assistant chooses tools and approach. Extensions and plan changes are possible after consultation.

Still valid from before:

* REA is a reference only: no installation and no upstream sync.
* Windows 11 is the platform.
* Binaries and Ghidra projects stay local. Pseudocode and analysis notes may go to Claude or Codex.
* Nothing proprietary goes into this public repo.
* Roles: Claude Code develops and analyses, Codex reviews, GPT coordinates. L2A stays agent-independent.
* The Audio Lab comes later.

## 2. Architecture

**L2A = PyGhidra + a small query CLI + DSP skills (Markdown) + one folder per case.** All other tools are used directly.

What is already on the machine [F]:

* **Ghidra and Java.** Ghidra 12.1.4 is at `C:\Tools\ghidra_12.1.4_PUBLIC` and needs Java 21. JDK 21.0.12 is at `C:\Tools\jdk-21.0.12.1+1`.
* **PyGhidra.** PyGhidra 3.1.0 and the JPype wheels for Python 3.12/Windows ship *inside* the Ghidra folder, so they install offline. Python 3.12.10 is installed.
* **Loaders and languages.** The binary, ELF and PE loaders are available. Any processor language can be selected, for example `ARM:LE:32:Cortex`.
* **Processor modules.** ARM, AARCH64, x86, Xtensa, RISCV and others are present. **No SHARC, DSP56300 or TI C6000.**
* **Built-in features.** Decompiler, FunctionID, BSim, VersionTracking and the emulator (`EmulatorHelper`) are included.

Why PyGhidra:

* It gives direct access to the Ghidra API from Python. No Java bridge and no `.bat` calls are needed; with arguments, `.bat` calls are a Windows injection risk that REA has to guard against [F].
* L2A simply passes loader, language and base address through. Anything Ghidra can open, L2A can open.
* REA, by contrast, refuses ELF and raw ARM on Windows [F].

```
D:\L2A-cases\<case>\      case.md, target files, ghidra\, notes   (local, never in git)
      ▲
  l2a open | query   (Python + PyGhidra)          method\*.md   (DSP skills, read by any agent)
      ▼
  Ghidra 12.1.4 + JDK 21      + any other tool when useful (binutils, debugger, plugin host, Python scripts)
```

* **Queries are targeted**: one function, one address range, one table. Several requests can go into one call, which saves Ghidra start-up time.
* **Agent independence** comes from plain files: `AGENTS.md`, `method/` and the case folder.

### Target platforms (examples)

| Platform | Binary | Ghidra route |
| --- | --- | --- |
| Daisy Seed3 (Cortex-M7) | ELF or raw `.bin`, loaded at `0x24000000` [F] | ELF or binary loader with `ARM:LE:32:Cortex` |
| AMYboard | ESP32-S3 firmware [F: [Sonicstate](https://www.sonicstate.com/news/2026/05/21/amyboard-a-2990-programmable-eurorack-module/)] | Xtensa module; quality [O] |
| VST3 (Windows) | PE x86-64 DLL [A] | PE loader |
| Korg drumlogue | `.drmlgunit` = stripped ARM ELF shared object [F] | ELF loader |
| Other logue SDK units (prologue, minilogue xd, NTS-1) | Cortex-M4 unit packages [A] | Unpack, then the Cortex language |
| SHARC, DSP56300, C6000, FV-1 | – | No Ghidra module [F]; handled case by case [O] |

### Dynamic analysis (when needed)

L2A has no framework for this; existing tools are used directly:

* **Ghidra emulator** for running a single DSP function.
* **Plugin host, debugger or Frida** for VST3. JUCE 9.0.4 is in Daisy-Seed's `.tools` [F]; the other tools are [A].
* **Hardware** only by the owner, or with the owner's OK.

## 3. What gets built (v0.1)

| # | Part | Notes |
| --- | --- | --- |
| 1 | **DSP skills** in `method/` | The main work (§4) |
| 2 | **`l2a open`** | Opens or imports a target with a small profile (loader, language, base address). Cortex-M profiles also read the vector table |
| 3 | **`l2a query`** | Overview of functions with size and FP instruction count; decompile; disassemble; xrefs; callers and callees; constants of a function; typed table read (float32 / int16 / Q15 / Q31); value search. Output is bounded; target text is marked untrusted |
| 4 | **Case template** `case.md` | Target and hash, source, licence and legal note, tool versions, findings table, open questions |

That is all. Library recognition, version comparison, emulation, debugging and the other heavy lifting are Ghidra and the existing tools.
More is added only when a real case needs it, for example a table classifier, an MCP wrapper, unpackers, more profiles or the Audio Lab.

## 4. DSP skills

These are the project's own text (nothing copied from REA): guidance, not mandatory procedure.

1. **Workflow.**
   * Every finding cites binary evidence (address, function, instruction or constant).
   * Findings are graded *observed*, *derived* or *inferred*; this vocabulary comes from REA [F].
   * Known public designs may suggest hypotheses but never replace evidence.
   * Note what was not checked.
2. **Finding the audio path.**
   * Cortex-M: vector table, then SAI/DMA interrupt, then the callback.
   * VST3: `GetPluginFactory`, then the processor, then `process()`.
   * logue SDK: the unit render entry.
   * ESP32: the I2S task.
3. **DSP building blocks.**
   * filters (one-pole, biquad, SVF)
   * delays, comb, allpass, interpolation
   * oscillators, LFOs, tables
   * envelopes, saturation, fast math
   * fixed point, SIMD
4. **Constants.**
   * sample-rate and musical constants
   * dB and exponential mappings
   * delay-length patterns (reverb fingerprints)
5. **Reverb and delay structures.**
   * diffusers, tanks, FDN
   * modulation, damping, feedback
6. **Parameter paths.** Knob, MIDI or plugin parameter, then smoothing and mapping, then the DSP value.
7. **Verification.** Recompute offline; use the emulator or dynamic observation if useful.

## 5. Security (pragmatic)

* **Public repo.** No binaries, firmware, plugins, decompiler output, Ghidra projects or case results. Cases live in
  `D:\L2A-cases\`. `.gitignore` and a tiny check back this up.
* **Pinned tools.** Record the hashes of Ghidra and the JDK once and compare them with the official downloads. Where the
  current `C:\Tools` installs came from is not recorded yet [O]. Install PyGhidra offline. No silent updates.
* **Target text is data.** Strings and decompiler output can contain injected instructions. REA files are study objects only:
  never installed, no MCP.
* **Dynamic runs** only with official vendor files, as a normal user without admin rights, noted in the case. Ghidra extensions or
  scripts from third parties only after a quick look.
* **Third-party targets.** The owner notes the legal basis and licence terms in `case.md` first. This is not legal advice.
* **Codex reviews** L2A code before merges.

## 6. Resource efficiency

* **Tokens.** Use targeted queries, bounded output and short case notes; no dumps into the context.
* **CI.** L2A has no GitHub Actions. If one is added, it runs quick unit tests only, never Ghidra.
* **Tests.** For a small change, run the affected tests. Before important merges, milestones and releases, run everything,
  including Ghidra integration. Sanitizers only matter if native code is ever added.
* **Depth.** The assistant decides how deep to go and notes significant omissions.

## 7. Tests

1. **Infrastructure test.**
   * PyGhidra installs offline.
   * `PhysicalModeling-v0.1.0.elf` and `.bin` import (base `0x24000000`, entry `0x24000749`) [F].
   * One function decompiles.
   * Start-up time is measured.
   * Bonus: one drumlogue unit [F].
2. **Rings/Torus with Cloud Reverb.**
   * The image `physical-modeling-fx-ambient` is built once in the Daisy-Seed project; it does not exist yet [F].
   * The analysis uses only the `.bin`, without the sources, build map or symbols. Every finding cites binary evidence.
   * Afterwards, compare with the source: correct, partly correct, wrong, or missed. The Cloud Reverb is the most interesting part,
     because there is no public reference for it.
3. **Optional: Source Audio Ventris/Nemesis.**
   * Firmware comes through the Neuro Desktop app
     [F: [bonedo.de](https://www.bonedo.de/artikel/neue-firmware-fuer-das-source-audio-ventris-dual-reverb-pedal),
     [Source Audio](https://www.sourceaudio.net/blog-navigating-the-neuro-desktop-with-the-ventris-dual-reverb.html)].
   * The CPU and the format are unknown [O].
   * Order: legal note, then a feasibility check, then analysis.

## 8. Not part of L2A

* developing instruments, effects, firmware or reimplementations
* installing REA or activating any MCP server
* a sandbox framework, a GUI, or automatic algorithm recognition

## 9. Review answers in short

1. **Lean enough?** Yes: four small parts, with the skills as the main work.
2. **REA functions via existing APIs?** Almost all of REA's Ghidra operations are plain Ghidra API calls ([review §3](REA_Architecture_Review.md)).
3. **What to build ourselves?** Skills, `open`, `query` and the case template.
4. **Take over REA code?** No. Only its evidence vocabulary.
5. **Overlooked risks?**
   * Tool provenance
   * Auto-loaded Ghidra scripts
   * Prior knowledge replacing evidence
   * Third-party code in dynamic runs
   * DSP chips without a Ghidra module
6. **Ghidra on Windows?** Very likely fine; everything is installed. NOT MEASURED until the infrastructure test.
7. **Indispensable DSP capabilities?** The seven skills and the targeted queries.
8. **Rings/Torus test suitable?** Yes, in the simple form above.
