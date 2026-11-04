# L2A roadmap

Basis: [L2A_Concept_v0.3.md](L2A_Concept_v0.3.md). Status: **approved by the owner on 2026-11-03** (revision 2).

This is a private project, so the plan is small. Steps can be reordered, extended or dropped after consultation.
Each step ends with a short note: what was run, MEASURED or NOT MEASURED, and what was skipped.
Owners: **C** = Claude Code, **X** = Codex, **O** = owner.

| # | Step | Who | Done when |
| --- | --- | --- | --- |
| 1 | Approve concept v0.3; Codex reviews it. **Owner approved 2026-11-03** | O, X | PR merged |
| 2 | Note the Ghidra and JDK hashes and compare them with the official downloads. **Done 2026-11-03**: JDK signature valid; Ghidra install byte-identical to the official ZIP (5,219/5,219 files) | O, C | `docs/TOOLCHAIN.md` |
| 3 | **Short PyGhidra check**. Ghidra is already known to run on Windows. Steps: install PyGhidra offline; import the raw `.bin` with explicit `BinaryLoader`, `ARM:LE:32:Cortex` and base `0x24000000`, and verify the base, language and reset vector; import the ELF; save, reopen without re-analysis, decompile one function; note the import and reopen times. **Done 2026-11-03**: all checks pass; loader arguments need the `-loader-` prefix ([PYGHIDRA_CHECK.md](PYGHIDRA_CHECK.md)) | C | Short note per check |
| 4 | **Core**: `l2a open` (import and analyse once into `<case>\ghidra\`, with a Cortex-M profile and generic ELF/PE, and `--reimport`); `l2a query` that reuses the saved project, with compact default output, `--max-lines`/`--offset` sections and `--out` restricted to the case folder; `.gitignore` check. The `case.md` template is already in `templates/`. **Done 2026-11-03** ([L2A_CLI.md](L2A_CLI.md)): Codex code review found 2 issues, both fixed in `922443f`; 43 tests green locally including Ghidra; merged (PRs #5, #6). Codex security review of `f287fca` (PR #7): 7 findings, all fixed in PR #8 (merged 2026-11-03; 60 tests green including Ghidra) | C, then X review | Affected tests green; review comments resolved |
| 5 | **DSP skills** in `method/`: workflow, audio path, building blocks, constants, reverb/delay, parameter paths, verification. **Drafted 2026-11-03** ([method/README.md](../method/README.md)); platform claims spot-checked with `l2a` on our own Daisy build; Codex review done 2026-11-04 ([review](reviews/STEP7_LOOKBACK_REVIEW.md) §4: 12 corrections, applied with step-7 item D21) | C, then X review | Skills usable by both agents |
| 6 | **Rings/Torus with Cloud Reverb**: build `physical-modeling-fx-ambient` in the Daisy-Seed project; analyse the `.bin` only; compare with the source afterwards. **Done 2026-11-04**: blind analysis of the raw `.bin` (48 findings, 10 open questions, frozen with SHA-256), then Claude's source comparison and an independent Codex assessment. Agreed result: 39 correct, 9 partly, 0 wrong, 15 grouped misses; the reverb core was decoded almost completely, and the misses lie mainly in the resonator, string and FM kernels and the modulation sources. Static only: no audio, target T60 or spectra MEASURED. Comparison notes stay in the local case | C, O, X | Comparison note: correct / partly / wrong / missed |
| 7 | **Look back**: which skills and queries helped, what is missing, what to drop. **Decided 2026-11-04** ([STEP7_LOOKBACK.md](STEP7_LOOKBACK.md)): 14 error patterns from three cases, 21 decisions after the Codex review ([review](reviews/STEP7_LOOKBACK_REVIEW.md)); the owner approved 16 to do and 5 deferred. **Done 2026-11-04**: all 16 approved items implemented: method notes (D4–D11, D16–D21, with the step-5 corrections), objdump pinned as second decoder (D3, provenance against the official archive still open), literal references in `l2a query disasm` and `consts --uses` (D1). Codex final check ([review](reviews/STEP7_IMPLEMENTATION_CHECK.md), PR #16): 0 blockers; its 3 should-fix findings and 2 notes are fixed; 63 tests green locally including Ghidra | O, C, X | Short decision list |
| 8 | **More targets** by owner priority: VST3, AMYboard, logue SDK, optionally Ventris/Nemesis (legal note first) | C | One case each |

Tests:

* For small changes, run only the affected tests.
* Before important merges and milestones, run the full local suite including Ghidra.
* A new or changed GitHub Actions workflow needs the owner's approval. Once approved, small, fast unit tests run automatically
  on pushes and PRs. The full Ghidra integration runs locally or manually, not on every push. CI never needs proprietary files.

Not on the roadmap:

* building instruments, effects or firmware
* installing REA
* a sandbox framework or a GUI
