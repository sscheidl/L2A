# L2A – Listen to Anything

Evidence-based static analysis of music software and firmware DSP, so that its algorithms
can be understood and documented as **independently written specifications**.
Principle: *understand, don't copy*.

**Status: concept, no implementation yet.** Nothing in this repository has been approved for
implementation. Hardware and listening results are NOT MEASURED.

> [!WARNING]
> This repository is **public**. It holds only L2A's own code, schemas and documentation.
> Proprietary binaries, decompiler output and case results are never committed; cases live
> outside the checkout (see [SPEC §6](docs/SPEC_v0.2.md#6-security-and-data-rules-binding)).

## Documents

| Document | Content |
| --- | --- |
| [SPEC_v0.2.md](docs/SPEC_v0.2.md) | Revised specification: architecture decision, v0.1 scope, security rules, phases |
| [REA_DECISION_MATRIX.md](docs/REA_DECISION_MATRIX.md) | What to take over, adapt, add or omit from REA |
| [RISKS_AND_OPEN_QUESTIONS.md](docs/RISKS_AND_OPEN_QUESTIONS.md) | Prioritised risks and questions for the owner |
| [CODEX_BRIEF_v0.1.md](docs/CODEX_BRIEF_v0.1.md) | Implementation brief for Codex (draft, not released) |
| [REA_STATIC_REVIEW_4b961e3.md](docs/REA_STATIC_REVIEW_4b961e3.md) | Static review of REA with file and line evidence |
| [history/CONCEPT_v0.1.de.md](docs/history/CONCEPT_v0.1.de.md) | Original concept v0.1 (German) |

## Roles

The owner decides scope and approvals. Codex is the main developer. Claude reviews the architecture.
GPT coordinates and checks quality. Agent rules: [AGENTS.md](AGENTS.md).

## Licence

Not yet chosen. If REA's Evidence vocabulary is adopted, its MIT notice must be kept.
