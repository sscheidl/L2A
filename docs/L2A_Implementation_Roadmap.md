# L2A roadmap

Basis: [L2A_Concept_v0.3.md](L2A_Concept_v0.3.md). Status: **proposal, not approved** (revision 2, 2026-11-03).

This is a private project, so the plan is small. Steps can be reordered, extended or dropped after consultation.
Each step ends with a short note: what was run, MEASURED or NOT MEASURED, and what was skipped.
Owners: **C** = Claude Code, **X** = Codex, **O** = owner.

| # | Step | Who | Done when |
| --- | --- | --- | --- |
| 1 | Approve concept v0.3; Codex reviews it | O, X | PR merged |
| 2 | Note the Ghidra and JDK hashes and compare them with the official downloads | O (C prepares the commands) | `docs/TOOLCHAIN.md` |
| 3 | **Short PyGhidra check**: Ghidra is already known to run on Windows. Install PyGhidra offline, open the Daisy ELF or `.bin`, decompile one function, note the start-up time | C | Short note |
| 4 | **Core**: `l2a open` (with a Cortex-M profile and generic ELF/PE), `l2a query`, the `case.md` template, `.gitignore` check | C, then X review | Affected tests green; review comments resolved |
| 5 | **DSP skills** in `method/`: workflow, audio path, building blocks, constants, reverb/delay, parameter paths, verification | C, then X review | Skills usable by both agents |
| 6 | **Rings/Torus with Cloud Reverb**: build `physical-modeling-fx-ambient` in the Daisy-Seed project; analyse the `.bin` only; compare with the source afterwards | C, O | Comparison note: correct / partly / wrong / missed |
| 7 | **Look back**: which skills and queries helped, what is missing, what to drop | O, C, X | Short decision list |
| 8 | **More targets** by owner priority: VST3, AMYboard, logue SDK, optionally Ventris/Nemesis (legal note first) | C | One case each |

Tests:

* For small changes, run only the affected tests.
* Before important merges and milestones, run the full local suite including Ghidra.
* GitHub Actions may be used normally (public repo). Unit tests run on pushes and PRs; nothing in CI needs proprietary files.

Not on the roadmap:

* building instruments, effects or firmware
* installing REA
* a sandbox framework or a GUI
