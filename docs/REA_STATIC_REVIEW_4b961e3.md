# REA static review (Phase 0, first pass)

* Subject: [morluto/rea](https://github.com/morluto/rea), npm `rea-agents` **6.8.0**
* Commit: `4b961e3715375971aee6dec848827c9c072d947b` (2026-11-03, "fix(cli): protect Amp settings during default registration (#8076)")
* Method: shallow `git clone` into an isolated scratch directory, hooks disabled, LFS
  smudge off, submodules not fetched. **Read only.** Nothing was installed, built or executed,
  and nothing was registered as an MCP server. Reviewers: Claude plus three read-only sub-agents. Decisive claims
  were re-checked by hand (marked ✔).
* Paths below are relative to the REA repository root.

**[C]** = seen in code or committed docs at this commit. **[A]** = inference or general knowledge.

## 1. Size, licence, health

| Finding | Evidence | Label |
| --- | --- | --- |
| MIT licence | `LICENSE`, `package.json` | [C] ✔ |
| ~7,100 tracked files; ~2,400 non-test source files (~568k lines); ~1,100 colocated tests plus ~2,400 files in `tests/`; 35 workflows | `git ls-files`, `.github/workflows` | [C] |
| Releases 4.0.0 (10-05) → 6.8.0 (10-25); three majors in four days; minors with BREAKING sections | `CHANGELOG.md` | [C] |
| Pins Ghidra 12.1.4 (verified version) and requires JDK ≥ 21 | `THIRD_PARTY_NOTICES.md`, `src/ghidra/GhidraReleasePolicy.ts` | [C] |
| Five git submodules (jadx-headless-mcp, binwalk, unblob, ghidra-nativeaot, wakaru) | `.gitmodules` | [C] ✔ |
| The very high GitHub star count (~424k) was not evaluated as a trust signal | `gh repo view` | [A] |

## 2. Architecture and extension

| Finding | Evidence | Label |
| --- | --- | --- |
| ~234 MCP tools defined as Zod contracts in `src/contracts/*ToolContracts.ts`, registered in `src/server/createServer.ts` | `src/contracts/toolEffects.ts:53` | [C] |
| Tool families can be limited with `REA_MCP_TOOL_FAMILIES`; out-of-scope tools stay registered but disabled. No read-only mode, no per-tool allowlist | `src/config/mcpToolFamilies.ts:13` | [C] ✔ |
| No public API: no `exports` or `main`, only `bin`. The composition contract is documented as internal | `package.json`, `docs/capability-composition.md:103` | [C] |
| Adding a tool family requires a fork that touches ≥ 15 internal files plus generated catalogs | `src/contracts/toolFamilyIds.ts`, `toolEffects.ts`, `createServer.ts`, `cli.ts` … | [C] / effort [A] |
| CLI on `incur`, ~180 commands, `--json` / `jsonl` / `md` / `csv`, `--snapshot`; not 1:1 with MCP (the "enhanced" family is MCP-only) | `src/cli.ts:174,181`, `docs/cli.md` | [C] |
| MCP transport stdio; `mcp --http` is opt-in, binds 127.0.0.1, checks Host/Origin, **no auth token, no TLS** | `src/main.ts`, `docs/mcp-contracts.md:1058-1080`, `serveStreamableHttp.ts` | [C] |
| REA itself calls no LLM API; it returns data to the calling agent | absence of SDKs and API calls | [C] (by absence) |

## 3. Evidence model (the reusable part)

| Finding | Evidence | Label |
| --- | --- | --- |
| Evidence record with `confidence: observed \| derived \| inferred` and `authority: shipped-artifact \| controlled-replay \| historical-reference \| external-service \| analyst-inference`, plus subject (name, sha256, path), provider, operation, parameters, raw and normalized results, limitations, locations, links. Content-addressed ID | `src/domain/evidence.ts:12-110` | [C] ✔ |
| Residual-unknowns ledger: status open / investigating / blocked / contradicted / resolved; supporting and contradicting evidence; "verified" resolution requires ≥ 1 evidence ID; hash-chained revisions | `src/domain/residualUnknown.ts:76-120` | [C] |
| No explicit `schema_version`; old formats are rejected ("recreate with current release") | `src/domain/evidence.ts:147` | [C] |
| Tool results mark target-derived text with `_meta.provenance.untrusted_content` | `src/server/toolResultEncoding.ts:29` | [C] |

## 4. Ghidra and firmware capabilities

| Finding | Evidence | Label |
| --- | --- | --- |
| Headless Ghidra with a Java socket bridge. Operations: list functions, names, segments and strings; disassembly; decompile (`procedure_pseudo_code`); instructions; callers and callees; xrefs; `read_bytes`; masked `search_bytes` (≤ 1000 hits); typed operand immediates | `bridge/ghidra/ReaGhidraBridge.java:441-482,774-830,1366-1392` | [C] |
| Not present: P-code export, constant or scalar search, type creation, call-graph export, memory-block creation, SVD | same | [C] (by absence) |
| Raw import: file offset 0 = entry = base; fixed language list x86, x86-64, ARM (A32, `ARM:LE:32:v7`), AArch64, 6502, 68000 | `src/ghidra/GhidraRawBinaryLanguage.ts:10-60`, `ReaGhidraPrepareRaw.java` | [C] ✔ |
| **"Thumb-only images, including Cortex-M firmware, are not supported"**; no load-address, vector-table or memory-map handling | `docs/raw-binary.md:31-33,150-152` | [C] ✔ |
| The language override is refused for raw targets | `src/ghidra/GhidraAnalysisProfile.ts:219-228` | [C] ✔ |
| **Windows: only native PE and raw 6502 admitted**; ELF, Mach-O and raw ARM are refused; existing-project reuse unavailable; bridge edits need a unix socket | `src/ghidra/GhidraProvider.ts:690-713`, `GhidraProviderCapabilities.ts:217-222` | [C] ✔ |
| On POSIX, ARM ELF with `REA_GHIDRA_LANGUAGE_ID=ARM:LE:32:Cortex` is documented but marked unverified; the setting is global | `docs/installation.md:1486-1510` | [C] |
| On POSIX, an existing Ghidra project can be read (owned copy, `-readOnly`), but not for raw targets | `docs/installation.md:1416-1450` | [C] ✔ |
| Built-in portable parsers: Intel HEX, S-record, UF2, DfuSe, ESP image, FIT, uImage, devicetree (region listing and extraction only) | `src/domain/firmware/*` | [C] |
| Binwalk and Unblob wrappers are Linux-only | `src/firmware/FirmwareCommand.ts:78-92` | [C] |
| No emulator lane for executing a single function (Unicorn appears only inside pwntools layout inference) | `bridge/pwntools/layout_impl.py` | [C] |
| No C++ vtable or RTTI recovery; fat Mach-O is refused (thin it first) | `ReaGhidraBridge.java:1448`, `GhidraProvider.ts:296-305` | [C] |
| No audio, DSP or synth-specific code anywhere | grep | [C] (by absence) |

## 5. Supply chain and runtime security

| Finding | Evidence | Label |
| --- | --- | --- |
| No `preinstall` / `install` / `postinstall`. `prepare` and `prepack` act only in a source checkout | `package.json`, `scripts/prepare.mjs`, `scripts/prepack.mjs` | [C] ✔ |
| Optional dependency `frida 17.23.2` has an install script that downloads a native binding | `package-lock.json` (`hasInstallScript`) | [C] / download [A] |
| Prebuilt `rea-windows-x64.node` (MinGW cross-build in CI). Its SHA-256 is checked against a `manifest.json` from the same tarball, which detects corruption but not tampering; no signature | `native/windows/README.md`, `src/windows/WindowsNativeLoader.ts:193-216` | [C] |
| Releases are published with `--ignore-scripts` from GitHub OIDC (npm provenance likely) | `.github/workflows/release.yml:412,437` | [C] / provenance [A] |
| No telemetry, analytics or auto-update found. Network use is opt-in or per call: Hopper feed (setup, macOS/Linux), `rea update`, source maps, Playwright/CDP, environment-state fetch | `src/application/HopperReleaseFeed.ts`, `UpdateRuntime.ts`, `server/environment/stateIntake.ts` | [C] (by absence) |
| The process spawner uses `shell: false`. Windows `.bat` calls reject `"%^!&\|<>` and CR/LF | `src/process/ProviderProcess.ts:311-316`, `WindowsBatchCommand.ts:35-79` | [C] |
| Ghidra runs `-readOnly` with a temporary project and private HOME/APPDATA/TEMP; per-session capability token. The policy itself states this "is not a sandbox" | `src/ghidra/GhidraLauncher.ts`, `SECURITY.md` | [C] ✔ |
| `rea setup` writes MCP registrations and skills into global agent configs (`~/.claude.json`, `~/.codex/config.toml`, Cursor, Gemini, VS Code …) after showing a plan, with backups | `src/application/SupportedClients.ts:524-660`, `src/cli/setupCommands.ts` | [C] |
| No workspace path allowlist: tools accept any absolute path the user can read | absence of a guard | [A] |
| 16 tools are flagged `executesForeignCode: true` (Frida, debuggers, capture_*). REA has no consent gate; only MCP hints are passed, and approval is left to the client | `src/contracts/toolEffects.ts` | [C] ✔ |
| The shipped skill recommends `npx -y rea-agents@latest` (unpinned) and states that "REA does not require permission grants or per-call approval flags"; the client may still require approval | `.agents/skills/reverse-engineer-anything/SKILL.md:69-73,457-459` | [C] ✔ |
| Agent-directed text in REA's `AGENTS.md:137-143` (Turborepo block telling agents to run a `node -p` command). Benign in intent; not followed | `AGENTS.md` | [C] |

## 6. Not yet reviewed (open for Codex Phase 0b, only if REA is needed later)

* Contents of the five submodules and the ~490 KB `package-lock.json` (42 runtime deps), audited as a dependency tree
* The published npm tarball versus this commit (reproducibility, provenance attestation)
* The Windows native addon source `native/windows/src/*.cc`
* Every Windows PE code path in `src/ghidra` (the only lane L2A might use)
