# Case: <short name>

> **The working memory of this case.** Read it first when starting or resuming, whether in Claude or Codex.
> Update it at the end of every work step. Raw tool output goes into separate files in this folder;
> this file holds the conclusions and the addresses that lead back to them.
> This file and the whole case folder stay local and never go into a git repository.

## Status

* **State:** open | in progress | paused | done
* **Last updated:** YYYY-MM-DD by <Claude | Codex | owner>
* **Next step:** <one or two sentences that a fresh session can act on immediately>

## Target

| Field | Value |
| --- | --- |
| File(s) | `target.bin` … |
| SHA-256 | |
| Source / provenance | own build at commit … / vendor download URL / … |
| Platform | for example Daisy Seed3 (STM32H750, Cortex-M7) |
| Ghidra import | loader, language, base address, extra regions |
| Licence and legal note | own code / open source (licence) / third party: legal basis noted by the owner |
| Tools | Ghidra 12.1.4, JDK 21.0.12, L2A version … |
| Rules for this case | for example "do not consult original sources" |

## Findings

Every finding cites binary evidence. Levels: **observed** (seen directly), **derived** (follows from observed facts),
**inferred** (plausible, not yet proven).

| # | Finding | Level | Evidence (address / function / instruction / constant) | Notes |
| --- | --- | --- | --- | --- |
| F1 | | | | |

## Examined functions

| Address | Our name | Role | Status | Notes / output file |
| --- | --- | --- | --- | --- |
| `0x…` | `audio_callback?` | | examined / partly / to do | `out/decomp_0x….c` |

## Important addresses and memory map

| Address / range | What | Evidence |
| --- | --- | --- |
| `0x…` | vector table / audio buffer / delay line / parameter struct | |

## Constants and tables

| Address | Type and length | Value or shape | Interpretation | Level |
| --- | --- | --- | --- | --- |
| `0x…` | float32 × 1 | 48000.0 | sample rate | observed |

## Open questions and hypotheses

| # | Question / hypothesis | What would decide it | Status |
| --- | --- | --- | --- |
| Q1 | | | open / resolved (→ F#) / dropped |

## Session log

Newest entry first. Note what was done, what was deliberately skipped, and any dynamic runs.

### YYYY-MM-DD – <Claude | Codex | owner>

* Done:
* Skipped or not checked:
* Dynamic runs (what, where, as which user):
