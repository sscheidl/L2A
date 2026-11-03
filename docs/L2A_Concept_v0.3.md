# L2A – Listen to Anything: consolidated concept v0.3

Status: **concept, not approved for implementation** (2026-11-03)
Supersedes: [SPEC_v0.2.md](SPEC_v0.2.md) and the v0.1 concept. It incorporates the owner decisions of 2026-11-03.
Author: Claude (architecture review). The owner decides scope and approvals.

## Evidence labels

| Label | Meaning |
| --- | --- |
| **[F:REA]** | Fact confirmed in the REA source at commit `4b961e3` ([review](REA_Architecture_Review.md)) |
| **[F:local]** | Fact confirmed by reading files on the owner's Windows 11 machine on 2026-11-03 (nothing executed) |
| **[F:repo]** | Fact confirmed in the Daisy-Seed repository |
| **[F:web]** | Fact from a public web source (cited) |
| **[A]** | Plausible assumption, not verified |
| **[O]** | Open question: needs a decision or a measurement |

No tool has been run. Every capability statement about Ghidra on this machine is **NOT MEASURED**.

## 1. Owner decisions (binding input)

* L2A does universal reverse engineering, specialised in music software, synthesisers, effects, DSP and firmware.
  Existing capabilities must not be restricted unnecessarily.
* REA is a **technical reference**, not a dependency. L2A studies its architecture, prefers existing tools' own APIs,
  and adopts REA parts selectively only with a proven benefit and after an independent security and licence check.
  There is no upstream synchronisation.
* Start with solid DSP skills and analysis methods. Build tools only when their benefit is proven.
* Tests:
  1. A short infrastructure test.
  2. The main test: Daisy Rings/Torus with Cloud Reverb, analysed from compiled firmware first, then compared with the source.
  3. Optionally, Source Audio Ventris and Nemesis.
* The Audio Lab comes later; the MVP has no audio measurement.
* Platform: **Windows 11**.
* Original firmware, binaries and Ghidra projects stay local. Pseudocode, disassembly, extracted DSP routines and
  analysis information **may** be sent to Claude or Codex.
* Roles:
  * **Claude Code** is the main developer and primary analyst.
  * **Codex** does the independent security and code review, and acts as backup.
  * **GPT** coordinates.
* L2A stays agent-independent.

## 2. Architecture correction

### 2.1 The simpler solution

v0.2 planned Ghidra headless scripts started through `analyzeHeadless`. There is a simpler and safer route:

**L2A = PyGhidra + a thin Python CLI + agent-neutral DSP skills + a file-based case format.**

| Fact | Label |
| --- | --- |
| Ghidra 12.1.4 is installed at `C:\Tools\ghidra_12.1.4_PUBLIC`, with JDK 21.0.12 at `C:\Tools\jdk-21.0.12.1+1` | [F:local] |
| Ghidra 12.1.4 requires Java ≥ 21 (`application.java.min=21`) | [F:local] |
| The Ghidra distribution ships **PyGhidra 3.1.0 and JPype 1.5.2 wheels, including `cp312-win_amd64`**. CPython 3.12.10 is installed | [F:local] |
| `analyzeHeadless` supports `-processor`, `-loader BinaryLoader -loader-baseAddr`, `-readOnly`, `-deleteProject` and `-max-cpu` | [F:local] |
| The language `ARM:LE:32:Cortex` exists (`ARM.ldefs`, `ARMCortex.pspec`) | [F:local] |
| Processor modules include ARM, AARCH64, x86, Xtensa, RISCV, MIPS, PowerPC, TI_MSP430 and more. There is **no SHARC, DSP56300 or TI C6000** module | [F:local] |
| Features include Decompiler, FunctionID, BSim, VersionTracking, SystemEmulation (`EmulatorHelper`), Sarif and the GNU/Microsoft/Swift demanglers | [F:local] |

Why PyGhidra instead of headless scripts or REA:

1. **The API is used directly in CPython** (`DecompInterface`, `FlatProgramAPI`, `FunctionManager`,
   `ReferenceManager`, `Memory` and so on), so L2A needs no Java bridge, no socket and no token protocol.
   REA needs all of these [F:REA].
2. **No `.bat` invocation.** Starting `analyzeHeadless.bat` from a program with arguments goes through cmd.exe parsing.
   That is a known argument-injection risk class on Windows, and REA has to guard against it
   (`WindowsBatchCommand.ts`) [F:REA]. PyGhidra starts the JVM in-process [A, documented in its README].
3. **Offline installation.** The wheels come from the Ghidra distribution itself, so no PyPI access is needed [F:local].
4. **Universal by pass-through.** L2A does not gate formats or architectures. It passes loader, language and
   base address to Ghidra, so everything Ghidra can open, L2A can open. REA, by contrast, refuses raw Cortex-M and,
   on Windows, ELF [F:REA].

