# 3. DSP building blocks

How common blocks look after compilation. Classify a function by its **state** (what persists between calls), its
**per-sample arithmetic**, and its **constants**. Recognising a shape is *inferred*. Confirm it with
[verification](07_verification.md).

## Filters

| Block | State per channel | Per-sample core | Typical constants |
| --- | --- | --- | --- |
| One-pole lowpass | 1 float `z` | `z += a·(x − z)` or `z = b·x + a·z` | `a = 1 − exp(−2π·fc/fs)`, so look for `exp`, `2π/fs` and values close to 1 |
| DC blocker | 2 floats | `y = x − x1 + R·y1` | `R` ≈ 0.995–0.9999 |
| Biquad (DF1 / DF2T) | 4 (DF1) or 2 (DF2T) floats | 5 multiplies: `b0 b1 b2 a1 a2` | Coefficient set computed from `cos(w)`, `sin(w)/(2Q)` with `w = 2π·fc/fs`; Q 0.7071 = `sqrt(0.5)` for Butterworth |
| State-variable filter (SVF) | 2 floats (`ic1eq`, `ic2eq`, or `low`/`band`) | `g = tan(π·fc/fs)`, then `k = 1/Q`, with outputs low, band and high from the same state | `π/fs`, `tan` or its approximation |
| Ladder / cascaded one-poles | 4+ floats | 4 chained one-poles, feedback from the last stage, often `tanh` | Resonance scaled up to about 4 |

* On ARM, a filter loop shows `vmul`/`vmla`/`vfma` chains, with state loads and stores at constant struct offsets.
  Coefficient recalculation (`sin`, `cos`, `tan`, `exp`) often happens outside the sample loop or only when a
  parameter changes.
* A filter cascade appears as the same code repeated, or a loop over stages with a stride of 5 coefficients (biquads).

## Delays and interpolation

* **Delay line:** a buffer (often in external SDRAM on Daisy, `0xC000_0000`), a write index, and a read index equal to
  write minus delay. Wrap is done with `& (size−1)` (power-of-two size) or with a compare-and-subtract.
* **Fractional read:** linear interpolation `a + f·(b − a)`, allpass interpolation, or Hermite/Lagrange with 4 taps.
  A 4-tap Hermite uses the constants 0.5 and 1.5.
* **Comb:** a delay plus feedback, `y = x + g·d[n−M]`. **Schroeder allpass:** `v = x + g·d; y = d − g·v` (signs vary).
  Details in [5](05_reverb_delay.md).

## Oscillators, LFOs and tables

* **Phase accumulator:** `phase += inc; if (phase >= 1) phase -= 1`. The increment is `f/fs`, so look for `1/fs`.
  Integer variants use a 32-bit phase that wraps naturally.
* **Wavetable:** an index taken from the top bits of the phase plus interpolation. A table of `2^n` floats is often
  `sin` or a band-limited wave: `table <addr> --type float32 --count 16`.
* **Polynomial sine and fast sine:** a short odd polynomial in the phase, without a table.
* **Band-limited steps:** PolyBLEP corrections near discontinuities (`t·t`, `2·t`, branches near phase 0 and 1).
* **Noise:** a linear congruential generator, for example the multiplier `1664525` with `1013904223`, or `xorshift`
  shifts 13/17/5. Then scaling to float with `1/2^31` or `1/2^32`.

## Envelopes

* An ADSR is a state machine (stage index) with one-pole approaches to targets (`level += (target − level)·rate`),
  or with linear ramps. Time constants appear as `exp(−1/(t·fs))`, or as a rate per sample multiplied by
  `1/1000` when times are in ms.
* Look for switch or if chains on a small integer, plus the transitions at gate on and gate off.

## Saturation and fast math

* Saturators: `tanh` (a libm call or a rational approximation such as `x·(27 + x²)/(27 + 9x²)`), soft clip
  `x − x³/3` clamped to ±1, hard clip via `vmin`/`vmax` or `vcmp` with branches.
* Fast exp2/pow approximations: bit tricks that build a float exponent: shift by 23, add `127`, and the constant
  `0x3f800000`, which is 1.0. A fast inverse square root uses the magic constant `0x5f3759df` or a variant.
* Library calls: `expf`, `powf`, `sinf`, `tanf`, `tanhf`, `log10f`. In stripped firmware these are often
  recognisable by their size and polynomial constants. They are not DSP structure; note them and move on.

## Fixed point (Cortex-M4/M7 DSP extension, older chips)

* Q15/Q31 data appears with `smulbb`, `smlabb`, `smmul`, `smlal`, `ssat`, `qadd` and arithmetic shifts by 15 or 31.
* Read tables with `--type q15` or `q31` ([4](04_constants.md)).
* Saturation (`ssat #16`) at an output usually marks the conversion to the codec format.

## SIMD

* ARM NEON (Cortex-A, some logue platforms) and x86 SSE/AVX (plugins) process 4 or 8 samples or channels at once.
  A loop count divided by 4 or 8, plus a scalar tail loop, is the sign.
* Cortex-M7 has no NEON. Its "SIMD" consists of 16-bit-pair instructions (`smlad`, `qadd16`) for fixed point.

## Denormals

* Writes to the FPSCR flush-to-zero bit (`vmsr fpscr`), or tiny additive constants (`1e-15` to `1e-20`) in feedback
  paths, protect against denormal slowdown. They are a hint for recursive filters and reverbs.
