# Roadmap step 7: look back (decided)

Status: **decided by the owner on 2026-11-04.** Drafted by Claude, revised the same day after the Codex review
([STEP7_LOOKBACK_REVIEW.md](reviews/STEP7_LOOKBACK_REVIEW.md), PR #14). The owner approved every recommendation in §4:
16 items to do, 5 deferred. This file records the decisions; the changes to `method/`, `l2a` and the toolchain follow in
separate PRs.

Labels: **[F]** checked fact, with a case reference; **[A]** assumption; **[O]** open question.
The case folders stay local (AGENTS.md). This file cites only their names and summary counts.

## 1. Basis

| Case | What it tested | Result [F] |
| --- | --- | --- |
| `pm-v010-binary` | Own Daisy build `PhysicalModeling-v0.1.0.bin`, binary only. Not a clean blind test: the analyst had seen ELF symbols before | 40 findings: 30 correct, 10 partly, 0 wrong. One open-question guess was wrong (board). "Partly" there also covered incomplete findings, so the counts are not directly comparable with step 6 |
| `nebulae-v2.1.2` | Linux board with Csound scripts, MIT upstream; done in a cloud session and handed back as one archive | No graded comparison. Lessons merged in PR #11 (`method/02_audio_path.md`) |
| `pm-fx-ambient-blind` (step 6) | Own build `PhysicalModelingFxAmbient-v0.2.1.bin`, strictly blind by the recorded protocol; frozen findings, then Claude's source comparison, then an independent Codex assessment | 48 findings: 39 correct, 9 partly, 0 wrong; 15 grouped misses. The two assessors agreed on every final grade |

## 2. What helped (keep)

* **Import once, query many times** [F]. Step 6 imported in 3.2 s and analysed in 16.9 s. Later queries in both
  sessions reused the saved project; no re-import is recorded.
* **Compact output and `--out` files** [F]. Large functions went to `out/` and were read in parts. No session reported
  the 60-line default as a blocker.
* **Recompute scripts** [F]. `recompute.py` printed 19 coefficients next to their float32 words, plus the delay-length,
  decay and damping tables. It printed values but asserted nothing: a label was wrong, and the F36 window was computed
  without the later rounding. The bend scale (F46) was not in it at all. See D4 and D17.
* **Offline model** [F]. The tank model implements the decoded gain law and gives 0.92 s for a nominal 1.0 s. That the
  damping and modulation explain the gap is inferred [A], and the model is not a target measurement (D18).
* **Grades by area** [F], counted from the final list: reverb F20–F41 19 of 22 correct (wrapper F20–F25 6/6, core
  F26–F41 13/16); generator F10–F19 9/10. These are finding counts, not a measure of coverage.
* **Blind protocol** [F]. Freezing the findings with a SHA-256, sealing the build reference, and letting the second
  assessor grade before reading the first assessment worked as documented. Each assessor caught an error that the
  other missed (Claude: F9 timer; Codex: F29 clamp, the X9/X10 counting error).
* **[A] marks on prior knowledge** [F]. The wrong board guess appeared in a finding's notes and as an open question, but
  marked as tentative, so it was never treated as a confirmed fact.

## 3. What went wrong, and why

Causes marked [A] are plausible mechanisms. The cases do not record the analyst's attention or time per finding.

| # | Error pattern | Where [F] | Cause |
| --- | --- | --- | --- |
| E1 | A PC-relative literal read one word off | Step 6 F38 (45 s read as 400 s) | `consts` lists each literal with only its **first** user and a count, and `disasm` prints `[pc,#0x28]` unresolved. `xrefs <literal address>` would have listed every user, but it was not used; the method does not mention it |
| E2 | A scale constant misread and the range derived from it | Step 6 F46 (bend ±1 instead of ±2 semitones) | A missing verification step: the constant was not in `recompute.py` |
| E3 | FPv5 instructions not decoded | Step 6 F36 (missed `vrinta` rounding); clamps lost in decompiler output | Ghidra 12.1.4 shows the checked `VSEL` and `VRINTA` words as `cdp2`, and the decompiler loses their effect. A case script decoded some of them; GNU objdump decodes them correctly. Other FPv5 forms were not checked |
| E4 | A function's role guessed from its call site | Step 6 F47 (`Controller::Commit` read as MIDI init), F48 (exp2 table read as clock divisions); `pm-v010` F38 (USB port) | The guessed role had no inferred label of its own; the rows mixed observed and inferred facts under one label. For F47 the callee was not decompiled; for the others the history is not recorded |
| E5 | A data flow interpreted from one path only | Step 6 F44 (CC 28 read as a switch lock), F48 (column 6 read as decay offset); `pm-v010` F25 (coupling read as output mix) | [A] The value was not followed to its other readers and writers. `pm-v010` proposed a method rule for this; it was not adopted |
| E6 | The same board guessed wrong twice | `pm-v010` Q5 and step 6 Q9 (Daisy Field; really `desktop_devkit`) | A control count and layout were used as evidence for a board |
| E7 | Coverage spent on unreachable code | Step 6: shimmer, freeze and alternate modes decoded in detail (F35–F38); 5 of 15 grouped misses are generator and exciter behaviour (M1–M5) | [A] Time went where the structure was clearest, not where the sound comes from |
| E8 | RAM initial values not read | Step 6 Q6 (per-model gains open blind) | The reset handler's `.data` copy (load-image source, RAM destination, length) was not followed. Here the load image is in AXI SRAM, and the values were in the `.bin` all the time |
| E9 | Grading slips by the assessors themselves | Codex F9 (missed a false aside); Claude F29 (rule not applied to an inactive branch), X9/X10 (unreachable items counted as reachable) | The strict rule existed but was applied inconsistently. There was no checklist for asides, inactive branches and reachability |
| E10 | Model consistency, causal explanation and target behaviour mixed in one statement | Step 6 F32; draft §2 before this revision | No separate evidence levels for "formula matches", "model behaves so" and "firmware measured" (Codex) |
| E11 | A printed recomputation taken as a passed check | Step 6 `recompute.txt` labels, F36, F46 | No pass criterion, tolerance or rounding step stated (Codex) |
| E12 | Summary counts drift after append-only corrections | Step 6 reverb 20/22 in the first draft after F29 changed; pm-v010 "partly" criterion | Summaries were not derived again from the final grade list (Codex) |
| E13 | Behaviour seen but not recorded, so it drops out of coverage | `pm-v010` infinite sustain; the step-6 examined-functions and miss lists | Only one of the two `pm-v010` method suggestions was carried forward (Codex) |
| E14 | A delivered or frozen state and the later working state confused | Nebulae archive intake and later `case.md` edits; step-6 model script changed after freezing | Hand-over guidance does not keep the original archive and later edits apart (Codex) |

## 4. Decision list

Effort: **S** = under an hour with tests, **M** = a few hours, **L** = a day or more. Estimates are assumptions [A].
All code items follow AGENTS.md: branch, tests, `check_repo.py`, PR, Codex review. Read-only `query` stays read-only.
The Owner column records the owner's decision of 2026-11-04. The Claude column shows Claude's recommendation after the review; where it changed, the first draft's value is in
brackets. Details of the Codex recommendations are in the review, §2 and §3.

| ID | Proposal | Type | Fixes | Effort | Claude | Codex | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | Document `xrefs <literal address>` for all users of a literal. Then `disasm` annotates the data references Ghidra resolves (address, word, optional float reading), and `consts --uses` lists all users | method, l2a | E1 | S (note), M (code) | Do | Do, narrower: note first, annotation as convenience | Approved: do |
| D2 | `disasm` decodes the FPv5 `cdp2` encodings as an annotation. This does not repair the decompiler | l2a | E3 | M–L | Defer (was: do) | Defer until D3 leaves a costly gap | Approved: defer |
| D3 | Pin GNU `arm-none-eabi-objdump` in `docs/TOOLCHAIN.md` (version, hash, provenance) as a second decoder; its output is target data | toolchain | E3 | S–M | Do first (was: only if D2 declined) | Do, independently of D2 | Approved: do |
| D4 | `07_verification.md`: every stated range, unit or count gets a recompute line with inputs, rate, precision, clamping and rounding | method | E2 | S | Do | Do, with semantic checks | Approved: do |
| D5 | `01_workflow.md`: a function's role comes from its body, its disassembly or a verified contract. Otherwise that role is marked *inferred* on its own, with what would decide it | method | E4 | S | Do | Do | Approved: do |
| D6 | `07_verification.md`: before recording a data-flow interpretation, trace the known readers, writers, flags and resets; list the unresolved ones | method | E5 | S | Do, bounded | Do, as bounded tracing | Approved: do |
| D7 | `02_audio_path.md`: do not name a board from control counts. A string, pin map or peripheral setup is evidence only when corroborated | method | E6 | S | Do | Do | Approved: do |
| D8 | `01_workflow.md`: plan coverage by the owner's question and by sound contribution. Unreachable modes get one line each by default; keep a list of what was left out | method | E7 | S | Do | Do, task-scoped | Approved: do |
| D9 | `02_audio_path.md`: follow the reset handler's `.data` copy (load-image source, destination, length; BSS separately) and read initial values from the load image | method | E8 | S | Do; helper later | Do method; defer helper | Approved: do |
| D10 | `07_verification.md`: checklist for comparisons. Check every aside; apply the rule to inactive branches; define "reachable" (host path and trigger); keep library capability, reachable behaviour and measured sound apart | method | E9 | S | Do | Do | Approved: do |
| D11 | `07_verification.md`: the step-6 protocol as standard for **formal** blind comparisons (uncontaminated analyst, freeze with hash, sealed reference, unanchored second assessor, append-only corrections) | method | keeps §2 | S | Do, for formal blind tests | Do for formal blind tests; optional elsewhere | Approved: do |
| D12 | `l2a query` for base-plus-offset accesses, as candidates within one function first | l2a | E5 | M–L | Defer until specified (was: do after D1/D2) | Defer until precisely scoped | Approved: defer |
| D13 | Create functions at code pointers found in literal pools during `l2a open` | l2a | — | M | Defer | Defer | Approved: defer |
| D14 | Constant provenance query: which instruction stores this value | l2a | E5 | M–L | Defer | Defer | Approved: defer |
| D15 | An `l2a` emulator command for single DSP functions | l2a | Q10-type questions | L | Defer | Defer | Approved: defer |
| D16 | Derive every summary count from the final grade and coverage list; label subgroups; keep the original counts as history | method | E12 | S | Do | Do (new) | Approved: do |
| D17 | Recomputations state a pass criterion: matching label and expression, units and rate, tolerance or bits, rounding | method | E11 | S | Do | Do (new) | Approved: do |
| D18 | Offline models record script hash, inputs, precision, the measured property and what they leave out; never called a target measurement | method | E10 | S | Do | Do (new) | Approved: do |
| D19 | Record seen behaviour and unresolved consumers in `case.md` at once, even before it is explained | method | E13 | S | Do | Do (new) | Approved: do |
| D20 | Hand-over intake for every archive: check member paths and types before extraction, verify the manifest without running scripts, keep the original archive and manifest apart from later edits | method | E14 | S | Do | Do (new) | Approved: do |
| D21 | Apply the step-5 skills corrections S1–S12 from the review, §4 | method | step 5 | M | Do, together with D4–D11 | Proposed in review §4 | Approved: do |

Count: Claude 16 do, 5 defer. Codex 16 do or proposed, 5 defer. The two columns agree on every item, and the owner
approved all of them.
Codex's narrower scopes for D1, D6, D8, D9 and D11 are taken into the proposal text.

## 5. What to drop or shrink

* **Detailed decoding of unreachable modes** (see D8): shrink to one line per mode by default, and keep a list of the
  work left out.
* **Superseded documents in `docs/`**: `SPEC_v0.2.md`, `CODEX_BRIEF_v0.1.md` and `REA_DECISION_MATRIX.md` could move to
  `docs/history/`, where `CONCEPT_v0.1.de.md` already is. `RISKS_AND_OPEN_QUESTIONS.md` is only partly superseded and
  stays. Both reviewers recommend doing this later, in a separate small PR with link checks, after the method changes.
* Nothing in `l2a` looks unused [A]. The usage of each query was not counted, so no query is dropped.

## 6. Open points and not covered

* The step-5 skills review is now done (review §4: all eight files, 12 points, all 44 constant entries correct).
  The owner accepted D21 on 2026-11-04, so roadmap step 5 counts as reviewed; the corrections follow with D21.
* [O] Step 8 order (VST3, AMYboard, logue SDK, Ventris/Nemesis) is the owner's call. A VST3 target would test the `pe`
  profile, which no case has used yet [F].
* Not counted: time spent per finding, number of queries, or which skill files the sessions actually opened.
* The Nebulae case had no graded comparison, so its weight here is low.

## 7. Implementation (2026-11-04)

| Items | Where | Status |
| --- | --- | --- |
| D4–D11, D16–D20, D21 (S1–S12) | `method/01`–`07`, `method/README.md` | Done |
| D3 | `docs/TOOLCHAIN.md`, *GNU objdump* | Done. Provenance against the official xPack archive is NOT VERIFIED [O]: that needs a download with the owner's consent |
| D1 | `src/l2a/queries.py`, `src/l2a/values.py`, `docs/L2A_CLI.md`, tests | Done. MEASURED 2026-11-04 on the step-6 case: `disasm 0x2400ece6` now shows `; [2400ed10] word 0x42340000 float 45`, and `consts --uses` lists both users of that literal |
| D2, D12–D15 | — | Deferred, as decided |

The Codex final check (`docs/reviews/STEP7_IMPLEMENTATION_CHECK.md`, PR #16) found 0 blockers, 3 should-fix
findings (xrefs wording, frozen model artefacts, archive and manifest intake) and 2 notes (a multi-user regression
test, an objdump re-check command). All five are fixed in the same PR.
