# 1. Workflow

## Start or resume a case

1. Read `<case>\case.md`, especially *Status → Next step* and *Rules for this case*. If the folder is new, the
   template is [templates/case.md](../templates/case.md); `l2a open` creates `case.md` from it.
2. Before any import, the owner must record the provenance, licence and legal basis of third-party targets.
3. Import once:

   ```text
   l2a open <case> <file> --profile cortex-m --base 0x24000000   # raw Cortex-M image
   l2a open <case> <file> --profile cortex-m-elf                 # Cortex-M ELF
   l2a open <case> <file> --profile pe                           # VST3 / Windows DLL
   ```

   A wrong profile or base address stops the import with an error. Do not work around that error: find the right
   settings instead (`docs/L2A_CLI.md`).

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
* Name what you understand in `case.md` (*Examined functions*), not in your head. Renames in Ghidra are optional and are
  done in the GUI, never while `l2a` has the project open.

## Grade every finding

| Level | Meaning | Example |
| --- | --- | --- |
| **observed** | Seen directly in the binary | "`0x24004480` holds float32 48000.0, read by `FUN_24004288`" |
| **derived** | Follows from observed facts by reasoning or recomputation | "the coefficient is `exp(-2π·1000/48000)`; recomputed, matches to 1e-7" |
| **inferred** | Plausible, not proven | "this looks like a Schroeder allpass" before its feedback sign and delay are checked |

* One finding per row in `case.md`, with the evidence column filled in: an address, instruction or constant.
* Hypotheses go into *Open questions*, together with what would decide them. When decided, link the finding (→ F#).
* Known public designs may suggest a hypothesis. A match becomes a finding only through target evidence
  ([7](07_verification.md)).

## End of every work step

* Update `case.md`: status, next step, findings, examined functions, addresses, constants, open questions, and a session
  log entry. The log entry says what was done, what was skipped, and any dynamic runs.
* Raw output stays in `<case>\out\`. `case.md` keeps conclusions and the addresses that lead back to the evidence.
* Note significant omissions, for example "parameter smoothing not examined".
