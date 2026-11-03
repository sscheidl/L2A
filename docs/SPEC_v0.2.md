# L2A – Listen to Anything: specification v0.2

Status: **concept, not approved for implementation** (2026-11-03)
Supersedes: concept v0.1 (German, 2026-11-03)
Author of this revision: Claude (architecture review). Decisions belong to the project owner.

Evidence labels used in every L2A document:

| Label | Meaning |
| --- | --- |
| **[C]** | Confirmed by reading the REA source at commit `4b961e3715375971aee6dec848827c9c072d947b` (rea-agents 6.8.0). Proof: [REA_STATIC_REVIEW_4b961e3.md](REA_STATIC_REVIEW_4b961e3.md). |
| **[A]** | Assumption: general knowledge, not checked against source or by measurement. |
| **[D]** | Proposed decision, open until the owner approves it. |

Nothing was installed, executed or registered as MCP during this review.

## 1. What changed from v0.1, and why

v0.1 assumed that REA provides the analysis base and L2A specialises it for music.
The static review shows that this holds only partly:

1. **REA cannot open our main target class on our main platform.** On Windows, REA's
   Ghidra lane admits only native PE (x86/x64/ARMNT/ARM64) and raw 6502; ELF, Mach-O and raw
   ARM are refused **[C]**. On every platform, raw imports are limited to a fixed language list.
   Thumb-only and Cortex-M images are explicitly unsupported, and the Ghidra language override
   is refused for raw targets **[C]**. Synth/effects firmware for the Daisy Seed (STM32H750, Cortex-M7)
   and most current hardware is exactly this case **[A for "most"]**.
2. **REA has no extension API.** It exposes only a `bin` entry and no `exports`, plugin loader or
   provider interface. Its docs call the composition contract internal **[C]**, so Variant A
   ("extension") does not exist in practice.
3. **REA changes too fast to fork cheaply.** Versions 4.0 → 6.8 shipped in 20 days, three majors
   landed in four days, and minors still carry BREAKING sections. The repository holds roughly 568k
   lines of non-test source and 35 CI workflows **[C]**. Variant B ("fork") would be a full-time
   maintenance job **[A, inferred from [C]]**.
4. **The most valuable part of REA for L2A is a vocabulary, not a runtime.** Its Evidence record
   separates `confidence` (observed / derived / inferred) from `authority` (shipped-artifact,
   controlled-replay, …, analyst-inference). It also keeps a residual-unknowns ledger with
   statuses and verified resolutions **[C]**. This is precisely v0.1's requirement that
   "proven findings must be distinguishable from assumptions". REA is MIT-licensed **[C]**,
   so this vocabulary can be reused with attribution.

Consequence: L2A v0.1 becomes **a method plus a few thin, pinned tools around stock Ghidra**.
REA becomes an *optional, later* adapter for the one lane where it works on Windows:
PE audio plugins (VST3/CLAP/AAX `.dll`) **[D]**.

## 2. Goal (unchanged in substance)

Support documented, reviewable investigations of music software and firmware DSP.
The output is an **independently written technical specification** of the algorithms, with
every claim traceable to evidence and every assumption marked. Principle: *understand, don't copy*.

## 3. Architecture decision

**Variant C – independent adapter [D].**

| Variant | Verdict | Reason |
| --- | --- | --- |
| A – extension of REA | **Not possible** | No public API, plugin loader or provider interface **[C]** |
| B – fork of REA | **Rejected** | Churn, size and a strict upstream contribution process **[C]**; we would use under 5 % of it **[A]** |
| C – independent adapter | **Chosen** | L2A owns a small case format and Ghidra scripts. It calls tools through narrow, pinned interfaces and may later call REA's CLI (`--json`) for PE targets |

Build-time composition only; no runtime plugin system.

```
L2A case (outside the repo)  ──>  l2a tools (this repo)  ──>  Ghidra 12.1.x headless (user-installed, pinned)
   manifest, findings,               import profile,             Python constant scanner (stdlib only)
   unknowns, spec                    export, scan                [later, optional] REA CLI for PE plugins
```

## 4. Scope of v0.1 (minimal verifiable version)

### 4.1 Supported targets

| Target | v0.1 | Reason |
| --- | --- | --- |
| ARM Cortex-M (Thumb-2, with or without FPU): ELF, raw `.bin`, Intel HEX | **Yes** | Main use case (Daisy and STM32 products). Stock Ghidra has the `ARM:LE:32:Cortex` language **[A]** |
| Windows x86-64 PE audio plugins | **No, Phase 3** | REA would support it **[C]**, but there is no concrete case yet |
| macOS universal Mach-O plugins | No | REA refuses fat Mach-O; requires thinning and POSIX **[C]** |
| SHARC, DSP56300, TI C6000, Spin FV-1 | No | No REA support **[C]**; no stock Ghidra module **[A]**. FV-1 already has its own project (`fv-1-DSP-xtractor`) |
| ESP32 / Xtensa (AMYboard) | No, open question | Not admitted by REA **[C]**. Whether AMYboard is ESP32-based and how good Ghidra's Xtensa support is: **[A]**, to be checked |

### 4.2 Components

