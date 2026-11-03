# L2A – Listen to Anything

An evidence-based analysis platform for music software, synthesizer and effects firmware, and DSP.
Example targets: Daisy Seed3, AMYboard, VST3 plugins, Korg logue SDK units.
L2A uses static and, where needed, dynamic analysis. It documents algorithms as **independently written specifications**.
Principle: *understand, don't copy*.

L2A only analyses. It does not develop synthesizers, effects or firmware; implementations happen in other projects.

**Status: concept, no implementation yet.** Nothing in this repository has been approved for
implementation. Hardware and listening results are NOT MEASURED.

> [!WARNING]
> This repository is **public**. It holds only L2A's own code, schemas and documentation.
> Proprietary binaries, decompiler output and case results are never committed; cases live
> outside the checkout (see [concept §5](docs/L2A_Concept_v0.3.md#5-security-pragmatic)).

## Documents

| Document | Content |
| --- | --- |
| [L2A_Concept_v0.3.md](docs/L2A_Concept_v0.3.md) | **Current** consolidated concept: PyGhidra architecture, target platforms, MVP scope, DSP skills, security, resource efficiency, test strategy |
| [REA_Architecture_Review.md](docs/REA_Architecture_Review.md) | REA functions and interfaces versus existing tool APIs; selective adoption |
| [L2A_Implementation_Roadmap.md](docs/L2A_Implementation_Roadmap.md) | Small step plan (8 steps) |
| [REA_STATIC_REVIEW_4b961e3.md](docs/REA_STATIC_REVIEW_4b961e3.md) | Static review of REA with file and line evidence |
| [SPEC_v0.2.md](docs/SPEC_v0.2.md), [REA_DECISION_MATRIX.md](docs/REA_DECISION_MATRIX.md), [RISKS_AND_OPEN_QUESTIONS.md](docs/RISKS_AND_OPEN_QUESTIONS.md), [CODEX_BRIEF_v0.1.md](docs/CODEX_BRIEF_v0.1.md) | Superseded v0.2 documents, kept for traceability |
| [history/CONCEPT_v0.1.de.md](docs/history/CONCEPT_v0.1.de.md) | Original concept v0.1 (German) |

## Roles

* The owner decides scope and approvals.
* Claude Code is the main developer and primary analyst.
* Codex does the independent security and code review, and takes over tasks Claude does not handle.
* GPT coordinates and checks scope.

L2A stays agent-independent: every case can be continued by either agent from its files.
Agent rules: [AGENTS.md](AGENTS.md).

## Licence

Not yet chosen. If REA's Evidence vocabulary is adopted, its MIT notice must be kept.
