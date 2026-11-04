# Roadmap step 7: look back (draft)

Status: **draft by Claude, 2026-11-04.** Codex reviews it next, and then the owner decides each item in §4. This file
only proposes. Nothing in it changes `method/`, `l2a` or the toolchain.

Labels: **[F]** checked fact, with a case reference; **[A]** assumption; **[O]** open question.
The case folders stay local (AGENTS.md). This file cites only their names and summary counts.

## 1. Basis

| Case | What it tested | Result [F] |
| --- | --- | --- |
| `pm-v010-binary` | Own Daisy build `PhysicalModeling-v0.1.0.bin`, binary only. Not a clean blind test: the analyst had seen ELF symbols before | 40 findings: 30 correct, 10 partly, 0 wrong. One open-question guess was wrong (board) |
| `nebulae-v2.1.2` | Linux board with Csound scripts, MIT upstream; done in a cloud session and handed back as one archive | No graded comparison. Lessons merged in PR #11 (`method/02_audio_path.md`) |
| `pm-fx-ambient-blind` (step 6) | Own build `PhysicalModelingFxAmbient-v0.2.1.bin`, strictly blind; frozen findings, then Claude's source comparison, then an independent Codex assessment | 48 findings: 39 correct, 9 partly, 0 wrong; 15 grouped misses. The two assessors agreed on every grade after one round |

## 2. What helped (keep)

* **Import once, query many times** [F]. Step 6 imported in 3.2 s and analysed in 16.9 s. Every later query, in both
  sessions, reused the same project. No re-import was needed.
* **Compact output and `--out` files** [F]. Large functions went to `out/` and were read in parts. The 60-line default was
  never a blocker.
* **Recompute scripts** [F]. `recompute.py` checked 19 coefficients against their float32 words, plus the delay-length,
  decay and damping tables. No recomputed value turned out wrong. The one scale error (pitch bend) was a constant that had *not* been recomputed.
* **Offline model** [F]. The tank model reproduced the decoded T60 formula (0.92 s for nominal 1.0 s, with damping and
  modulation explaining the gap). The reverb core was the best-graded area: 20 of 22 correct.
* **Blind protocol** [F]. Freezing the findings with a SHA-256, sealing the build reference, and letting the second
  assessor grade before reading the first assessment worked. Each assessor caught an error that the other missed
  (Claude: F9 timer; Codex: F29 clamp, the X9/X10 counting error).
* **[A] marks on prior knowledge** [F]. The wrong board guess was marked [A] and kept as an open question, so it never
  became a finding.

## 3. What went wrong, and why

| # | Error pattern | Where [F] | Cause |
| --- | --- | --- | --- |
| E1 | A PC-relative literal read one word off | Step 6 F38 (45 s read as 400 s) | `l2a query consts` lists each literal with only its **first** user and a count (`@2400ea28 (x2)`). `disasm` prints `[pc,#0x28]` unresolved. The analyst had to compute the address by hand |
| E2 | A scale constant misread and the range derived from it | Step 6 F46 (bend ±1 instead of ±2 semitones) | The constant was not in `recompute.py` |
| E3 | FPv5 instructions not decoded | Step 6 F36 (missed `vrinta` rounding); clamps lost in decompiler output | Ghidra 12.1.4 shows `VSEL`/`VRINTA`/`VMAXNM` as `cdp2`. A case script (`fpv5_decode.py`) decoded some of them; GNU objdump decodes them correctly |
| E4 | A function's role guessed from its call site | Step 6 F47 (`Controller::Commit` read as MIDI init), F48 (exp2 table read as clock divisions); `pm-v010` F38 (USB port) | The callee was not decompiled, and the finding did not say "inferred" |
| E5 | A data flow interpreted from one path only | Step 6 F44 (CC 28 read as a switch lock), F48 (column 6 read as decay offset); `pm-v010` F25 (coupling read as output mix) | The value was not followed to all its readers. `pm-v010` proposed a method rule for this; it was not adopted |
| E6 | The same board guessed wrong twice | `pm-v010` Q5 and step 6 Q9 (Daisy Field; really `desktop_devkit`) | A control count was used as evidence for a board |
| E7 | Coverage spent on unreachable code | Step 6: shimmer, freeze and alternate modes decoded in detail (F35–F38); 5 of 15 misses are the resonator, string and FM kernels | Time went where the structure was clearest, not where the sound comes from |
| E8 | RAM initial values not read | Step 6 Q6 (per-model gains open blind) | The reset handler's `.data` copy (flash source, RAM destination, length) was not followed. The values were in the `.bin` all the time |
| E9 | Grading slips by the assessors themselves | Codex F9 (missed a false aside); Claude F29 (rule not applied to an inactive branch), X9/X10 (unreachable items counted as reachable) | No explicit rule for asides and inactive branches; "reachable" not defined |