### 2.2 Component view

```
D:\L2A-cases\<case>\          (local only; never in git)
  case.json  target.bin  ghidra\  exports\  findings\  notes\
        ▲
        │  l2a CLI (Python, stdlib + PyGhidra)       method\  (agent-neutral DSP skills, Markdown)
        │  case init | import | export | query        read by Claude Code and Codex via AGENTS.md
        ▼
  PyGhidra 3.1.0 ──► Ghidra 12.1.4 + JDK 21  (C:\Tools, pinned, hash-recorded)
```

* **Agents call the CLI and read files.** Claude Code and Codex both run shell commands and read JSON/Markdown,
  so neither needs an MCP server [A]. A thin MCP wrapper over the same functions is a later option (§7).
* **Agent independence comes from files:** `AGENTS.md` (canonical; `CLAUDE.md` only includes it), `method/*.md`, and the case
  directory. A case can be continued by the other agent from the files alone.
* **Other tool chains are used directly, not wrapped:** GNU binutils from the pinned Daisy toolchain
  (`arm-none-eabi-objdump/readelf/nm/objcopy`) [F:repo], and later, for example, ILSpy, jadx or Frida for non-DSP targets.
  L2A records their use in the case. It does not rebuild REA's breadth.

## 3. Scope of the MVP (v0.1)

### 3.1 What L2A builds itself

| # | Component | Size | Why it is needed |
| --- | --- | --- | --- |
| 1 | **DSP skills** (`method/`) | Main effort | The owner's priority. It is the part REA and Ghidra do not have [F:REA: no DSP code] |
| 2 | **Case format** (`case.json` + folder layout) | Small | Reproducibility, provenance and agent hand-over |
| 3 | **Findings/unknowns schema** + Markdown render | Small | Separates proof from assumption, using REA's vocabulary [F:REA] |
| 4 | **`l2a import`**: profile-based import (loader, language, base address, extra memory regions; Cortex-M vector-table seeding with the Thumb bit) | Small | Ghidra imports a raw binary but does not interpret the Cortex-M vector table [A] |
| 5 | **`l2a export`**: JSON of functions, decompiler text, call edges, xrefs, strings (tagged `untrusted`), and **per-function FP/DSP instruction counts** | Small/medium | One deterministic file per analysis run. Agents work from it instead of a GUI |
| 6 | **`l2a query`**: decompile a function, xrefs to/from, **typed read** (float32/int16/Q15/Q31/uint16 array at an address) | Small | The interactive part, for drilling down during analysis |
| 7 | **Repo guard test**: no binaries or dumps in the public repo | Tiny | Public repository |

### 3.2 What L2A does not build (existing functionality)

| Need | Existing tool | Label |
| --- | --- | --- |
| Disassembly and decompilation for 40+ processor families | Ghidra | [F:local] |
| Library function identification (libDaisy, STM32 HAL, CMSIS) | Ghidra FunctionID / BSim | [F:local] presence; usefulness [O] |
| Comparing builds and versions | Ghidra VersionTracking / BSim | [F:local] |
| ELF symbols, sections and maps of own builds | `arm-none-eabi-readelf/nm/objdump` | [F:repo] |
| Single-function emulation (later) | Ghidra `EmulatorHelper` | [F:local] |
| Numeric checks (filter response from coefficients and similar) | Throw-away Python in the case directory | – |
| Evidence and unknowns vocabulary | Taken from REA as a data model | [F:REA] |

### 3.3 Deferred until a test proves a need

These are candidates, not plans:

* Table-shape classifier (sine/window/exponential detection)
* FunctionID databases built from libDaisy/HAL/CMSIS builds
* MCP wrapper
* Single-function emulation harness
* Firmware container parsers (DfuSe, UF2; REA has them [F:REA])
* Mach-O thinning and Objective-C metadata for AU plugins
* Xtensa profiles (AMYboard [O])
* Audio Lab

## 4. DSP skills that are indispensable for v0.1

These are written as L2A's own text in `method/`, and nothing is copied from REA's skills. Each skill states what to
look for, which `l2a query` call proves it, and how to record the finding.

1. **Workflow and findings discipline.** The `observed` / `derived` / `inferred` levels are combined with the authority
   (artifact, analyst inference, historical reference). The flag **`prior_knowledge: true`** marks any claim based on known public
   source rather than on this binary (§6.2). Unknowns stay open until they are verified.
