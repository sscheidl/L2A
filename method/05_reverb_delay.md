# 5. Reverb and delay structures

Reverbs are networks of delays, filters and gains. To describe one, you need its **topology** (what feeds what), every
**delay length**, every **gain** with its sign, the **damping filters**, and the **modulation**.

## First, find the delay memory

* Large buffers live in external RAM on embedded targets (Daisy SDRAM `0xC000_0000`, ELF `.sdram_bss`) or on the heap
  (plugins). `l2a query <case> info` shows the memory blocks that Ghidra has mapped. That is not a map of the run-time
  memory: a raw import often maps only the image, so external RAM, heap and buffers stay unmapped. Infer buffer
  addresses and sizes from the code (base addresses, masks, clears at start-up) and mark run-time state as not read.
* Each delay line is a buffer plus a write index. Collect them per function:
  * base address
  * size: from the wrap mask `& (N−1)` or the wrap compare
  * read offsets: constants or parameter-dependent values

  These numbers are the reverb's fingerprint.
* Delay lengths may be stored as integers in a table (`table <addr> --type int32`), or as floats in ms and converted
  with `fs · 0.001`.
* A design written for another sample rate may scale its lengths by `fs/reference` at start-up.

## Topologies

| Structure | Signs in the code |
| --- | --- |
| **Feedback delay / echo** | One long buffer. Feedback gain, often a one-pole lowpass in the loop, and a wet/dry mix |
| **Schroeder/Moorer** | Several parallel feedback combs with lengths of similar size, summed, then 2–4 series allpasses with shorter lengths. Damping is a one-pole inside each comb |
| **Allpass diffuser chain** | Series allpasses with gains around 0.5–0.75 at the input, before a tank |
| **Figure-eight tank (plate style)** | Two cross-coupled branches, each with a modulated allpass, a delay, a damping lowpass, a decay gain, a second allpass and a delay. The output is a sum of taps from several delays with alternating signs |
| **FDN (feedback delay network)** | N delays (4, 8, 16). Their outputs are mixed by a matrix (Hadamard: ±1/√N; Householder: `2/N` minus the identity), then fed back with gains per line. Look for butterfly add/sub patterns or a loop over N×N |
| **Shimmer / pitch** | A delay read with a varying rate (two crossfaded taps, a window), feeding back into the tank |

## Literature values as hypotheses [A: recalled from the public sources, not re-checked here]

Matching numbers suggest a lineage. They do not prove it: check the topology and the signs too ([7](07_verification.md)).

* **Freeverb** (public domain, 2000), at 44.1 kHz:
  * comb lengths 1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617
  * allpass lengths 556, 441, 341, 225, with allpass gain 0.5
  * stereo spread +23 samples
* **Dattorro plate** (J. Dattorro, "Effect Design Part 1", JAES 1997), at 29761 Hz:
  * input diffusers 142, 107, 379, 277
  * tank: modulated allpasses 672 and 908, delays 4453 and 3720, allpasses 1800 and 2656, delays 4217 and 3163
  * diffusion gains 0.75, 0.625, 0.7 and 0.5
* Other generic signs: mutually prime lengths; ratios that keep modes apart; lengths scaled by `fs/44100` or
  `fs/29761`.

## Modulation

* An LFO (sine, triangle or random) offsets the read position of one or two allpasses or delays by a few to a few
  dozen samples. That requires a fractional read: linear interpolation, allpass or Hermite.
* Record the LFO rate (Hz, from the increment and `fs`) and its depth in samples.

## Damping and tone

* A one-pole lowpass inside the loop (high-frequency damping) and sometimes a one-pole highpass or a DC blocker. Record
  each coefficient and what controls it.
* Input or output EQ is often a biquad outside the loop.

## What to record per structure

* The **graph**: node list (delay, allpass, filter, gain) and edges, with addresses.
* For each node: the length or coefficient, its evidence address, and whether it is fixed or parameter-driven.
* **Decay control:** which parameter scales which feedback gains, and the mapping ([6](06_parameter_paths.md)).
* Stereo: whether the left and right channels share a tank, and where the taps differ.
* What is still open, for example "sign of the second tank allpass not checked".
