# Decision matrix: REA take over / adapt / add / omit

> **Superseded** by [REA_Architecture_Review.md §5](REA_Architecture_Review.md) (2026-11-03). Kept for traceability.

Labels: **[C]** confirmed in REA source at `4b961e3` ([review](REA_STATIC_REVIEW_4b961e3.md)),
**[A]** assumption, **[D]** proposal for the owner.

| REA component | Decision | When | Rationale |
| --- | --- | --- | --- |
| Evidence vocabulary (`confidence`, `authority`, limitations, locations) | **Take over (as data model, not code)** | v0.1 | Fits v0.1's "proof vs assumption" requirement exactly [C]. Reimplemented as a small JSON Schema, with MIT attribution |
| Residual-unknowns ledger (status, supporting/contradicting evidence, verified resolution) | **Take over (simplified)** | v0.1 | Same reason. Hash chains and content addressing omitted in v0.1 |
| "Untrusted content" marking of target-derived text | **Take over (idea)** | v0.1 | Prompt-injection defence for decompiler and string output [C] |
| Ghidra headless pattern (temporary project, private HOME/TEMP, `-readOnly`, bounded heap) | **Adapt (idea)** | v0.1 | Good isolation hygiene [C]. L2A applies it in its own launcher; REA's code is not copied |
| Ghidra lane on Windows for raw/ELF Cortex-M | **Omit, cannot be used** | – | Refused on Windows; raw Thumb/Cortex-M unsupported everywhere [C] |
| Own Cortex-M import (vector table, base address, memory map, Thumb) | **Add (L2A)** | v0.1 | Real gap [C]; small Ghidra script |
| DSP constant/table scanner (float32/Q15/Q31, known constants, table shapes) | **Add (L2A)** | v0.1 | Real gap: REA has only masked byte search [C] |
| Per-function instruction-mix metrics (FPU/DSP density → audio hotspots) | **Add (L2A)** | v0.1 | Not in REA [C]; cheap, high value for finding the audio path [A] |
| DSP analysis method / agent instructions | **Add (L2A, own text)** | v0.1 | REA's skill is generic and recommends unpinned `npx @latest` [C] |
| REA CLI (`--json`) for Windows PE audio plugins (VST3/CLAP/AAX `.dll`) | **Adapt later** | Phase 3, on demand | Works on Windows [C]; no concrete case yet. Requires the conditions in SPEC §6.4 |
| REA MCP server (~234 tools) | **Omit in v0.1** | Phase 3 earliest | Large tool and permission surface; no read-only mode [C]; CLI + JSON files suffice |
| `rea setup`, plugin manifests, shipped skills | **Omit** | – | Edit global agent configs and install agent instructions [C] |
| Firmware container parsers (HEX, S-record, UF2, DfuSe, ESP, uImage/FIT) | **Omit in v0.1** | Phase 3 if needed | Useful [C], but Intel HEX → bin is trivial; other formats have no case yet |
| Binwalk / Unblob | **Omit** | – | Linux-only in REA [C] |
| Frida, LLDB, GDB, Rizin, browser/Electron/Android/pcap/EVM/… families | **Omit** | – | Executes targets [C] or out of scope |
| Hopper, IDA, JEB, Kuna providers | **Omit** | – | Commercial or out of scope; Ghidra alone suffices [C] |
| Fork of REA (Variant B) | **Reject** | – | Churn and size [C]; we would use a tiny fraction [A] |
| Extension of REA (Variant A) | **Not possible** | – | No public API or plugin loader [C] |
