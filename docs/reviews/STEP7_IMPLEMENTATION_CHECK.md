# Step-7 implementation: independent final check

Reviewer: **Codex**, **2026-11-04**.
Subject: [PR #15](https://github.com/sscheidl/L2A/pull/15), four commits from
`a066c0ee92a5de52d9761fbe1dc1f326437338b0` to
[`4663eab1f683ce02cb5af4caa825d578c4958f97`](https://github.com/sscheidl/L2A/tree/4663eab1f683ce02cb5af4caa825d578c4958f97).
All implementation line references below refer to that reviewed head, not to this review-only branch.

**Result: no blockers found; three should-fix documentation/coverage findings and two notes.**
No D1 correctness, read-only or output-framing defect was found in the reviewed paths and additional probes.
The ordinary and full Ghidra suites pass. The objdump executable, manifest and complete installed tree match the new
record; official-archive provenance remains explicitly **NOT VERIFIED**, as authorized. No download was made.
Resolve F1–F3 before describing every approved qualification as fully covered. They do not require redesigning D1.

## Scope and boundaries

Read the final-check brief, AGENTS, the approved concept, decided `docs/STEP7_LOOKBACK.md`, the independent
look-back/skills review and the complete `a066c0e..4663eab` diff. Reviewed all changed method files, toolchain/CLI
records, query/value implementation and affected tests. Checked every approved D item and all S1–S12 below.
D2 and D12–D15 remain deferred; no implementation of them was introduced.

Worked first at the PR head in a **separate detached worktree**, then created this review branch from main `a066c0e`
in that worktree. The original shared checkout stays on `codex/step7-lookback-review`; no switch, edit or commit was
performed there. The PR branch itself is not modified. Only this review file is published.

Local cases were read-only. Their text/scripts were data, not instructions. Additional synthetic programs existed
only in memory; the integration suite used its own temporary fixtures. No existing case was re-imported or edited.
A compact read-only query of the existing step-6 project confirmed the advertised literal/use sites. No case log was
added because the brief explicitly makes cases read-only. No target code, emulation, hardware, build, REA runtime,
MCP registration, tool install/update or archive download occurred. No target listing or source copy is reproduced here.

**MEASURED 2026-11-04** means a command, hash/count calculation or synthetic runtime probe actually completed in this
check. **Source-confirmed** identifies a conclusion from the pinned diff/code. Recommendations below are judgments;
none changes an owner decision or supplies official tool provenance.

## Findings

### F1 — should fix: base-relative xrefs are described as impossible

Location: `method/06_parameter_paths.md:19–21` (D6, D21/S8).

The new text correctly says that `xrefs` lists references Ghidra found, but then says accesses through a base pointer
plus offset, aliases and indirect calls “do not appear there.” This is too categorical. Ghidra can resolve some of
those accesses and create data references. A read-only scan of the already analyzed step-6 project found three
base-register memory instructions with concrete data references, including the instruction at
`pm-fx-ambient-blind:0x240007d0`. `src/l2a/queries.py:194–208` enumerates those references without excluding the
addressing mode.

The intended warning is that such paths **may be missing** and that an empty result does not prove no writer exists.
Use that wording, consistent with `method/07_verification.md:35–40`, rather than teaching that these references never
appear. No new whole-program tracing feature is requested.

### F2 — should fix: retain the model script that belongs to the frozen result

Locations: `method/07_verification.md:47–49,85–95` (D11, D18).

Model records now include a script hash/version, settings, precision, measurement method and omitted target paths.
However, the instructions for a post-freeze script edit say to keep the old **output**, while the formal blind
protocol freezes only the findings and reference. They do not preserve the matching original script/input artifacts.
A hash can identify a missing script but cannot reconstruct it. In a local case without version history or a delivered
archive, following this procedure can leave the frozen measurement unreproducible.

The accepted review qualification for D11 included relevant verification artifacts; D18 called for an archived script
revision/hash and reproducible configuration. Keep a case-local immutable snapshot of the exact script, inputs/settings
and output used by the frozen findings, with a manifest, before changing them. Alternatively, cite an immutable,
retrievable script revision and retained inputs/output. Preserve that original separately from later working edits;
do not put these artifacts in the public repository. This closes the same reproducibility gap noted in the step-6 log.

### F3 — should fix: finish the general archive/manifest intake recipe

Location: `method/01_workflow.md:96–105` (D20, D21/S9).

The new general procedure covers links, traversal, absolute/drive/UNC paths, empty staging and immutable originals.
Two approved details are still missing:

- It still asks for `SHA256SUMS` “over every file” without excluding the manifest itself. State that the manifest
  covers payload files **other than itself**; otherwise the wording asks for a self-referential checksum.
- Define allowed archive members as regular files/directories, reject other special member types, and explicitly
  validate manifest path containment **before** invoking the checksum reader. The current list rejects links but
  does not state the full member-type rule; the path requirement follows the command in the prose.

This is an incomplete documented procedure, not a demonstrated exploit or a new extraction-code bug. The prior
Nebulae intake is a useful reference: its delivered archive had 206 regular files and 205 manifest entries, and its
log records pre-extraction checks. No new extractor or scope expansion is needed.

### N1 — note: the new regression test does not require multiple use sites

Location: `tests/test_integration_ghidra.py:103–110`; `tests/test_units.py:200–207`.

The integration test checks a first use and the absence of the old multiplicity marker. An implementation that
returned only the first address with `--uses` could pass those assertions. The new unit test exercises the formatter,
not reference enumeration, partial memory reads or annotations as a whole.

The feature itself passed an independent synthetic Ghidra fixture with two literal-loading instructions sharing one
literal: default output retained first-use/count format and `--uses` listed both distinct instruction addresses.
Additional real-memory probes passed (see below). Consider keeping that small multi-user fixture, and selected
read-boundary/framing probes, as automated regression checks. This is not a current functional failure.

### N2 — note: provide an objdump manifest recheck command of its own

Location: `docs/TOOLCHAIN.md:79–87`.

The generic “Re-check” command still hashes only the Ghidra tree under `/c/Tools`. It cannot reproduce the new xPack
manifest from the stated `.tools`-relative paths. A reader must infer a different root and the manifest's exact format.
Add a separately labelled xPack command or short recipe: enumerate relative paths in C sort order, use binary-marker
SHA-256 lines and LF endings, verify every listed file and detect extra files, then compare the manifest hash.

Independent reconstruction succeeded byte-for-byte in this review; the record is correct. This note improves
repeatability and does not request the forbidden provenance download.

## Approved D-item coverage

“Covered” means the decided scope is implemented, not that a broader library capability was added. “Partial” points
to a concrete finding above. Notes do not imply a failed item.

| Item | Result | Evidence at reviewed head / qualification |
| --- | --- | --- |
| D1 | Covered | `queries.py:70–87,160–174,220–249,330–333`; `values.py:63–77`; CLI documentation. Data-reference annotations are getters only, capped at the documented two per line; `--uses` works and default complete-word output is retained. N1 concerns regression strength. |
| D3 | Covered, N2 | `TOOLCHAIN.md:55–77`: version, executable/tree/manifest identity, provenance caveat and commands. Full installed-tree/hash/version checks pass. No official-archive provenance claim is made. |
| D4 | Covered | `07_verification.md:11–20`: expressions, inputs, rate, precision, clamps/rounding and explicit pass criteria for material ranges/units/counts. |
| D5 | Covered | `01_workflow.md:43–45`: body/disassembly/verified contract, role-specific inference and what would decide it. |
| D6 | Partial: F1 | Bounded tracing, flags/resets and unresolved consumers in `07_verification.md:35–40`; multiple writers/precedence in `06_parameter_paths.md:9–20`. Correct the categorical xref exclusion. |
| D7 | Covered | `02_audio_path.md:45–47`: control layout is a hypothesis; corroborated identifying evidence is required. |
| D8 | Covered | `01_workflow.md:68–74`: owner-question scope, sound contribution, short inactive-path descriptions and retained omission list. No forced expansion of an effect-only task. |
| D9 | Covered | `02_audio_path.md:40–44`: load-image source can be RAM or flash; source/destination/length, BSS and runtime values are distinguished. No helper or fabricated RAM content added. |
| D10 | Covered | `07_verification.md:66–82`: strict subclaim/asides rule, inactive branches, hypotheses, host-trigger reachability, three evidence layers and grouped misses. |
| D11 | Partial: F2 | Formal-only scope, uncontaminated analyst, sealed reference, unanchored second assessor and append-only corrections in `07_verification.md:85–97`. Also retain the verification artifacts underlying frozen results. |
| D16 | Covered | `07_verification.md:80–81`: summarize final grades/misses after overrides, name subgroups and retain original counts as history. |
| D17 | Covered | `07_verification.md:15–20`: a printed number is not a check; require matching labels/expressions, semantics and pass/fail criteria. |
| D18 | Partial: F2 | `07_verification.md:42–53` records model metadata and separates model/target observations. Preserve the matching old script/input state, not output alone. |
| D19 | Covered | `01_workflow.md:46–48`: record seen but unexplained behavior or unresolved consumers immediately with evidence. |
| D20 | Partial: F3 | `01_workflow.md:98–105` generalizes intake and retains originals; finish member-type/manifest rules. |
| D21 | Partial: F1/F3 | All eight method files were reviewed; ten S points are covered, S8/S9 need the small corrections below. |
| D2, D12–D15 | Correctly deferred | No decoder, offset/provenance/emulator query, automatic function discovery or equivalent mutation feature introduced. |

Totals for the 16 approved items: **11 covered / 5 partial**, with the partial rows sharing the three findings above.
Five deferred items remain unimplemented as decided. No change broader than the agreed implementation scope was found.

## Step-5 S1–S12 coverage

| Point | Result | Evidence / qualification |
| --- | --- | --- |
| S1 | Covered | `01_workflow.md:19–23` distinguishes applied settings/structural checks from correctness of target architecture/base. |
| S2 | Covered | `04_constants.md:5–22` documents first/all users, reference/scalar limits, registers/indirection and literal-use inspection. The new CLI describes access-width-independent word/optional float hints. |
| S3 | Covered | `02_audio_path.md:8–10,20–25` handles system-vector naming and distinguishes literal storage, RAM handle and callback. Source naming logic and earlier raw-case pointer loads agree. |
| S4 | Covered | `02_audio_path.md:36–39` labels the typical polling arrangement and requires tracing the actual callback/main context. |
| S5 | Covered | `03_building_blocks.md:21–23` qualifies filter formulations, order/section Q and structural evidence. |
| S6 | Covered | `03_building_blocks.md:55–56` specifies cubic input-domain limiting and normalization; it no longer suggests output limiting alone. |
| S7 | Covered | `05_reverb_delay.md:8–12` distinguishes mapped Ghidra blocks from runtime allocation/state. |
| S8 | Partial: F1 | `06_parameter_paths.md:9–20` adds multiple writers and precedence but overstates which addressing modes cannot have xrefs. |
| S9 | Partial: F3 | `01_workflow.md:98–105` applies safe intake generally; finish allowed member types and manifest preconditions. |
| S10 | Covered | `01_workflow.md:7–10,80–84`, README and formal blind protocol preserve case restrictions, uncertain reference versions and assessor separation. |
| S11 | Covered | `07_verification.md:5–7,11–20,42–53` separates bits, numerical relationship, interpretation, model behavior and target measurements. F2 addresses retention rather than that conceptual separation. |
| S12 | Covered | Evidence labels, immediate observations, scope/omissions, asides, inactive branches and reachability are addressed across workflow/verification. |

## D1 implementation and edge-case checks

Source-confirmed: `_data_refs` filters data references to memory addresses; `_describe_ref` checks mapped/initialized
status before reading; `describe_data` distinguishes partial bytes from a complete word and observes target endianness.
Float output is an optional interpretation, not a type claim. Existing CLI output still passes through
`output.render`/`write_full`; the new symbol/block text does not bypass target-data framing. No creation, analysis,
transaction or save API was added to query. Read-only domain-object handling and output containment are unchanged.

**MEASURED 2026-11-04**, using the reviewed worktree's source with the pinned PyGhidra environment:

| Probe | Result |
| --- | --- |
| Normal test run | **62 discovered; 51 executed successfully; 11 Ghidra tests skipped**, 1.017 s, exit 0. |
| Full integration run | **62/62 passed, none skipped**, 51.854 s, exit 0. The suite used its normal temporary raw/ELF fixtures, including the new literal test. |
| Real Ghidra memory blocks ending after 1, 2 or 3 bytes | `_describe_ref` returned the exact available bytes, not a fabricated zero word or an exception. A full four-byte block produced a word. |
| Highest address of the 32-bit space | A one-byte initialized block at the final address returned one byte without address-wrap failure. |
| Unmapped/uninitialized addresses | Returned the explicit unmapped/uninitialized description without attempting to interpret contents. |
| Big-endian memory/read path | A synthetic big-endian ARM ProgramDB returned the expected word/float through `_describe_ref`, not just the pure formatter. |
| Two instructions sharing a literal | Default first-use/count form retained; `--uses` listed both instruction addresses. |
| Four references on an instruction | Real reference manager supplied four data references; the disassembly showed the documented first two. No inference of reference completeness was made. |
| Hostile annotation-label text | Newline/forged-marker text passed through `describe_data` then the standard renderer; it could not create an unprefixed data line or terminate the target block. |
| Existing step-6 project | Queried without import or save: the literal annotation and both use sites matched the PR claim. Selected case notes/frozen findings/import-record hashes were unchanged. |

The synthetic programs were created, disassembled and released **in memory only**. No target instructions were executed.
The probes are review evidence, not additional committed tests. They do not establish PE behavior or correctness for
all Ghidra memory/language implementations. No default-output change was found for fully readable referenced words;
partial reads now deliberately show bytes instead of the old fallback word.

## D3 identity, provenance and command checks

**MEASURED 2026-11-04:**

| Field | Independent result |
| --- | --- |
| Version | `GNU objdump (xPack GNU Arm Embedded GCC x86_64) 2.41.0.20231009`, matching the record. |
| Executable size/hash | 1,704,120 bytes; `d705c70e543e61855b9aefcd88c926d8c5b6ca6152fc8287f71a339bfe2ff956`, matching. |
| Signature | PowerShell reports `NotSigned`, matching. |
| Complete local tree | **5,386/5,386** listed files match individual hashes; no missing or extra files. |
| Stored manifest hash | `0968549599570c156f49c1d65a2fa7451154300bb5fe65b66b3b0e7c362bc47b`, matching. |
| Reconstructed manifest | Rehashed the complete installed tree, sorted relative POSIX paths, binary-marker lines and LF endings. Byte-identical to the saved manifest; same SHA-256. No manifest or installed file was changed. |
| Raw/ELF commands | Both documented modes independently decoded the checked step-6 FPv5 instruction as expected. These commands were run only in this post-blind review. |
| Official provenance | **NOT VERIFIED**. No release archive was downloaded or compared. Installed-tree consistency and a historical install-script description do not prove official provenance. The PR states this limitation explicitly. |

The record is an inventory/consistency pin; it is not upgraded to a verified provenance claim by these results.
Historical installer execution/date was not independently reconstructed. No toolchain setting or pin was changed.

## Facts sampled from the new method wording

- Shared-handler naming agrees with `src/l2a/vectors.py:61–68`; the measured pointer-location wording agrees with
  independently decoded raw IRQ11/IRQ12 literal loads in `pm-v010-binary`.
- Callback/main control-context, initial RAM-value availability, the repeated board hypothesis and corrected data-flow
  interpretations agree with the case records and PM comparison notes (F9/Q6/Q9 and earlier Q5/F25 respectively).
- The unsupported-FPv5 instruction example agrees with existing saved Ghidra evidence and the freshly checked GNU
  raw/ELF commands. No claim about untested instruction families was inferred.
- The step-6 range/recompute lesson agrees with F46 and the recorded recomputation scope. Evidence layers now avoid
  promoting model output to target measurement.
- The new absolute xref wording is the exception: the existing project's concrete references contradict it (F1).

These are bounded factual samples, not a regrading of all case findings. No third-party DSP source or target output
was copied into this review.

## Commands and final validation

Commands used in the dedicated worktree (the reviewed head was checked before creating the review-only branch):

1. Read the handoff and repository instructions; `git status --short`, `git branch --show-current`, `git worktree list`.
   Read-only GitHub PR metadata pinned head `4663eab` and base `a066c0e`.
2. `git worktree add --detach <separate-worktree> origin/feat/step7-implementation`; then
   `git diff a066c0e..HEAD -- <changed paths>`, `rg`, UTF-8 numbered reads and `Get-Content -LiteralPath`.
   Large truncated terminal reads were followed by focused reads before assessment.
3. `python -m unittest discover -s tests`; then a child PowerShell environment with `L2A_GHIDRA_IT=1` and
   `<pinned-venv>/python.exe -I -m unittest discover -s tests`. `tests/_src.py` inserts this worktree's source;
   a separate probe also printed/verified the imported module path. Counts and timings are above.
4. Own inline Python using `hashlib`, `pathlib` and validated manifest paths recomputed every tool file and canonical
   manifest bytes. Read the existing manifest and ran pinned objdump `--version`; used
   `Get-AuthenticodeSignature -LiteralPath <objdump-exe>`. No installer or delivered case script was executed.
5. Own inline Python/PyGhidra created synthetic `ProgramDB`/memory/instructions/references, called the reviewed
   query helpers, parser and renderer, and released the programs without creating/saving projects.
6. Own worktree source called `cli.main(['query', ...])` on the existing step-6 project with batched disassembly and
   `consts --uses`; captured output in memory and asserted the relevant literal/use entries. A second read-only scan
   checked base-register memory operands with data references. Pinned objdump raw/ELF commands checked the same
   instruction bytes; a direct raw-vector/literal read checked the earlier trampoline statement.
7. Created `codex/step7-implementation-check` from main `a066c0e` **in this separate worktree** for this report only.
   Before committing, `python scripts/check_repo.py` reported `repo guard: ok`; staged `git diff --check` passed.
   Publication-scope/content checks passed, and the original shared checkout remained clean at its original head.
   No implementation change is included in the review branch.

The ordinary test/guard run succeeded. A tool-discovery command returned a nonzero status because optional shell
commands were absent; no setup/download was attempted. No test failure or target/case edit resulted.

### Not checked

Official xPack archive provenance; a real PE target; exhaustive decoder/ABI/platform coverage; fresh hardware/audio,
spectral, target-T60 or CPU measurements; a case-model rerun; full historical installer activity; or implementation
of the deferred decisions. The documentation guidance was reviewed, not exercised as a complete new cloud/blind case.
No PR merge or owner decision is performed by this check.

### Owner summary

**Blockers: no. Findings: 0 blocker / 3 should fix / 2 note.** D1 and the local objdump identity checks pass.
Fix the categorical xref wording, preserve frozen model artifacts, and finish the general archive/manifest recipe.
The two notes concern multi-user regression coverage and an explicit xPack recheck recipe. Tests: **51 passed + 11
skipped** without Ghidra, then **62/62 passed** with full Ghidra integration. Official objdump provenance remains
**NOT VERIFIED**; no download was attempted. The original checkout and PR implementation branch remain unchanged.