2. **Locating the audio path on Cortex-M/STM32H7.** The chain runs from the vector table to the SAI/DMA IRQ handlers, then
   to the framework callback and the user audio callback. A useful heuristic is FP-instruction density together with call
   depth. Library code (HAL, USB, MIDI, UI) is separated off.
3. **DSP primitive catalogue** with decompiler signatures:
   * one-pole, biquad, SVF/TPT
   * comb and allpass with circular buffers (index masking, power-of-two sizes)
   * fractional delay with interpolation
   * phase accumulators and LFOs
   * interpolated table lookups
   * envelopes and followers
   * saturation and fast-math approximations (tanh, exp2 and pow polynomials)
   * denormal guards
   * fixed-point patterns (`SSAT`, `SMULL`, `SMLAD`)
4. **Constant interpretation:**
   * sample-rate-derived constants (2π/fs, 1/fs)
   * musical constants (2^(1/12), 440, ln 2)
   * dB and exponential mappings
   * coefficient sets
   * **delay-length signatures** (mutually prime or prime sets, for identifying reverbs)
5. **Reverb and delay structure analysis:**
   * early reflections, input diffusers, tanks/FDN
   * modulation of delay taps
   * damping placement
   * feedback-matrix recognition
6. **Parameter and modulation paths:** from the control input (ADC/MIDI/CC) through the smoothing and mapping curves to the
   DSP parameter. This is needed to state "Decay maps to …" as a finding.
7. **Verification by recomputation:** extracted coefficients or tables are recomputed offline. No target code is executed in v0.1.

## 5. Security and data handling

The owner's rules in §1 apply. The following additions come from this review.