| # | Component | What it does | Not included |
| --- | --- | --- | --- |
| 1 | **Case format** | `case.json` manifest: target SHA-256, source/provenance, licence, **legal-basis note (filled by the owner)**, data classification, **AI-egress permission**, tool versions. Folder layout for findings, unknowns and the final spec | No database, no server |
| 2 | **Findings schema** | JSON Schema for findings and unknowns, adopting REA's `confidence` / `authority` / unknown-status vocabulary with attribution (MIT). Markdown renderer for review | No content addressing or hash chains in v0.1 |
| 3 | **Cortex-M import** | A Ghidra headless script plus a small target profile (base address, flash/RAM regions, optional SVD file). It reads the vector table (initial SP, reset and IRQ handlers with the Thumb bit) and seeds functions | No auto-detection of the load address in v0.1; the profile is given by the analyst |
| 4 | **Export** | A Ghidra headless script that writes JSON: functions, decompiler output, xrefs, call edges, referenced constants, and **per-function instruction mix** (FPU/DSP-instruction density, loops). This is how audio hotspots are found | No GUI, no MCP |
| 5 | **Constant/table scanner** | Python, stdlib only. Finds float32, int16/Q15 and Q31 arrays and known DSP constants (π fractions, 1/√2, sample-rate values, dB/exp/pow tables) and classifies table shapes (sine, window, ramp, exponential) | No algorithm recogniser |
| 6 | **DSP analysis method** | `AGENTS`/skill markdown written by L2A: how to locate the audio callback (SAI/DMA IRQ → callback), identify filter topologies, oscillators, delay lines and modulation paths, and how to write findings. Checklist per DSP family (3.1 of v0.1) | Copies nothing from REA's skills |

Everything else from v0.1 sections 3–4 is the **analyst's work using these tools**, not a feature.

### 4.3 Verification in v0.1

Hypotheses are checked statically and numerically: cross-references, constant values, and
recomputing for example a filter response from extracted coefficients in a scratch script.
**No target code is executed in v0.1.** Emulating single functions is deferred (see section 8).

## 5. Phase plan (revised)

| Phase | Content | Exit criterion |
| --- | --- | --- |
| **0** | Static REA review (done in substance, see the review file). **Ghidra** provenance check (official release, SHA-256, JDK) | Owner approves this spec and the Codex brief |
| **1** | Components 1–6 in this repo, with unit tests on synthetic inputs | Tests green locally; nothing proprietary in git |
| **2** | Scientific function test on a **self-built** binary with sealed ground truth (section 7) | Metrics recorded as MEASURED / NOT MEASURED |
| **3** | Only on demand: REA CLI adapter for PE plugins, Xtensa, emulation, Audio Lab | Separate approval per item |

## 6. Security and data rules (binding)

The rules from v0.1 section 5 remain. Added or sharpened:

1. **This repository is public.** It contains only L2A's own code, schemas, docs and generated
   synthetic fixtures. Cases live outside the checkout (default `../L2A-cases/`, never pushed).
   `.gitignore` blocks common binary and dump formats, and a test fails if tracked files match them.
2. **AI egress is a per-case decision.** Decompiled proprietary code shown to a cloud agent
   (Codex, Claude, GPT) leaves the machine. `case.json` records the owner's decision:
   `ai_egress: none | summaries | full`. Tools must not exceed it, and for `none` the agent may see only
   L2A's own aggregates.
3. **Analysed bytes are untrusted input, including for the agent.** Strings, symbol names and
   decompiler output can carry prompt-injection text. Agent instructions treat them as data;
   exports mark them as untrusted (REA does the same with `untrusted_content` **[C]**).
4. **No REA runtime in v0.1.** If REA is approved later (Phase 3), the conditions are:
   - pinned commit and lockfile
   - `npm ci --ignore-scripts`
   - no `rea setup` (it edits agent configs **[C]**)
   - no `npx …@latest` (REA's own skill instructs this **[C]**)
   - no `mcp --http` (no auth, no TLS **[C]**)
   - `REA_MCP_TOOL_FAMILIES` restricted
   - a separate Windows user or VM without credentials
5. **Ghidra and JDK are user-installed and pinned.** They come from official sources, with the SHA-256
   recorded in `case.json`. Ghidra is not a sandbox (REA's own security policy says so **[C]**).
   Untrusted vendor files are opened in a separate Windows user or Windows Sandbox.
6. **Clean-room separation for implementations.** The final spec must not contain decompiled
   listings or verbatim tables beyond what a short citation needs. Any later C/C++ implementation
   is written from the spec, ideally in a separate agent session that never saw the decompiler output.
7. **No execution of target code, no hardware control, no network access by L2A tools.**

## 7. Phase 2 test design

* **Target**: a small firmware built by us from open components (for example DaisySP biquad,
  oscillator, delay and LFO under MIT, with parameters we choose), using the pinned Daisy toolchain.
  It is delivered as stripped ELF **and** raw `.bin`.
* **Ground truth**: source, parameters and expected signal flow sealed in `answer-key/`, which is
  not visible to the analysing agent session.
* **Baseline**: the same binary analysed with plain Ghidra and an agent, without L2A tools.
* **Metrics** (recorded as MEASURED with date):
  - recovered ground-truth items / total
  - wrong claims marked "observed" (target: 0)
  - unknowns correctly left open
  - analyst/agent time
  - reproducibility (a second run produces the same exports)

## 8. Deferred (explicitly not v0.1)

* Any REA runtime or MCP integration (Phase 3, PE plugins only, after its own isolated test)
* MCP server for L2A itself (CLI + JSON files are enough for agents)
* Emulating single DSP functions (Ghidra emulator / Unicorn): this executes target code and is security-relevant
* L2A Audio Lab (measurement); legally possibly the cleaner route for proprietary targets (risk R7)
* Non-Cortex-M architectures, Mach-O, firmware unpacking (Binwalk/Unblob are Linux-only in REA **[C]**)
* C++ class/vtable recovery for JUCE/VST3 plugins, plugin-entry recognition
* Automatic DSP algorithm recognition, any GUI, any reimplementation work

## 9. Roles

Unchanged from v0.1. Additionally, this repository's `docs/` are the single source of truth.
Claude, Codex and GPT outputs that change scope are merged into these files by PR, and the owner approves.
