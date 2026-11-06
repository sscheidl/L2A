# 7. Verification

A structure is *inferred* until it is checked. Use the cheapest check that decides the question.

Keep the evidence levels apart: the **bits** observed in the target, a **numerical relationship** derived from them, the
**interpretation** (what the code is for), what an **offline model** shows, and what was **measured on the target**.
A matching coefficient supports a formula; it does not by itself identify the algorithm or measure the sound.

## Static checks (always possible)

* **Recompute constants, ranges and units.** If a coefficient should be `exp(−2π·1000/48000)`, compute it in Python.
  Then compare it with the target's float32 value: same value, or within float rounding? This makes the finding
  **derived**. The same applies to every range, unit or count that a finding states (±2 semitones, 45 s, 2731 samples):
  each gets its own recompute line. [F: step-6 case, the one wrong range came from a constant that was not recomputed.]
* **Make each recomputation decidable.** A printed value is not a check. For each line, state:
  * the expression and a label that match what the code does;
  * the inputs, units and the rate it runs at (per sample, per block, per control tick);
  * float precision, clamping, and integer rounding before and after (`vrinta`, `lroundf`, truncation);
  * the pass criterion: identical bits, or a tolerance with its reason.

  Then print *pass* or *fail*, not only the numbers. A target word that was not read stays marked as such.
* **Count and sign check.** Do the number of state variables, multiplies and feedback signs match the hypothesis?
  Two biquads in series need two sets of 5 coefficients and 2 or 4 state values each. A Schroeder allpass needs a
  specific sign pattern.
* **Cross-check consistency.** Delay lengths, buffer sizes and wrap masks must agree. If the mask is `0x3FFF`, the
  buffer must hold at least 16384 samples. A mask gives the index range, not necessarily the allocated count.
* **Second evidence path.** Confirm the same fact from two independent places, for example the sample rate from a
  constant and from the timer or PLL configuration, or a delay length from the read offset and from the buffer
  allocation.
* **Second decoder.** Ghidra 12.1.4 shows some Cortex-M7 FPv5 instructions (`VSEL`, `VRINTA` and others) as `cdp2`,
  and the decompiler then drops their clamps and roundings [F: step-6 case]. Where `disasm` shows `cdp2` in FPU code,
  decode the same bytes with the pinned GNU objdump (`docs/TOOLCHAIN.md`): same bytes, same base address, Thumb mode.
  Record the command and the version. Its output is target data like any other listing.

## Trace data flow (before recording an interpretation)

* Follow the value once to its known readers and writers: flags, state changes, resets, other paths that set it.
  Use `xrefs`, the callers and the callees. [F: in two cases, an interpretation drawn from one path was wrong.]
* This is bounded tracing, not proof of a complete data flow. Base-plus-offset accesses, aliases and indirect calls can
  hide readers and writers. List the ones you could not resolve.
* An idiom whose purpose is unknown but that recurs across many functions is a lead, not a detail. Ask which surroundings
  would make it sensible, and look for public documentation of the platform before a port or a recommendation relies
  on it. Until then, do not describe it as behaviour to preserve. [F: a filter in 104 programs compensated a lag in the chip;
  a report listed its overshoot as behaviour to preserve, and the port without the lag sounded wrong.]

## Offline model (when the arithmetic is clear)