| # | Rule | Reason |
| --- | --- | --- |
| S1 | Cases live in `D:\L2A-cases\<case>\` (no spaces, outside every git checkout) | Public repo; avoids path-quoting problems [A] |
| S2 | **Analysis sessions run with the case directory as their only working area.** Claude Code uses deny rules for paths outside it; Codex uses its workspace sandbox. No access to the Daisy-Seed repo or other Playground projects during a blind run | Blind-test validity and accidental data access [O: exact settings to be defined in M0] |
| S3 | PyGhidra goes into a dedicated venv using `pip install --no-index --find-links <ghidra>/Ghidra/Features/PyGhidra/pypkg/dist` | No PyPI; same trust anchor as Ghidra [F:local] |
| S4 | Record SHA-256 of the Ghidra ZIP and the JDK archive and compare them with the official releases (NSA GitHub, Adoptium). **The origin of the existing `C:\Tools` installations is not recorded** | Provenance [O] |
| S5 | Ghidra runs with a private user-settings and script directory per run, and loads no third-party extensions or scripts (for example SVD loaders or Ghidra MCP plugins) without review | Auto-loaded scripts are code execution [A]; REA isolates HOME/APPDATA similarly [F:REA] |
| S6 | Target-derived text (strings, symbols, decompiler output) is exported with `untrusted: true`. Skills instruct agents to treat it as data | Prompt injection [F:REA uses the same marking] |
| S7 | REA is never installed. Its files are read only as untrusted objects of study | Owner decision |
| S8 | Agent memory files (for example Claude's auto-memory) must not carry case content into other sessions | Contamination and data leakage between cases [A] |
| S9 | Third-party targets (Ventris/Nemesis): the owner records the legal basis and licence terms in `case.json` **before** extraction | v0.1 §6 |

## 6. Test strategy

### 6.1 Infrastructure test (M1)

* **Target:** the existing own build `PhysicalModeling-v0.1.0.elf` (with DWARF) and its `.bin` [F:repo]. It is not blind.
* **Checks:**
  * PyGhidra starts from the offline venv.
  * The ELF imports with `ARM:LE:32:Cortex`.
  * The raw `.bin` imports at base `0x24000000`. The ELF shows `.isr_vector` at `0x24000000`, entry `0x24000749` (Thumb), and `.text` of about 134 KB [F:repo].
  * The audio callback decompiles.
  * Wall time and memory.
* **Result:** MEASURED / NOT MEASURED per check. This is the go/no-go decision for PyGhidra on Windows.

### 6.2 Main test: Rings/Torus with Cloud Reverb (M4–M5)

**Suitability: yes, with three corrections.**

Strengths:

* It is a real product image: libDaisy, HAL, MIDI, four voices, six models, a modulation matrix and the Ambient reverb.
* It is the owner's own code, so there is no legal question. The full ground truth is available.
* Base address `0x24000000` is non-standard: the bootloader loads the image into AXI SRAM [F:repo]. That makes it a realistic import challenge.

Problems and corrections:

1. **Prior-knowledge contamination.** The Rings/Torus DSP is published MIT source (Mutable Instruments, stmlib) [F:repo: `third_party/stmlib/LICENSE`]
   and widely known to language models [A]. An agent may *recognise* the resonator instead of reconstructing it.
   → Score the Rings part and the **own Cloud Reverb** (`effects/reverb`, the owner's design) separately. The Cloud Reverb is the actual
   capability test, and `prior_knowledge` claims are counted separately.
2. **Source access.** The analysing session must not be able to read the Daisy-Seed repository (S2), its memory, or the build map.
   It gets only `target.bin` and the case manifest.
3. **The composed image does not exist yet.** `physical-modeling-fx-ambient` is defined in `projects.mk`, but no
   `build/fx-ambient` exists [F:repo]. → In M4, a separate preparation session with repo access builds it at a recorded commit.
   That session produces `objcopy -O binary`, the SHA-256 and the sealed answer key.

Test design:

* **Runs.** Each run uses a fresh agent session and a fresh case directory:
  * **A** – baseline: Ghidra plus agent, without `method/` and `l2a export/query`.
  * **B** – L2A.
  * **C** – optionally, the same as B on the ELF with symbols, as an upper bound that separates tool limits from stripping.
* **Answer key.** About 20–30 checkable facts, written before the runs. Examples:
  * sample rate and block size
  * voice count and model list
  * Cloud mode decay mapping (logarithmic, 1–45 s) and damping range (14,000–400 Hz) [F:repo: `docs/MODULAR_COMPONENTS.md`]
  * reverb buffer sizes
  * delay lengths and allpass count
  * location of the dry/wet mix
* **Metrics.**
  * facts recovered correctly
  * wrong claims marked `observed` (target: 0)
  * `prior_knowledge` claims
  * unknowns left open correctly
  * time
  * reproducibility of the exports
* **Last step:** compare with the source and record the lessons learned in the case.

### 6.3 Optional practice test: Source Audio Ventris / Nemesis (M7)

* Firmware updates are distributed through the Neuro Desktop editor or its installer, not as a standalone file
  [F:web: [bonedo.de](https://www.bonedo.de/artikel/neue-firmware-fuer-das-source-audio-ventris-dual-reverb-pedal),
  [Source Audio blog](https://www.sourceaudio.net/blog-navigating-the-neuro-desktop-with-the-ventris-dual-reverb.html),
  [Nemesis manual](https://manuals.plus/source-audio/nemesis-delay-effects-pedal-manual)].
* Processor, container format and encryption are unknown [O]. If the DSP is not covered by Ghidra (no SHARC, DSP56300 or C6000 module [F:local]),
  static analysis may be impossible without third-party processor modules.
* Gate: the legal basis comes first (S9), then a feasibility check by static inspection of the installer, without running it.
  Only after that comes analysis.

## 7. Explicitly later

* MCP server or wrapper: only if CLI and file hand-over prove to be a bottleneck
* Single-function emulation (`EmulatorHelper`): executes target code; needs its own security review
* Audio Lab (measurement)
* Additional architecture profiles (Xtensa/AMYboard, x86-64 PE plugins), Mach-O handling, container parsers
* Selective REA code adoption (see [REA_Architecture_Review.md §5](REA_Architecture_Review.md))
* GUI, automatic algorithm recognition, reimplementation work

## 8. Review answers in short

| Question | Answer |
| --- | --- |
| 1. Lean enough? | Yes, after one correction: drop Ghidra script plumbing in favour of PyGhidra, and keep tools to the seven small components in §3.1. Universality comes from pass-through, not wrappers |
| 2. REA functions available via existing APIs? | Almost all of REA's Ghidra operations are thin wrappers over the Ghidra API, which PyGhidra exposes directly ([review §3](REA_Architecture_Review.md)) |
| 3. What to build ourselves? | DSP skills, the case/findings format, profile import with vector-table seeding, export with instruction mix, typed query |
| 4. Selective REA code adoption? | In the MVP, only the evidence/unknowns **vocabulary** (MIT, attributed). REA code is a reference for edge cases, not a source to copy |
| 5. Overlooked risks? | Prior-knowledge contamination, agent file access to the source, provenance of the installed Ghidra/JDK, `.bat` argument handling, auto-loaded Ghidra scripts, memory files across cases, Ventris firmware possibly being on a non-Ghidra DSP |
| 6. Ghidra on Windows feasible? | Very likely, with reasonable effort: everything needed is installed and offline-installable [F:local]. It is **NOT MEASURED** until M1 |
| 7. Indispensable DSP capabilities? | The seven skills in §4. Tool-wise, only the FP/DSP instruction counts and typed array reads |
| 8. Rings/Torus test suitable? | Yes, with the three corrections in §6.2: separate scoring for the Cloud Reverb, isolated sessions, and the composed image built in a separate preparation step |
