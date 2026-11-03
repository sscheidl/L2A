# 4. Constants

Numbers are the cheapest evidence. Typical paths:

* `l2a query <case> consts <f>` shows every data word a function reads, with its float32 reading.
* `l2a query <case> search --float 48000` finds a value and the functions that use it.
* `l2a query <case> table <addr> --type float32 --count 32` reads tables.

## How compilers store constants [A]

* **Literal pool** (ARM): `vldr s0, [pc, #…]` reads a float word next to the function. It shows up in `consts` as
  `data … word 0x… float …`.
* **`movw`/`movt` pairs:** two halves of the float's bit pattern are built in a register and moved with `vmov`.
  `consts` then shows two scalars, for example `0x8000` and `0x473b`, which together are 48000.0. A memory `search`
  will **not** find these, so check `consts` too.
* **VFP immediates:** `vmov.f32 s0, #0.5` encodes simple values (±0.125…31 with short mantissas) directly in the
  instruction. They appear in the disassembly, not in memory.
* **Folded math:** `x / 48000` often becomes `x * 2.0833333e-05`. `2π/fs` is folded into one constant. Search for the
  product, not for its parts.
* **Pointer or float? Decide by use, not by value:** `consts` prints a float32 reading for every plausible word, so
  the peripheral address `0x40020010` shows up as "float 2.03…".
  * The address range alone decides nothing. Common constants fall into the same ranges: 1.0 is `0x3f800000`,
    π is `0x40490fdb`, 48000.0 is `0x473b8000`, and −2.0 is `0xc0000000`.
  * Look at the instructions that consume the word. A pointer is loaded into a core register and then dereferenced
    (`ldr`/`str` with it as the base) or compared with other addresses. A float constant is loaded with `vldr`, or
    moved with `vmov` into an FPU register, and then used in floating-point arithmetic.
  * The memory map (`l2a query <case> info`) helps further: a word that points into a mapped block, or into a known
    peripheral range, is a pointer *candidate*.
  * If the use is unclear, record both readings and mark the interpretation *inferred*.
* **Double precision:** C code without the `f` suffix can produce float64 constants (`--type float64`,
  `search --double`) and calls to software double routines on single-precision FPUs.

## Reference table (float32 bit patterns MEASURED 2026-11-03 with Python `struct.pack('<f', …)`)

| Meaning | Value | float32 bits |
| --- | --- | --- |
| sample rate 48 kHz | 48000 | `0x473b8000` |
| sample rate 44.1 kHz | 44100 | `0x472c4400` |
| sample rate 96 kHz | 96000 | `0x47bb8000` |
| sample rate 32 kHz | 32000 | `0x46fa0000` |
| 1/48000 | 2.08333333e-05 | `0x37aec33e` |
| 1/44100 | 2.2675737e-05 | `0x37be37c6` |
| 1/96000 | 1.04166667e-05 | `0x372ec33e` |
| π | 3.14159265 | `0x40490fdb` |
| 2π | 6.28318531 | `0x40c90fdb` |
| π/2 | 1.57079633 | `0x3fc90fdb` |
| 1/(2π) | 0.159154943 | `0x3e22f983` |
| 2π/48000 | 0.000130899694 | `0x3909421e` |
| π/48000 (SVF `tan` argument) | 6.54498469e-05 | `0x3889421e` |
| ln 2 | 0.693147181 | `0x3f317218` |
| 1/ln 2 | 1.44269504 | `0x3fb8aa3b` |
| log2 10 | 3.32192809 | `0x40549a78` |
| log10 2 | 0.301029996 | `0x3e9a209b` |
| ln(10)/20: dB to linear via `exp` | 0.115129255 | `0x3debc8e3` |
| 20/ln(10): linear to dB via `log` | 8.68588964 | `0x410af967` |
| 1/20: dB to linear via `pow(10, dB·0.05)` | 0.05 | `0x3d4ccccd` |
| √0.5 (Butterworth Q, −3 dB pan) | 0.707106781 | `0x3f3504f3` |
| √2 | 1.41421356 | `0x3fb504f3` |
| A4 = 440 Hz | 440 | `0x43dc0000` |
| MIDI note of A4 | 69 | `0x428a0000` |
| 1/12 (semitones to octaves) | 0.0833333333 | `0x3daaaaab` |
| 2^(1/12) | 1.05946309 | `0x3f879c7d` |
| frequency of MIDI note 0 | 8.17579892 | `0x4102d013` |
| 127 (7-bit MIDI maximum) | 127 | `0x42fe0000` |
| 1/127 | 0.00787401575 | `0x3c010204` |
| 1/128 | 0.0078125 | `0x3c000000` |
| 1/16383 (14-bit MIDI or pitch bend) | 6.10388818e-05 | `0x38800200` |
| 1/16384 | 6.10351562e-05 | `0x38800000` |
| 32767 | 32767 | `0x46fffe00` |
| 32768 | 32768 | `0x47000000` |
| 1/32768 (16-bit to float) | 3.05175781e-05 | `0x38000000` |
| 1/32767 | 3.05185095e-05 | `0x38000100` |
| 2^23 (24-bit audio) | 8388608 | `0x4b000000` |
| 1/2^23 (24-bit to float) | 1.1920929e-07 | `0x34000000` |
| 2^31 (32-bit audio) | 2.14748365e+09 | `0x4f000000` |
| 1/2^31 (32-bit to float) | 4.65661287e-10 | `0x30000000` |
| 1/1000 (ms to s) | 0.001 | `0x3a83126f` |
| 0.999 (typical smoothing or feedback) | 0.999 | `0x3f7fbe77` |
| 1e-6 | 1e-06 | `0x358637bd` |
| 1e-15 (denormal guard) | 1e-15 | `0x26901d7d` |

Integers:
* `0x3f800000` is 1.0 as bits, used in fast-math tricks.
* `0x5f3759df` is the fast inverse square root constant.
* `1664525` and `1013904223` are the LCG multiplier and increment.
* `0x7fffffff` and `0x80000000` mark 32-bit saturation.

## Patterns that reveal a mapping

* **Exponential frequency mapping:** `f = f0 · 2^(v·range)`, or `exp(v·ln(fmax/fmin))`. Look for `exp2f` or `powf`
  calls and the bounds 20, 20000, or musically chosen limits.
* **dB:** `pow(10, x/20)` or `exp(x · 0.115129255)`. A parameter range of −60…0 or −inf…+6 is typical.
* **Pitch:** `440 · 2^((n − 69)/12)`, or `8.1758 · 2^(n/12)`.
* **Time constants:** `exp(−1/(t · fs))`. Here `t` comes from a parameter in ms (`·0.001`), so look for `fs` and `0.001`
  in the same function.
* **Delay lengths in samples:** integers, often prime or mutually prime, sometimes scaled by `fs/reference_rate`
  ([5](05_reverb_delay.md)).

## Record

Add each constant to `case.md` (*Constants and tables*) with:
* its address and type;
* its value;
* its interpretation;
* its level: observed for the value, derived or inferred for the interpretation.