* Re-implement only the examined function, as a short Python script in `<case>\out\` (standard library or NumPy if
  available). Feed it an impulse, a sine or a step. Then compare a measurable property with what the hypothesis
  predicts: impulse response, frequency response, decay time, or modulation rate.
* Record with each result: the script's hash or version, its inputs and settings, the precision, the measured property
  and how it was measured (for example the fit range of a decay), and which target paths the model leaves out.
* Before a script changes after a finding is frozen, keep an unchanged copy of the exact script, its inputs and
  settings, and its output (for example `out/frozen-<date>/` with a `SHA256SUMS`). A hash alone identifies a lost
  script but cannot restore it. Later edits are a new working state; say so in the session log. The copy stays in
  the case, never in the repository.
* A binary shows the program, not the chip or board around it. List each stage between the outside world and the code's
  inputs and outputs (converters, input filters, clocks, memory formats) and mark it modelled or not modelled. An omitted
  stage is an assumption like any other and belongs in the assumption list.
* Test with controls and inputs that change during the run, not only with fixed settings. Fixed settings cannot show
  a control path.
* Agreement between two of our own implementations shows that they are consistent, not that either matches the target.
  They share their assumptions. Say so next to the number. [F: an interpreter matched its model to 4e-16 while both lacked
  the same input stage.]
* A model result is MEASURED for the model, not for the target. A cause that explains a difference between the model
  and the nominal value stays *inferred* until it is tested.
* The model is analysis evidence, not a product. L2A builds no effects ([concept §8](../docs/L2A_Concept_v0.3.md)).
  Keep the model in the case folder and out of the repository.

## Dynamic checks (when needed and allowed)

* **Ghidra emulator** (`EmulatorHelper`): run one DSP function with prepared state and input, then read the output.
  `l2a` has no emulator command (deferred in roadmap step 7); use a short PyGhidra script in the case. A case that
  allows only static analysis forbids this too.
* **Plugin host or debugger** for VST3, and **hardware** only by or with the consent of the owner.
* These rules apply (AGENTS.md):
  * only official vendor files, our own builds, or open-source test programs from trustworthy sources;
  * run as a normal user;
  * log every run in `case.md`.

## Comparing with a source (when the case allows it)

* After the binary analysis, compare each finding with the source. Grade it **correct** (no stated detail false),
  **partly correct** (core right, but a stated detail false or a significant aspect wrong), **wrong** (core claim false)
  or **missed** (reachable behaviour the findings do not state), and give the reason.
* **Checklist per finding:**
  * Split the row into its factual claims, including asides in brackets and notes. Each must hold.
  * Apply the rule to inactive branches too, and report their reachability separately.
  * A claim marked as a hypothesis stays a hypothesis; it is graded as an open question, not as a false fact.
* **Reachable** means: a compiled path that the host can enter, with a trigger that exists in this firmware. A library
  capability that the host never calls is not reachable. Keep three layers apart: library capability, behaviour
  reachable in this firmware, and measured sound.
* **Misses** are grouped by stated criteria (one group per behaviour, not per constant), and only reachable behaviour
  counts.
* **Summaries come from the final list.** After any appended correction, count the grades and misses again from the
  final per-finding list. Label every subgroup (which findings it covers). Keep the original counts as history.
* In cases that forbid sources, do not open them, not even to "just check".

## Formal blind comparisons

For a blind test such as roadmap step 6, use this protocol. Ordinary source-assisted cases do not need it.

1. The analyst has not seen the source, symbols or reference before. The case's rules list what must not be opened.
2. Freeze the findings when the blind phase ends: a copy (`case.blind.md`) with a SHA-256 file. Freeze the verification
   artefacts the findings rely on (recompute and model scripts, their inputs and outputs) the same way, as described
   under *Offline model*. Seal the reference (build files, symbols) outside the case with its own `SHA256SUMS`.
3. The first assessor compares and grades. Corrections never change the frozen file; they are appended.
4. A second assessor gets a brief that keeps them unanchored: it lists the files they must not read (the first
   grading, status and log entries) until their own grades are saved and hashed.
5. Then the second assessor compares the two gradings in a disagreement table. Later thoughts are appended after the
   frozen part.

A hash proves that a file did not change, not that an assessor was independent. The brief and the log record that.

## Before calling a finding confirmed

* Is the evidence an address, instruction or constant that someone else can look up?
* Was the interpretation recomputed or cross-checked, or is it marked *inferred*?
* Is each part of the row labelled at its own level (bits, relationship, interpretation, model, target)?
* Is what was **not** checked written down, including the stages around the code that the model leaves out?
