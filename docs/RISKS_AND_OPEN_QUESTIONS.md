# Technical risks and open questions (prioritised)

> **Partly superseded** (2026-11-03): the owner answered Q1–Q3 and Q5 (see [L2A_Concept_v0.3.md §1](L2A_Concept_v0.3.md)), and the remaining risks are carried into v0.3 §5–6. Kept for traceability.

Labels: **[C]** confirmed in REA source at `4b961e3`, **[A]** assumption.

## Risks

| # | Risk | Severity | Basis | Mitigation in v0.2 |
| --- | --- | --- | --- | --- |
| R1 | **Proprietary code leaves the machine through the AI agent's provider.** Decompiled firmware shown to Codex, Claude or GPT is sent to the respective cloud service | High | REA returns data to the client [C]; provider behaviour [A] | `ai_egress` per case (none / summaries / full); tools enforce it (SPEC §6.2) |
| R2 | **Public repository.** `sscheidl/L2A` is public; one careless commit publishes a target or a dump | High | Repo visibility (checked 2026-11-03) | Cases outside the checkout, `.gitignore`, a test that fails on tracked binary/dump files |
| R3 | **v0.1 assumption failure: REA does not support the main target.** Windows rejects ELF and raw ARM; raw Thumb/Cortex-M unsupported everywhere | High (already materialised) | [C] | Architecture switched to Variant C around stock Ghidra |
| R4 | **Prompt injection from analysed bytes.** Strings, symbols and comments in firmware or plugins reach the agent context | Medium | REA marks such content as untrusted [C]; the attack itself [A] | Untrusted marking in exports; agent instructions treat exports as data; no tool that acts on export content |
| R5 | **Parser and decompiler exploits.** Ghidra and the JDK parse hostile files with the user's rights; "not a sandbox" | Medium | REA `SECURITY.md` [C] | Separate Windows user or Windows Sandbox for vendor files; pinned, hash-checked Ghidra and JDK |
| R6 | **Supply chain if REA is ever installed**: unpinned `npx @latest` in REA docs and skill, prebuilt native addon with a self-referential hash, Frida install-time download | Medium (Phase 3 only) | [C] | No REA in v0.1; Phase 3 conditions in SPEC §6.4 |
| R7 | **Legal basis for decompiling proprietary software.** Private or scientific interest is no blanket permission (v0.1 §6) | High, per case | [A], not legal advice | Owner records the legal basis per case before analysis; nothing proprietary in Phase 2 |
| R8 | **False confidence.** Plausible but wrong reconstructions (for example a misread filter topology) recorded as fact | Medium | [A] | `observed` requires a tool evidence location; `inferred` is the default; Phase 2 measures wrong "observed" claims |
| R9 | **Clean-room contamination.** Decompiled code flows into the "independent" spec or a later implementation | Medium | [A] | No listings in specs; reimplementation from spec in a separate session (SPEC §6.6) |
| R10 | **Ghidra Cortex-M quality.** Thumb-2 FPU code with literal pools, inline tables and `TBB`/`TBH` jump tables may decompile poorly; DSP loops are often unrolled or CMSIS-DSP-optimised | Medium | [A] | Measured in Phase 2 on our own binary before any real case |
| R11 | **Scope creep from v0.1's long DSP list** (granular, pitch shifting, reverb …) | Low/Medium | – | These stay analyst knowledge in the method document, not tools |

## Open questions for the owner

| # | Question | Why it matters |
| --- | --- | --- |
| Q1 | Approve Variant C and the decision "no REA runtime in v0.1"? | Changes v0.1's core assumption |
| Q2 | Which agent may see which data class: is `ai_egress: none` the default for proprietary targets? | R1; determines how useful agents are on real cases |
| Q3 | Which environment isolates the analysis: separate Windows user, Windows Sandbox, or a VM/WSL2? | R5; WSL2 would also allow the REA ELF lane later [C: POSIX only] |
| Q4 | Which Ghidra and JDK versions are pinned (REA verified Ghidra 12.1.4 and JDK ≥ 21 [C])? Is Ghidra already installed, and from where? | Reproducibility and provenance |
| Q5 | Phase 2 target: is a DaisySP-based test firmware (biquad, oscillator, delay, LFO) acceptable, and who builds and seals the answer key? | The test must be blind to the analysing session |
| Q6 | Is AMYboard in scope at all, and on which CPU? [A: ESP32-S3/Xtensa, unverified] | Decides whether Xtensa support is ever needed |
| Q7 | Does a real first case exist yet (hardware firmware or a VST3 plugin)? | Phase 3 REA adapter only makes sense with a PE case |
| Q8 | Which German legal framework applies per case (for example the decompilation and observation provisions of the UrhG for computer programs and licence terms)? This needs the owner's or a lawyer's assessment | R7; black-box observation/measurement (the deferred Audio Lab) may be the legally simpler route [A] |
| Q9 | Where should private cases live: `../L2A-cases/` local only, or a separate **private** GitHub repository? | R2; backups |
| Q10 | German translation of these documents wanted (secondary, per the English-first rule)? | Documentation effort |
