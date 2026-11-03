# 7. Verification

A structure is *inferred* until it is checked. Use the cheapest check that decides the question.

## Static checks (always possible)

* **Recompute constants.** If a coefficient should be `exp(−2π·1000/48000)`, compute it in Python. Then compare it
  with the target's float32 value: same value, or within float rounding? Note the formula, inputs, result and
  difference. This makes the finding **derived**.
* **Count and sign check.** Do the number of state variables, multiplies and feedback signs match the hypothesis?
  Two biquads in series need two sets of 5 coefficients and 2 or 4 state values each. A Schroeder allpass needs a
  specific sign pattern.
* **Cross-check consistency.** Delay lengths, buffer sizes and wrap masks must agree. If the mask is `0x3FFF`, the
  buffer must hold at least 16384 samples.
* **Second evidence path.** Confirm the same fact from two independent places, for example the sample rate from a
  constant and from the timer or PLL configuration, or a delay length from the read offset and from the buffer
  allocation.

## Offline model (when the arithmetic is clear)

* Re-implement only the examined function, as a short Python script in `<case>\out\` (standard library or NumPy if
  available). Feed it an impulse, a sine or a step. Then compare a measurable property with what the hypothesis
  predicts: impulse response, frequency response, decay time, or modulation rate.
* The model is analysis evidence, not a product. L2A builds no effects ([concept §8](../docs/L2A_Concept_v0.3.md)).
  Keep the model in the case folder and out of the repository.

## Dynamic checks (when needed and allowed)

* **Ghidra emulator** (`EmulatorHelper`): run one DSP function with prepared state and input, then read the output.
  `l2a` has no emulator command yet [O]; use a short PyGhidra script in the case, and propose a command if this is
  needed often.
* **Plugin host or debugger** for VST3, and **hardware** only by or with the consent of the owner.
* These rules apply (AGENTS.md):
  * only official vendor files, our own builds, or open-source test programs from trustworthy sources;
  * run as a normal user;
  * log every run in `case.md`.

## Comparing with a source (when the case allows it)

* After the binary analysis, compare each finding with the source. Grade it **correct**, **partly correct**, **wrong**
  or **missed**, and give the reason. The Rings/Torus test (roadmap step 6) uses exactly this scale.
* In cases that forbid sources, do not open them, not even to "just check".

## Before calling a finding confirmed

* Is the evidence an address, instruction or constant that someone else can look up?
* Was the interpretation recomputed or cross-checked, or is it marked *inferred*?
* Is what was **not** checked written down?