## 4. Decision list

Effort: **S** = under an hour with tests, **M** = a few hours, **L** = a day or more. All code items follow AGENTS.md:
branch, tests, `check_repo.py`, PR, Codex review.

| ID | Proposal | Type | Fixes | Effort | Claude's recommendation | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | `l2a query disasm` annotates every data reference inline (`; [0x2400ed10] float 45`), and `consts --uses` lists all user addresses instead of the first one | l2a | E1 | S | Do | |
| D2 | `l2a query disasm` decodes the FPv5 `cdp2` encodings (`VSEL`, `VRINTA/N/P/M`, `VMAXNM/VMINNM`, `VCVTA…`) as an annotation. L2A's own code, from the Arm encoding tables; unit tests on known words | l2a | E3 | M | Do | |
| D3 | Alternative or addition to D2: pin GNU `arm-none-eabi-objdump` in `docs/TOOLCHAIN.md` as a second decoder | toolchain | E3 | S | Only if D2 is declined | |
| D4 | `07_verification.md`: every stated range, unit or count in a finding gets a recompute line | method | E2 | S | Do | |
| D5 | `01_workflow.md`: a function's role comes from its body. If the callee was not decompiled, the finding says *inferred* in its own row | method | E4 | S | Do | |
| D6 | `07_verification.md`: before recording a data-flow interpretation, follow the value once to all its readers and its writers (the `pm-v010` proposal) | method | E5 | S | Do | |
| D7 | `02_audio_path.md`: do not name a board from control counts. Record "board unknown" unless a string, pin map or peripheral setup identifies it | method | E6 | S | Do | |
| D8 | `01_workflow.md`: plan coverage by sound contribution. Generator and exciter kernels and the real parameter routing come first; unreachable modes get one line each until those are done | method | E7 | S | Do | |
| D9 | `02_audio_path.md`: read the reset handler's `.data` copy loop and take RAM initial values from the flash source. Later perhaps an `l2a` helper that maps the copy | method, later l2a | E8 | S (method) | Do the method note; tool later if needed again | |
| D10 | `07_verification.md`: grading rules for comparisons. Check every aside; apply the rule to inactive branches too; keep three layers apart: library capability, behaviour reachable in this firmware, measured sound | method | E9 | S | Do | |
| D11 | `07_verification.md`: make the step-6 blind protocol the standard comparison protocol (freeze with hash, sealed reference, second assessor grades before reading the first, frozen part hashed, later notes appended only) | method | keeps §2 | S | Do | |
| D12 | `l2a query` for struct-offset accesses: "instructions that read or write `base+0x28…0x34`", across functions (`pm-v010` proposal 2). Step 6 Q3 needed exactly this | l2a | E5 | M | Do after D1/D2 | |
| D13 | Create functions at code pointers found in literal pools during `l2a open` (`pm-v010` proposal 1) | l2a | — | M | Defer: no new evidence in step 6 | |
| D14 | Constant provenance query: which instruction stores this value (`pm-v010` proposal 3) | l2a | E5 | M | Defer: D6 and D12 cover most cases | |
| D15 | An `l2a` emulator command for single DSP functions (`07_verification.md` [O]) | l2a | Q10-type questions | L | Defer: not needed often yet | |

## 5. What to drop or shrink

* **Detailed decoding of unreachable modes** (see D8): shrink to one line per mode unless the owner asks for more.
* **Superseded documents in `docs/`**: `SPEC_v0.2.md`, `CODEX_BRIEF_v0.1.md`, `REA_DECISION_MATRIX.md` and the answered
  part of `RISKS_AND_OPEN_QUESTIONS.md` could move to `docs/history/`, where `CONCEPT_v0.1.de.md` already is. Links would
  need updating. Recommendation: do it, as a separate small PR.
* Nothing in `l2a` itself looks unused [A]. The usage of each query was not counted.

## 6. Open points and not covered

* [O] The Codex review of the step-5 skills (roadmap step 5) is still open. The review of this draft could cover it.
* [O] Step 8 order (VST3, AMYboard, logue SDK, Ventris/Nemesis) is the owner's call. A VST3 target would test the `pe`
  profile, which no case has used yet [F].
* Not counted: time spent per finding, number of queries, or which skill files the sessions actually opened.
* The Nebulae case had no graded comparison, so its weight here is low.
