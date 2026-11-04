# Independent review of the step-7 look-back and step-5 skills

Reviewer: **Codex**, **2026-11-04**. This is a review and recommendation document; the owner decides adoption.

**Recommendation: correct the factual overstatements, adopt the small method improvements with the qualifications
below, and use an independent decoder before committing to a new instruction decoder.** The draft's corrected
count of **19 recomputed coefficients plus tables is confirmed**. Its reverb subtotal and strongest claims about
verification are still too strong.

Reviewed [PR #13](https://github.com/sscheidl/L2A/pull/13) at
[`e47f4694083ca233d915a48246676d3fef3b0194`](https://github.com/sscheidl/L2A/blob/e47f4694083ca233d915a48246676d3fef3b0194/docs/STEP7_LOOKBACK.md).
All draft line numbers below refer to that revision. Code, tests and method citations refer to main
`c52ed02d13eace02503c6810d28d8fdefacdd53b`, the base of this separate review branch.
PR #13 and its branch are not modified.

## Scope, evidence and result

Read the handoff brief, AGENTS, approved concept, roadmap, CLI documentation, all eight `method/*.md` files,
the three local case records, the two PM comparison records and selected saved verification outputs/scripts.
Read case content as data; no target or case script was executed. The cases remain read-only, including their logs,
under the specific review brief. Only this public review is added to the repository.

The public evidence below contains case names, counts and short references only. No listings, target source copies,
binary data, case reports or Ghidra projects are included. A case reference such as
`pm-fx-ambient-blind/F38` means the local case's frozen finding and its comparison; local files are not public dependencies.

This ledger splits compound statements into independently assessable claims. Definitions and proposals are evaluated
as definitions/recommendations, not counted as factual claims. Repeated factual claims are cross-referenced rather
than counted repeatedly. It covers §§1–3 and the factual context in the introduction and §§5–6; §4 has its own decision table.

| Claim outcome | Count |
| --- | ---: |
| confirmed | 45 |
| wrong / wording requiring correction | 8 |
| not checkable from the supplied record | 9 |
| Total | 62 |

“Confirmed” distinguishes source-confirmed implementation from recorded historical measurements. It does not imply
a new hardware test. “Not checkable” includes subjective or already-labelled assumptions, not just defects.
The eight corrections include summary/wording errors; they are not eight additional false DSP findings.

**MEASURED 2026-11-04 in this review:** arithmetic/count checks, immutable-file checks, archive-only manifest verification,
and the existing non-Ghidra test run. **NOT MEASURED:** target execution/audio, model reruns, decoder completeness,
new Ghidra behavior, or implementation effort. Effort estimates and proposed remedies below are reviewer judgments [A].

## 1. Claim-by-claim check

| ID | Draft location | Result | Assessment | Evidence |
| --- | --- | --- | --- | --- |
| C01 | §1 / L13 | confirmed | The first case's own-build, binary-analysis identity is recorded. | `pm-v010-binary/case.md`, Target and prior-exposure note; `comparison_vs_source.md` §1. |
| C02 | §1 / L13 | confirmed | It was not a clean blind test; earlier symbol exposure is explicitly disclosed. | `pm-v010-binary/case.md:27–33`. |
| C03 | §1 / L13 | confirmed | The reported 40-finding totals are 30 correct / 10 partly / 0 wrong. | `pm-v010-binary/comparison_vs_source.md` §2; historical grades, not regraded here. |
| C04 | §1 / L13 | confirmed | The board hypothesis was rejected separately from the finding totals. | Same comparison §2 and Q5; `case.md`, Open questions. |
| C05 | §1 / L14 | confirmed | Nebulae is a Linux/audio-engine/script case. | `nebulae-v2.1.2/case.md`, Target, boot chain and DSP reconstruction. |
| C06 | §1 / L14 | confirmed | A vendor MIT upstream exists; this does not establish package/upstream byte identity. | `nebulae-v2.1.2/case.md:33`; [vendor LICENSE](https://github.com/Qu-Bit-Electronix/QB_Nebulae_V2/blob/master/LICENSE), independently read. |
| C07 | §1 / L14 | confirmed | The cloud case was ultimately handed back as one archive. | `nebulae-v2.1.2/case.md:446–469`; archive inspected without extraction: 206 files / 31 directories, 205/205 listed hashes pass. |
| C08 | §1 / L14 | confirmed | No graded binary/source comparison is present for Nebulae. | `nebulae-v2.1.2/case.md`; findings/reconstruction are not an independent correctness score. |
| C09 | §1 / L14 | confirmed | Nebulae lessons reached main through PR #11. | Merge `d968af1`; changes `dcd1a06` and `e9f36ee`, including methods 01/02 and README. |
| C10 | §1 / L15 | confirmed | Step 6 is documented as an own-build, strictly blind analysis. | `pm-fx-ambient-blind/case.blind.md`, Target/rules/session log. Confirmed as the recorded protocol, not a forensic proof of everything the analyst ever saw. |
| C11 | §1 / L15 | confirmed | Frozen findings, Claude comparison and independent Codex assessment exist in the stated order. | Same case: frozen SHA-256, `comparison.md`, `comparison.codex.md`, independent snapshot/hash and logs. |
| C12 | §1 / L15 | confirmed | The final totals are 48 findings, 39 correct / 9 partly / 0 wrong, and 15 grouped misses. | `comparison.codex.md`, final result; `comparison.md:180–181`. |
| C13 | §1 / L15 | confirmed | The assessors ultimately agreed on every finding grade. | `comparison.md:167–181` accepts the remaining correction. The frozen initial tables intentionally retain their earlier differences. |
| C14 | §2 / L19 | confirmed | Import and analysis timings round to the values printed in the draft. | `pm-fx-ambient-blind/ghidra/l2a-imports.json`, timings. Saved measurements, not new timings. |
| C15 | §2 / L19–20 | confirmed | The query implementation reuses the saved project without import/analysis/save. | `src/l2a/cli.py:213–254`; `src/l2a/ghidra.py:136–150`; case query records. |
| C16 | §2 / L19–20 | not checkable | The universal claim about every historical query and no re-import cannot be fully audited from the selected records. | No complete immutable command history was supplied. The available import record/logs support ordinary reuse. |
| C17 | §2 / L21 | confirmed | Large-function output files and section-by-section examination are documented. | `pm-fx-ambient-blind/case.blind.md`, examined functions/session log; `comparison.codex.md`, command record; existing output files. |
| C18 | §2 / L21–22 | confirmed | The default is 60 lines; paging and full output are implemented. | `src/l2a/output.py:18,36–60`; `src/l2a/cli.py:246–251`. |
| C19 | §2 / L22 | not checkable | The default was 'never a blocker' is a retrospective experience claim. | No failure/effort accounting can establish that universal statement. Say no blocker was reported. |
| C20 | §2 / L23 | confirmed | The recomputation coefficient group contains 19 entries. | AST count of 19 top-level reporting calls in `pm-fx-ambient-blind/out/recompute.py`; 19 coefficient lines in `recompute.txt`. |
| C21 | §2 / L23–24 | confirmed | Delay-length, decay and damping calculations are present in addition to those entries. | `pm-fx-ambient-blind/out/recompute.py` and matching sections of `recompute.txt`. |
| C22 | §2 / L24 | wrong | 'No recomputed value turned out wrong' overstates what the log proves. | The same log has a mislabeled coefficient expression and a shifter-window calculation that omits the later rounding (F36). Some computed float words also differ from target words; no tolerance assertions are made. Numerical proximity is not semantic validation. |
| C23 | §2 / L24 | confirmed | The bend-scale check was absent from the recomputation script. | Read/AST inspection of `out/recompute.py`; F46 and both assessment notes. |
| C24 | §2 / L25–26 | confirmed | The model output contains the rounded estimate quoted in the draft. | `pm-fx-ambient-blind/out/tank_model.txt`, nominal/control runs. This is a saved model result, not a target measurement or a fresh rerun. |
| C25 | §2 / L25 | confirmed | The offline model implements the interpreted decay-gain law. | `out/tank_model.py`, `run()` gain calculation; original F32. This confirms model intent, not equivalence to executing the firmware. |
| C26 | §2 / L25–26 | not checkable | The complete causal explanation of the reported gap remains inferred; preserve the draft's explicit offline-model scope. | F32 explicitly leaves the explanation inferred; `comparison.codex.md`, limitations. Saved control runs support contributions within the model, not a complete causal proof or target observation. The draft does not explicitly claim a firmware measurement. |
| C27 | §2 / L26 | wrong | The reverb total 20/22 is stale. | Final ledger for F20–F41 gives **19 correct / 3 partly**. F29's accepted downgrade changes the earlier total. |
| C28 | §2 / L26 | wrong | 'The reverb core was the best-graded area' does not follow from final finding grades. | The core F26–F41 has 13/16 correct; wrapper F20–F25 has 6/6, generator F10–F19 has 9/10. The 22-row group combines wrapper and core; define a different metric explicitly if intended. |
| C29 | §2 / L27–28 | confirmed | Findings/snapshot hashes and sealed-reference identity checks were recorded. | `case.blind.md.sha256`, `codex-evidence/independent-assessment.sha256`, `comparison.codex.md`, provenance/binary checks. Frozen findings and review-prefix integrity rechecked here. |
| C30 | §2 / L27–28 | confirmed | The independent review records saving its grades before opening Claude's comparison. | `comparison.codex.md`, frozen boundary/command record; independent snapshot matches its prefix. This validates the documented handoff, not hidden cognitive history. |
| C31 | §2 / L28–29 | confirmed | The timer, clamp and unreachable-miss corrections were caught by different assessors. | `comparison.codex.md`, disagreement table; `comparison.md`, addendum. |
| C32 | §2 / L30 | confirmed | The board guess was explicitly tentative and also an open question. | `case.blind.md`, F42 Notes and Q9; earlier case Q5. |
| C33 | §2 / L30–31 | wrong | It did appear inside a finding row, although correctly marked tentative. | `case.blind.md`, F42 Notes. Replace 'never became a finding' with 'was not treated as a confirmed fact'. |
| C34 | E1 / L37 | confirmed | The literal-address interpretation error is documented and independently checked. | Step-6 F38/Q7; `comparison.codex.md`, binary spot checks. No target listing reproduced here. |
| C35 | E1 / L37 | confirmed | `consts` emits the first collected use and a multiplicity count. | `src/l2a/queries.py:198–230`, especially `where[0]` and `len(where)`. |
| C36 | E1 / L37 | confirmed | `disasm` adds no resolved data-reference annotation of its own. | `src/l2a/queries.py:139–163`; saved step-6 disassembly outputs. Ghidra may already render some operands as resolved addresses. |
| C37 | E1 / L37 | wrong | Hand calculation was not the only available route. | `xrefs` already enumerates references to an absolute literal (`queries.py:166–180`), and `consts` reports the literal address/content. Inline annotations improve convenience; the draft's necessity claim is false. |
| C38 | E2 / L38 | confirmed | The scale/range error and its missing recomputation check are documented. | F46; assessments and C23. The broader cause should be described as a missing verification step, not a measured account of attention. |
| C39 | E3 / L39 | confirmed | The observed VSEL/VRINTA decoding gap affects interpretation and decompiler output. | `case.blind.md`, tool note; saved `out/codex_sustain.txt`, `codex_pitch_window.txt` and corresponding independent decoder evidence. |
| C40 | E3 / L39 | not checkable | The broader VMAXNM assertion has not been independently demonstrated here. | The helper contains that decoding case, but its existence is not proof of a matching observed instruction or exhaustive Ghidra behavior. Restrict the factual claim to checked words. |
| C41 | E3 / L39 | confirmed | A case helper and GNU second-decoder evidence exist for selected affected words. | `out/fpv5_decode.py`; `codex-evidence/objdump-sustain.txt`, `objdump-window.txt`. Not a validation of every helper encoding. |
| C42 | E4 / L40 | confirmed | The listed role/transport interpretations were corrected by the comparisons. | Step-6 F47/F48; `pm-v010-binary/comparison_vs_source.md`, F38. |
| C43 | E4 / L40 | wrong | The blanket assertion that the findings did not say 'inferred' is inaccurate. | Step-6 F47 Notes already contain an inferred qualifier and F48 has a mixed observed/inferred level. The real omission is **claim-specific** qualification of the guessed role, not complete absence of an inference label. |
| C44 | E4 / L40 | not checkable | A single 'callee not decompiled' cause is not established for every example. | The comparison explicitly reports an unexamined callee in one example; that does not establish the same history for the table-role and earlier descriptor examples. |
| C45 | E5 / L41 | confirmed | The listed one-path data-flow interpretations were materially corrected. | Step-6 F44/F48; `pm-v010-binary/comparison_vs_source.md`, F25. |
| C46 | E5 / L41 | not checkable | Failure to inspect all readers as the historical cause cannot be independently reconstructed. | The corrections support incomplete tracing as a plausible mechanism; complete analyst activity/attention was not recorded. |
| C47 | E5 / L41 | confirmed | The earlier forward/backward tracing proposal was not added to method 07. | `pm-v010-binary/comparison_vs_source.md:164–166`; current `method/07_verification.md`; git history. |
| C48 | E6 / L42 | confirmed | The repeated board guesses use control-layout resemblance as their stated basis. | Earlier case Q5 and step-6 Q9/F42 Notes; their comparison corrections. Resemblance remains a hypothesis, not identifying evidence. |
| C49 | E7 / L43 | confirmed | Inactive capabilities were described while generator/exciter internals remained open. | Step-6 F35–F38, examined-functions table, Q1/Q2 and `comparison.codex.md`, miss list. |
| C50 | E7 / L43 | confirmed | M1–M5 are five of the 15 final grouped omissions concerning generator/exciter behavior. | `comparison.codex.md`, M1–M5/M15. These are semantic groups, not five functions or a completeness denominator. |
| C51 | E7 / L43 | not checkable | The claim that time followed the clearest structure is an unmeasured causal diagnosis. | No time-by-finding accounting exists in the supplied record. Mark it [A], while retaining the observed coverage imbalance. |
| C52 | E8 / L44 | confirmed | Initial RAM values were left open although the load image contained them. | Step-6 Q6; independent `binary-checks.txt` and `out/codex_startup.txt`. |
| C53 | E8 / L44 | wrong | Calling this startup source 'flash' is incorrect for the cited case. | The startup evidence and memory map identify the load-image source in SRAM. Say **load-image source / load address**, which may be RAM or flash. |
| C54 | E9 / L45 | confirmed | The assessors' timer, inactive-branch and reachable-count mistakes are recorded. | `comparison.codex.md`, post-freeze table; `comparison.md`, addendum. |
| C55 | E9 / L45 | wrong | A missing rule/definition is an inadequate statement of the demonstrated cause. | Both comparisons already state the strict no-false-detail rule; the Codex review also defines reachability. The observed problem was inconsistent enforcement. A dedicated aside/reachability checklist would still help. |
| C56 | §5 / L73–75 | confirmed | The named older documents are wholly or partly superseded. | Their opening notices; `README.md:31–32`. Preserve the distinction for the partly superseded risk document. |
| C57 | §5 / L74–75 | confirmed | The history document exists and moving the named files requires link updates. | `docs/history/CONCEPT_v0.1.de.md`; inbound references in README, concept, old brief and history document. |
| C58 | §5 / L76 | not checkable | Nothing in l2a looks unused is an assumption, not a measured usage result. | No per-command usage inventory was supplied. Retain [A]; do not delete commands on this basis. |
| C59 | §6 / L80 | confirmed | The step-5 Codex review was pending when this draft was written. | Roadmap step 5 at main `c52ed02`; this review now supplies it, without changing roadmap status. |
| C60 | §6 / L81–82 | confirmed | None of the three cases exercises a PE/VST3 target. | Both PM import records use raw Cortex-M; Nebulae has no Ghidra import. Confirmed within these three cases, not every possible local project. |
| C61 | §6 / L83 | not checkable | The unrecorded time/query/skill-usage quantities cannot be independently recovered. | The draft appropriately discloses this limitation; no performance or effort conclusion is derived from them. |
| C62 | Intro / L3–7 | confirmed | The draft proposes decisions without changing method, l2a or toolchain. | Pinned draft diff changes only `docs/STEP7_LOOKBACK.md` and the roadmap. Owner decisions remain open; case details are not copied. |

The corrected reverb total follows directly from the final grade list: **F20–F41: 19 correct / 3 partly / 0 wrong**;
**F26–F41 alone: 13 / 3 / 0**. These are finding counts, not measurements of algorithmic coverage or sound fidelity.
The earlier PM comparison also used “partly” for incompleteness in some rows; its totals are historical results,
not a directly comparable accuracy metric under the stricter step-6 rule.

## 2. Independent recommendation for every D item

Effort below means a reviewable change including appropriate checks, not just editing the main code path.
**S** is credible for each small method note. **M/L** estimates are assumptions; none was timed.
For every item: preserve case containment, target-data framing, pinned-tool rules, normal-user execution and the
separation of read-only `query` from project-mutating `open`. No workflow, toolchain or method change is adopted here.

| ID | Claude | Codex | Cause fit, realistic effort, simpler alternative and specific risk |
| --- | --- | --- | --- |
| D1 | Do; S | **Do, narrower; M for code** | Helps E1. First document existing `xrefs <literal-address>` for all uses; a second all-uses interface is convenience, not a missing capability. Annotate references Ghidra actually resolves: address, readable bytes/word, and an explicitly optional type interpretation. Do not call every referenced word a float. Account for width, endianness, uninitialized/unmapped targets and references outside the instruction body. Reuse `output.render/write_full` framing. No program mutation or new output-path escape. A bounded prototype might be S; the full “every reference” promise with checks deserves M. |
| D2 | Do; M | **Defer** | E3 is real, but textual annotation does **not repair Ghidra p-code or the decompiler**, and therefore does not by itself fix lost clamps or `fpops`. A tiny subset could be M; all listed forms, invalid encodings, registers, precision, architecture gating and conditions can be L. First use D3. Reconsider only demonstrated gaps that remain costly; cite primary encoding definitions and test both valid and rejected words. Keep raw bytes/original decode beside any annotation and label its scope. Avoid a second incomplete decoder presented as authoritative. |
| D3 | Only if D2 declined; S | **Do independently, before D2** | Directly supplies a second evidence path for E3, even if D2 is later implemented. Use the existing tool; pin version, executable/package identity and provenance deliberately, without silently installing/updating it. S for a record if provenance is available; allow M if verification is needed. Compare identical bytes with the correct ISA/mode/base and record command/version. A second decoder's output is target data and must not bypass framing or execute embedded text. No Ghidra extension is needed. |
| D4 | Do; S | **Do, with semantic checks** | Addresses E2. For material ranges/units/counts, record inputs, arithmetic, evaluation rate, float precision, clamping and integer rounding. Counts may come from a documented loop/layout calculation rather than a fabricated equation. D17 below closes the gap between a printed calculation and an actual check. Do not demand bit identity when an explicit, justified numerical tolerance is appropriate. Keep probes and target-derived output inside the case. |
| D5 | Do; S | **Do** | Addresses E4 if qualification is **per asserted role**, not a row containing several unrelated facts with a mixed label. Inspect the body or an independently verified signature/call contract; otherwise record the role as inferred and say what would decide it. Decompilation is not the only valid evidence: disassembly or trustworthy pinned source may suffice. Names/strings alone remain data. |
| D6 | Do; S | **Do as bounded tracing** | Addresses E5. “All readers and writers” cannot be promised by ordinary address xrefs with aliases, indirect calls and base-plus-offset accesses. Trace the relevant known paths, flag values, state changes, resets and writers; record unresolved aliases/readers explicitly. Current `q_xrefs` enumerates Ghidra references, not semantic whole-program data flow. S for this method note, not for an exhaustive analysis engine. |
| D7 | Do; S | **Do** | Helps E6. Control count/layout supports a hypothesis only. A string is also merely identifying evidence to corroborate against pin/peripheral setup or trustworthy provenance; a misleading string must not make a board identity “observed.” No new tool or hardware action is required. |
| D8 | Do; S | **Do, task-scoped** | Addresses the observed E7 coverage imbalance, not the unmeasured attention diagnosis. Prioritize reachable paths that answer the owner's question and their parameter routing. Generator/exciter coverage matters for an instrument-wide account; an effect-only brief must not silently expand into every generator kernel. One-line inactive capabilities are a good default, with explicit exceptions for an identified hypothesis or owner request. Preserve omitted work in a coverage list rather than erasing it. |
| D9 | Method now; helper later; S | **Do method; defer helper** | Addresses E8. Replace “flash source” with **load-image source / LMA**. Check source, destination, length, sections, alignment, endianness and copy bounds; distinguish initialized data from zeroed BSS and runtime state. Use ELF load information when allowed; raw-image startup tracing otherwise. Do not invent contents for an unmapped RAM block or modify the project just to display initial values. S for the note; no general startup-table parser is justified yet. |
| D10 | Do; S | **Do** | Helps enforce E9's already-applicable strict rule. Inventory factual subclaims and asides, including inactive branches, while reporting their practical reachability separately. Define “reachable” through a host path and available trigger; a callable library API alone is insufficient. Preserve tentative hypotheses as hypotheses. Keep misses grouped by stated criteria and show later corrections separately. S for a concise checklist/example. |
| D11 | Do as standard; S | **Do for formal blind comparisons; optional elsewhere** | Keeps the useful protocol, with explicit exceptions. A genuinely blind analysis needs an uncontaminated analyst from the start; a fresh assessor also needs an unanchored brief that excludes grading/status/log leaks until its own grades are saved. Freeze the findings and relevant verification artifacts, retain hashes, then append second thoughts. A hash proves file identity, not cognitive independence. Do not require a sealed answer key/second assessor for every ordinary source-assisted case. All frozen content stays outside git; no upload permission changes. |
| D12 | Do after D1/D2; M | **Defer until precisely scoped** | The need in E5/Q3 is supported, but syntactic offset matches are not object/field cross-references. Across functions, register reuse, aliases, scaled accesses, access widths and architecture differences make the stated semantics closer to L. A bounded read-only candidate scanner for one function/ISA could be M; label results as candidates and document false negatives. Try D6 plus a targeted disassembly search first. Never turn “no matches” into proof of no writes. No new project mutations. |
| D13 | Defer; M | **Defer** | The earlier case provides a real missing-function example, but step 6 adds no measured demand for automatic discovery. `disasm <address> --count <n>` is an existing inspection fallback. A literal that resembles an executable pointer is not necessarily code, especially in an executable raw-image block. M for a tightly constrained heuristic, M/L for reliable multi-format behavior. Any future creation belongs only in an explicit import/analysis transaction, with ISA/Thumb/bounds checks and rollback; never in query. |
| D14 | Defer; M | **Defer** | Helpful for flag provenance, but D6/D12 “cover most cases” has not been measured. Global store provenance is closer to L once aliases, stack state and control-flow merges matter; a narrow local backward slice could be M. Start with a recorded manual producer/consumer chain. Mark ambiguity rather than returning a unique origin without proof; keep the query read-only. |
| D15 | Defer; L | **Defer** | L is a credible lower bound for usable emulation with prepared memory, calling conventions, FPU/environment state, deterministic bounds and failure handling. The cases do not establish repeated need for a CLI wrapper. For a specific authorized question, start with a small case-local experiment and log it. Static-only case rules still prohibit target execution/emulation until that case's authorization changes; a new command must not widen those rules. |

**Recommendation differences:** D2 changes from do to defer; D3 becomes independent/prioritized; D12 changes from do to defer.
D6, D8, D9 and D11 retain useful work but need the narrower scope or corrected wording above.
Overall: **10 do / 5 defer / 0 drop** for D1–D15.

For §5, keep inactive-mode analysis brief by default and retain the unexamined work list. **Defer the optional history-file
move until the factual/method corrections are settled**, then use a separate small PR with link checks and clear current-document
pointers. Preserve the still-relevant risk information; do not archive a partly superseded file as if every issue were resolved.
There is no measured basis for deleting a query as unused. Step-8 target ordering remains the owner's decision.

## 3. Missing error patterns and additions

These are separate reviewer proposals. The cited evidence is case/repository evidence; the remedy and its priority are judgments.

| New pattern | Evidence | Implication / proposal |
| --- | --- | --- |
| E10: model consistency, causal explanation and target validation need distinct evidence levels | Step-6 F32 retains an inferred explanation; draft §2 places that explanation under [F]; model script/output and assessment limitations | Preserve the explicitly offline scope and qualify the causal explanation. Separate formula consistency, model behavior and firmware observation. **D18**. A self-consistent model can still omit relevant processing or use different arithmetic; the draft does not report an actual target measurement. |
| E11: printed recomputation is mistaken for a passed assertion; labels and downstream semantics can drift | Step-6 `out/recompute.py` / `recompute.txt`, coefficient labels, F36, and F46's absence | A similar coefficient is not proof of the published count/range or operation. **D17**. Do not silently equate a tolerance comparison with bit identity. |
| E12: summary counts/rankings drift after append-only corrections; historical grading criteria differ | Final F29 addendum versus draft §2; earlier PM comparison §2's incompleteness treatment | Derive summaries from the final ledger, state group boundaries and retain original counts as history. **D16**. Do not present cross-case counts as a measured improvement in accuracy. |
| E13: behavior was seen but not recorded, and therefore vanishes from coverage | `pm-v010-binary/comparison_vs_source.md:153,164–166`; step-6 examined-functions/miss lists | D6 adopts only one of the two earlier method suggestions. Record a short evidence-backed observation or open item immediately, even if interpretation is unfinished. **D19**. |
| E14: artifact integrity and the evolving working case are different states | Nebulae partial delivery/full-archive intake, later edited `case.md`, and step-6 post-freeze model-script correction noted in the comparison log | Preserve the immutable delivered/frozen artifact and its manifest; distinguish later working edits and script versions. Generalize safe intake to every archive/handoff. **D20**, also qualifies D11/D18. |

| New proposal | Codex recommendation | Smallest useful scope and cost [A] |
| --- | --- | --- |
| D16: summarize from a final grading/coverage ledger | **Do** | S method change: identify the final override set, count categories/groups once and label all subgroups. A small case-local count check suffices; no repository case database. |
| D17: make material recomputations decidable | **Do** | S method change: require an explicit pass criterion, matching label/expression, units/rate, tolerance or bits, and pre-/post-rounding count checks. Record unverified target words as such. Avoid a new general framework. |
| D18: state model validation/reproduction contracts | **Do** | S method note: archive script revision/hash, inputs/configuration, arithmetic precision, measured property/fit interval and output. State which target paths were omitted and whether comparison used an independent target/source execution. Do not claim target measurement from a local model. |
| D19: record seen behavior and unresolved consumers immediately | **Do** | S method note and a concise case coverage checklist; preserve a reference even before a full explanation is ready. Ownership/reachability and uncertainty remain separate. |
| D20: safe, immutable handoff intake | **Do** | S for guidance, not a new extractor: validate archive member types/paths and destination containment before extraction into an empty stage; reject links, absolute/traversal and Windows drive/UNC paths. Validate manifest paths as data, hash without executing delivered scripts, exclude the manifest itself from its own entries, and retain original archive/manifest separately from later working-case hashes. Keep licensing/upload rules unchanged. |

## 4. Step-5 skills review (separate from the draft review)

**Disposition: the review is now performed; the skills are useful guidance with corrections/gaps below.**
They are not yet a fully verified platform reference. The constants table passed; the strongest problems concern
tool guarantees and evidence handling. This PR records the review only: it does not silently implement changes,
mark owner acceptance, or alter roadmap step 5.

| File | Review outcome |
| --- | --- |
| `method/README.md` | Evidence levels, target-data treatment and compact-output policy are sound. Add the qualifications in S1/S12; generic pattern [A] does not override an actual case restriction. |
| `method/01_workflow.md` | Good basic workflow, version/ownership boundaries and resumption record. Correct/extend S1/S2/S9/S10. |
| `method/02_audio_path.md` | Useful embedded and Linux routes; shared-handler, polling-context, pointer-source and map qualifications in S3/S4/S7 are needed. Other-platform recipes remain hypotheses, not demonstrated case results. |
| `method/03_building_blocks.md` | Useful pattern inventory; S5/S6 clarify applicability and nonlinear domains. No case-specific reimplementation belongs here. |
| `method/04_constants.md` | **44/44** reference rows match independently reconstructed formulas rounded to float32; pointer-by-use guidance is valuable. Fix the completeness claim in S2; add D4/D17. |
| `method/05_reverb_delay.md` | Topology/sign/modulation checklist fits the cases. Add S7/S8; literature values correctly remain [A], and were not independently revalidated here. |
| `method/06_parameter_paths.md` | Backward tracing and rate-aware smoothing are useful. S8/D6 must explain indirect references, multiple writers, precedence and unresolved branches. |
| `method/07_verification.md` | Good numerical/structural checks and case-local model limits. S10–S12 and D10/D11/D17/D18 make confirmation and measurement boundaries explicit. |

| Skill issue | Classification / evidence | Required qualification or gap |
| --- | --- | --- |
| S1: import verification is overstated | Factual wording, `01_workflow.md:19–20`; `src/l2a/ghidra.py:175–194`, `vectors.py:35–58` | The checks establish that requested loader settings were applied and some structural conditions hold. They do not prove the user chose the correct base/architecture for the target. Say that explicitly; independently check vectors, mapped addresses and the actual execution path. |
| S2: `consts` is not every word read by the program | Factual wording, `04_constants.md:5,11–15`; `queries.py:192–230` | It uses Ghidra data references and scalar operands. Indirect loads, dynamic addresses, undecoded instructions and register-constructed values are not a complete data-flow enumeration. Document first-use/count output, the existing all-use xrefs route and these limits. This is not a new code bug. |
| S3: shared handlers and literal pointers are described too categorically | Factual precision, `02_audio_path.md:8–10,20–22`; `vectors.py:61–68`; saved PM IRQ evidence | Shared targets can retain a system-handler name; not every shared target is named `irq_shared_*`. The trampoline loads a RAM handle's **address from an image literal**, not necessarily a pointer stored in RAM. Keep pointer location, pointed-to object and callback storage distinct. |
| S4: control polling is not fixed to the main loop | Pattern qualification, `02_audio_path.md:35–36`; step-6 F9 and callback evidence | Controls may be updated in the audio callback while MIDI/state updates occur elsewhere. Trace the actual execution context, publication and ordering; label the current sentence as a typical arrangement, not a prerequisite. |
| S5: a recognizable arithmetic shape needs a stated variant | Pattern qualification, `03_building_blocks.md:11–15` | A tan-based SVF recipe describes particular formulations; it is not every two-state SVF. Butterworth Q examples depend on filter order/section. State the variant and confirm coefficient/state/sign relationships before naming an implementation. No new target claim is made from these patterns. |
| S6: polynomial clipping needs a domain | Mathematical precision, `03_building_blocks.md:51–52` | The cubic shown is not a global monotone saturator; clipping its output alone does not fix its reversal outside the intended input interval. State input-domain limiting and normalization. An independent arithmetic counterexample confirms this; it is not a defect demonstrated in a target. |
| S7: listed memory blocks are not a runtime allocation map | Gap, `05_reverb_delay.md:8–13`; `queries.py:80–92`; step-6 import/memory-map record | Raw imports may contain only the image. `info` lists mapped Ghidra blocks; external RAM, heap and buffers can remain unmapped. Infer allocations from code/layout and mark missing runtime state. Load-image initial values and current RAM contents are different evidence. |
| S8: address xrefs are not object-field or whole-flow proof | Gap, `06_parameter_paths.md:11–13`; `queries.py:166–180`; both PM comparisons | Multiple producers, base-relative accesses, aliases, resets, overrides and shared/per-voice routes require contextual tracing. Record update/smoothing rates and known/unresolved writers. An empty xref set cannot prove no writer exists; D12 must preserve that limitation. |
| S9: safe unpacking applies to returned archives too | Security/data-rule gap, `01_workflow.md:79–82` versus `02_audio_path.md`, Linux step 1; Nebulae intake log | Move/cross-link the existing pre-extraction path/type checks to the general handoff procedure. Include manifest containment and immutable-original versus working-state checks (D20). The reviewed archive passed the read-only checks; this is missing guidance, not a reported exploit. |
| S10: blind rules and library-version uncertainty must remain explicit | Rule precedence/gap, `01_workflow.md:5–10,63–67`; `07_verification.md:40–42`; earlier contamination disclosure and Nebulae Q1 | Make upstream/source lookup conditional on the case's source restrictions. Historical-release selection remains an assumed reference, not proof of the installed device version; existing inferred-for-device language is good. For formal blind review, also avoid status/log/brief anchoring until grades are frozen (D11). |
| S11: matching a coefficient does not identify an algorithm or measure its output | Evidence gap, `07_verification.md:7–9,19–25`; step-6 F32/F36/F46 | Separate observed bits, a derived numerical relationship, inferred interpretation, model observations and target measurements. Include rounding, clamp domain, update rate and an independent evidence path. A formula match alone must not promote the whole structure to confirmed. |
| S12: confirmation/coverage rules need subclaim and layer boundaries | Gap, `01_workflow.md:43–57`; `07_verification.md:38–48`; step-6 assessment/addendum | Apply the strict rule to factual asides and inactive branches, keep tentative hypotheses tentative, and define reachability before counting misses. Record seen/unexamined behavior promptly and scope coverage to the question. D8/D10/D19 address this without turning all generic guidance into mandatory exhaustive analysis. |

The float32 check used 44 independently constructed mathematical values, not just reparsing the table's decimal
column; all bit patterns matched. No wrong table entry was found. Generic DSP patterns and untested-platform
recipes remain [A]. This review does not claim that every ABI, peripheral layout, literature delay list or plugin
framework was independently validated. No reference library or target implementation is copied into the repository.

## 5. Commands, checks and publication boundary

Commands/checks completed on 2026-11-04:

| Check | Result |
| --- | --- |
| Git state and scope | Started on clean main `c52ed02`; created `codex/step7-lookback-review` from main. Read the remote-tracking draft with `git show origin/docs/step7-lookback-draft:docs/STEP7_LOOKBACK.md`; GitHub read-only PR metadata confirms head `e47f469`. No PR #13 mutation. |
| Rules/draft/method/code/case inspection | `Get-Content -LiteralPath`, bounded numbered Python reads, `rg -n/-C`, `rg --files`, `git log/show/diff`. Inspected query/output/import/vector code, relevant tests, guard and toolchain record. Case scripts were read/parsed, never imported or executed. |
| Arithmetic and ledger checks | Own Python using `math`, `struct`, `ast` and `re`: 44 semantic float32 table checks pass; 19 coefficient-report calls; final grade subgroup totals; frozen findings SHA-256 and independent-review prefix match. No new artifacts written into cases. |
| Archive-only verification | Own Python `tarfile/hashlib`: inspected member paths/types, hashed in-memory archive entries, no extraction. 206 regular files / 31 directories; 205/205 manifest hashes pass. This checks the archived delivery state, not the later edited working case. |
| Read-only baseline | Hashes of **72/72** selected case notes, verification outputs/scripts and import records remained unchanged. No case log added because this brief explicitly makes cases read-only. |
| `python -m unittest discover -s tests` | Exit 0: **60 discovered, 50 executed successfully, 10 Ghidra tests skipped** (1.023 s). Existing tests only; they do not establish new decoder correctness. |
| `python scripts/check_repo.py` | Required before commit, with the review staged: **repo guard: ok**. The guard checks tracked/indexed paths and sizes, not the semantic confidentiality of arbitrary Markdown; this review also receives a manual content check. |
| `git diff --check` and staged scope | Working/staged whitespace checks passed; only `docs/reviews/STEP7_LOOKBACK_REVIEW.md` is staged. No method/code/toolchain/workflow/draft/case artifact change. |

Two initial inspection commands needed correction: the draft has no local branch of that short name, so it was
read from `origin/docs/step7-lookback-draft`; a numbered console read encountered Windows output encoding and
was rerun with explicit UTF-8 output. Neither failure wrote a case or changed the draft. Large terminal reads
that were truncated were followed by targeted reads before assessing their contents. The first documentation
validation pass also needed an ID-pattern correction for titled D16–D20 rows and removal of an extra EOF blank
line; the final structural and whitespace checks passed after those corrections.

The publication is this review on its own branch/PR. No merge, owner decision, code implementation, new workflow,
tool installation, REA runtime or MCP registration is performed.

### What was not checked

- No new Ghidra import/query/integration run; saved evidence and current code decide the reviewed implementation claims.
- No target execution, emulation, build, hardware, audio/listening, spectral/T60/CPU measurement or case-model rerun.
- No exhaustive ARM-encoding audit, VMAXNM reproduction, other-platform/PE/plugin run or driver/ABI/peripheral verification.
- No reconstruction of complete historical query counts, private analyst attention, time per finding or skill-open telemetry.
- No regrading of every earlier PM/Nebulae finding or new upstream/package byte comparison. The upstream license check
  confirms the published license, not legal equivalence of every distributed byte.
- No measured implementation effort or complete alias/data-flow solution. Recommendations are proposals, not adopted changes.

## Owner decision summary

The claim ledger has **45 confirmed / 8 requiring correction / 9 not checkable** claims. Keep the useful method direction,
correct the summary/evidence overstatements, **defer D2 and D12**, and **do D3 independently of D2**.
The remaining D recommendations and scope qualifications are in §2. New proposals **D16–D20** cover final-ledger
summaries, decisive recomputations, model-validation contracts, immediate observation recording and safe immutable
handoffs. The separate step-5 review covers every method file and records 12 corrections/qualification gaps; the
44-entry numerical reference table passes. Owner acceptance and any implementation remain follow-up work.
