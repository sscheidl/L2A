# L2A implementation roadmap (minimal, prioritised)

Basis: [L2A_Concept_v0.3.md](L2A_Concept_v0.3.md). Status: **proposal, not approved**.

Every milestone ends with a short result note: commands run, results marked **MEASURED** (with date) or **NOT MEASURED**,
and what is still open. Owners:

* **C** = Claude Code (main developer)
* **X** = Codex (independent review)
* **O** = owner

## M0 – Approval and environment (O, X)

| Step | Who | Exit |
| --- | --- | --- |
| Approve concept v0.3 (PyGhidra architecture, MVP scope, test design) | O | Merged PR |
| Record SHA-256 of the Ghidra 12.1.4 ZIP and JDK 21.0.12 archives; compare with official releases | O (C prepares the commands) | `docs/TOOLCHAIN.md` |
| Create `D:\L2A-cases\`; define session isolation for blind runs (Claude Code deny rules, Codex sandbox) | O + C | Documented settings |
| Independent security review of the plan: offline PyGhidra venv, Ghidra script/extension isolation, data flow to agents | X | Review note in the PR |

## M1 – Infrastructure test (C, about half a day [A])

1. Offline venv: `pip install --no-index --find-links <ghidra>\Ghidra\Features\PyGhidra\pypkg\dist pyghidra`.
2. Throw-away script in `D:\L2A-cases\infra-test\`, not in the repo:
   * import `PhysicalModeling-v0.1.0.elf` with `ARM:LE:32:Cortex`
   * import the raw `.bin` at `0x24000000`
   * decompile the audio callback
   * time and memory usage
3. Result note: go/no-go for PyGhidra on Windows. On no-go, the fallback is `analyzeHeadless` with an argument allowlist.

## M2 – L2A core v0.1 (C, then X review)

Order of work:

1. Repo skeleton:
   * `pyproject.toml`: stdlib only, plus PyGhidra as an optional runtime dependency
   * `l2a/`, `tests/`, `schemas/`, `method/`
   * `THIRD_PARTY_NOTICES.md` with the REA vocabulary attribution
2. `l2a case init` + `schemas/case.schema.json`: target SHA-256, provenance, licence, legal-basis note, tool versions and hashes.
   Refuses a location inside a git checkout.
3. `schemas/finding.schema.json`, `unknown.schema.json` + `l2a findings render`:
   * `confidence` × `authority`
   * `prior_knowledge`
   * `observed` requires an evidence location
4. `l2a import --profile`:
   * loader, language, base and regions
   * Cortex-M vector-table seeding (initial SP check, reset and IRQ handlers, Thumb bit)
   * private Ghidra settings and script directories
5. `l2a export`:
   * functions, decompiler text, calls, xrefs
   * strings tagged `untrusted`
   * FP/DSP instruction counts
   * deterministic output; analysis options recorded
6. `l2a query`: `decompile`, `xrefs`, `read --type float32|int16|q15|q31|u16 --count N`.
7. Repo guard test.

Tests:

* Unit tests for schemas and the CLI run without Ghidra.
* Integration tests run against a fixture **built from source at test time** with the pinned Daisy toolchain, never a committed binary.
  They are skipped with a clear message if Ghidra is absent.

Exit criteria:

* tests green locally
* the Codex review comments resolved

## M3 – DSP skills v0.1 (C, then X review for injection and overreach)

`method/` files, each with "what to look for", "how to prove it with `l2a query`" and "how to record it":

| File | Content |
| --- | --- |
| `00_workflow.md` | Case flow, findings discipline, `prior_knowledge`, unknowns |
| `10_audio_path_cortex_m.md` | Vector table → SAI/DMA IRQs → callback chain on STM32H7/libDaisy; separating library code |
| `20_dsp_primitives.md` | Filters, delays, comb/allpass, interpolation, oscillators/LFOs, tables, envelopes, saturation, fast math, fixed point |
| `30_constants.md` | Sample-rate, musical, dB/exponential constants; delay-length signatures |
| `40_reverb_delay.md` | Diffusers, tanks/FDN, modulation, damping, feedback matrices |
| `50_parameters.md` | Control input → smoothing/mapping → DSP parameter |
| `60_verification.md` | Offline recomputation; what counts as verified |

`AGENTS.md` points both agents to `method/`. There are no agent-specific copies.

## M4 – Main test preparation (separate session with repo access; C or X)

* Build `physical-modeling-fx-ambient` at a recorded Daisy-Seed commit with the pinned toolchain.
  Produce `objcopy -O binary`, the SHA-256 and the ELF (kept only for run C and for scoring).
* Write the sealed answer key (20–30 facts, Cloud Reverb and Rings scored separately) and the scoring sheet.
  Store it outside every analysis case directory.

## M5 – Main test run (fresh sessions, case directory only)

* **Run A:** baseline (Ghidra + agent, no `method/`, no `l2a export/query`).
* **Run B:** L2A.
* **Run C** (optional): L2A on the ELF with symbols.
* Score against the answer key, then compare with the source.
* Result note with MEASURED metrics: correct facts, wrong `observed` claims, `prior_knowledge` claims, open unknowns, time, reproducibility.

## M6 – Decision gate (O, with C and X)

Decide only from M5 evidence which deferred candidates become work:

* table classifier
* FunctionID DBs for libDaisy/HAL/CMSIS
* MCP wrapper
* emulation harness
* container parsers
* more profiles

Also check whether any skill or tool proved useless and should be removed.

## M7 – Optional: Source Audio Ventris / Nemesis

Order:

1. Legal basis and licence terms recorded by the owner.
2. Static feasibility check of the Neuro Desktop installer and firmware container, without running it: CPU, format, encryption.
3. Analysis only if a Ghidra processor module exists.

## Not on the roadmap

Audio Lab, GUI, automatic algorithm recognition, reimplementation of analysed algorithms, any REA installation.
Each needs a new owner decision.
