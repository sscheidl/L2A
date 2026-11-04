# 1. Workflow

## Start or resume a case

1. Read `<case>\case.md`, especially *Status → Next step* and *Rules for this case*. If the folder is new, the
   template is [templates/case.md](../templates/case.md); `l2a open` creates `case.md` from it.
2. **Check for a public upstream first**, unless the case's rules forbid sources (a blind test, for example). Many vendors publish their firmware or plugin code (GitHub, release notes,
   SDKs). Search for it before analysing, and compare the version string. If an upstream with a licence exists, record its
   URL, licence and version in `case.md`; that usually settles the legal question in minutes. Otherwise the owner records
   the provenance, licence and legal basis of a third-party target before any import.
3. Import once:

   ```text
   l2a open <case> <file> --profile cortex-m --base 0x24000000   # raw Cortex-M image
   l2a open <case> <file> --profile cortex-m-elf                 # Cortex-M ELF
   l2a open <case> <file> --profile pe                           # VST3 / Windows DLL
   ```

   `l2a open` checks that the requested loader, language and base were applied, plus some structural conditions such
   as a plausible vector table, and stops with an error if they fail. Do not work around that error: find the right
   settings instead (`docs/L2A_CLI.md`). Passing these checks does **not** prove that the base or architecture fits the
   target. Check that yourself: the vectors point into mapped code, literal addresses land in mapped blocks, and the
   path from reset makes sense.

## Survey (cheap, one Ghidra start)

```text
l2a query <case> info --then functions --sort fp --max-lines 25 --then functions --sort size --max-lines 15
```

* `fpops` counts instructions with floating-point p-code. A float DSP kernel stands out here; fixed-point code shows
  up instead as large functions with many multiplies ([3](03_building_blocks.md)).
* Then find the audio path ([2](02_audio_path.md)) instead of decompiling the top of the list blindly. What the
  callback calls is what matters.

## Dig in, one function at a time

```text
l2a query <case> decompile <f> --max-lines 80 --then consts <f> --then calls <f>
```

* Big functions go to a file in the case: `decompile <f> --out decomp_<addr>.c`. Then read it in parts.
* **A function's role comes from its own code**: its body, its disassembly, or a verified signature or call contract.
  A role guessed from a call site, a name or a string stays *inferred*. The finding says so for that role in its own
  words, with what would decide it. A row that mixes observed facts with an inferred role labels each part.
* **Record what you see at once.** Behaviour you notice but cannot explain yet (an infinite sustain, a flag that is
  never read, a second writer) goes into `case.md` immediately, as a finding or an open question with its address.
  Unrecorded observations drop out of coverage.
* Name what you understand in `case.md` (*Examined functions*), not in your head. Renames in Ghidra are optional and are
  done in the GUI, never while `l2a` has the project open.

## Grade every finding

| Level | Meaning | Example |
| --- | --- | --- |
| **observed** | Seen directly in the binary | "`0x24004480` holds float32 48000.0, read by `FUN_24004288`" |
| **derived** | Follows from observed facts by reasoning or recomputation | "the coefficient is `exp(-2π·1000/48000)`; recomputed, matches to 1e-7" |
| **inferred** | Plausible, not proven | "this looks like a Schroeder allpass" before its feedback sign and delay are checked |

* One finding per row in `case.md`, with the evidence column filled in: an address, instruction or constant. For
  targets that ship as source or scripts (Python, Csound, Pd, Lua …), the evidence is `file:line` in the target.
* Findings from a sub-agent stay marked as such until you have re-read their evidence yourself. Mark re-verified ones
  with ✔.
* Hypotheses go into *Open questions*, together with what would decide them. When decided, link the finding (→ F#).
* Known public designs may suggest a hypothesis. A match becomes a finding only through target evidence
  ([7](07_verification.md)).

## Plan coverage

* Start from the owner's question. For an instrument, the generator and exciter kernels and the real parameter routing
  usually decide the sound; cover them before features this firmware cannot reach.
* Code that is compiled in but not reachable from the host (an effect mode the firmware never selects, for example) gets
  one line each by default: what it is and why it is unreachable. Go deeper only for a stated hypothesis or on request.
* Keep a short list of what was left out, so that the next session or the reviewer can see the gap.

## Targets built on a library

Many targets delegate the DSP to a library: Csound, Pd, JUCE, CMSIS-DSP, DaisySP or the logue SDK.

* **Pin a reference version.** Record the repository, tag and commit of the library source you read, in *Target →
  Reference library*. Use the version the target ships with. If that version is unknown, use the last release before
  the target's date as an *assumed* reference, and keep "which version is on the device?" as an open question.
* **Grade library behaviour against that version.** A behaviour that rests on library source is at best
  *derived for <version>*. It stays *inferred* for the device until the version is confirmed.
* **Tag ownership** in signal-flow and parameter findings:
  * **[TGT]**: implemented in the target's own code.
  * **[API]**: fixed by the arguments the target passes to the library.
  * **[LIB]**: behaviour that exists only inside the library.

  This separates what the vendor designed from what the library does.

## Work done in a cloud session

* Upload originals to a cloud agent session only for our own or openly licensed targets. For proprietary targets, only
  derived material leaves the machine (AGENTS.md, *Data*).
* Hand the result back as **one archive of the whole case folder**: `case.md`, `out/`, `target/`, scripts and manifests,
  with `SHA256SUMS` over every file. Reference libraries are not copied; give their URL, tag and commit in a `REF.txt`.
* **Intake of a returned archive**, and of any other hand-over archive:
  * List the archive before extracting it. Refuse links, absolute paths, `..` entries and Windows drive or UNC paths,
    and check that every member stays inside the destination.
  * Extract into a new, empty folder, then move it to `D:\L2A-cases\<case>\`.
  * Run `sha256sum -c SHA256SUMS` without running any delivered script. The manifest's paths are data and must stay
    inside the case. A missing file is a finding about the hand-over: note it in the session log.
  * Keep the original archive and its manifest unchanged next to the case. Later edits to `case.md` or scripts are a new
    working state: say so in the session log instead of silently updating the old manifest.

## End of every work step

* Update `case.md`: status, next step, findings, examined functions, addresses, constants, open questions, and a session
  log entry. The log entry says what was done, what was skipped, and any dynamic runs.
* Raw output stays in `<case>\out\`. `case.md` keeps conclusions and the addresses that lead back to the evidence.
* Note significant omissions, for example "parameter smoothing not examined".
