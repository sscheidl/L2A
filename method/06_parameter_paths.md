# 6. Parameter paths

A parameter path runs from an input to a DSP value:

**source → raw value → scaling/mapping → smoothing → DSP variable**

Trace it backwards from the DSP: it is easier than tracing forwards from the knob.

## Backwards from the DSP

1. In the audio callback, find a coefficient or gain that is read from RAM rather than from a constant.
2. Find who writes it: `l2a query <case> xrefs <ram address>`. Often there is one writer in the control path, and
   sometimes a smoother inside the callback. But expect more: a knob and a MIDI CC may write the same value, a preset
   load or a reset may overwrite it, and per-voice copies may exist.
3. In the writer, follow the value back through the mapping ([4](04_constants.md)) to its source.
4. Before recording the interpretation, follow the value once to its other readers too: who uses it, and what changes
   when it changes ([7](07_verification.md), *Trace data flow*).

`xrefs` lists the references Ghidra found to an address. Ghidra resolves some accesses through a base pointer plus an
offset (`[r4, #0x28]`), but accesses through computed pointers, aliases and indirect calls **may be missing**. An empty
`xrefs` list does not prove that nothing writes the value. Record the writers you know, which one wins, and the ones you could not resolve.

## Sources

| Source | Typical signs |
| --- | --- |
| **Embedded knobs and CV** (ADC) | DMA from ADC into a small array of uint16 or float values. Scaling with `1/65535`, `1/4095` (12-bit) or a float conversion. Pots are often filtered by a one-pole |
| **Encoder and buttons** | GPIO reads, counters, debounce timers |
| **MIDI** (UART or USB) | Status-byte switch (`0xB0` control change, `0x90` note on, `0x80` note off, `0xE0` pitch bend), 7-bit values scaled by `1/127`, 14-bit values combined with `<< 7` |
| **Plugin parameters** | Normalised values 0…1 delivered through parameter change queues in the process call, or through a setter called by the host. Each parameter has an ID; the plugin maps it to a range |
| **Presets and storage** | Structures read from flash, QSPI or a file, then copied into the parameter state |

## Mapping

* Linear: `min + v·(max − min)`. Exponential: `min · (max/min)^v`. dB: `pow(10, …/20)`. Pitch: `2^(semitones/12)`.
* Skewed curves: `v²`, `v³`, or `pow(v, k)`. Tables: an index from `v`, then interpolation.
* Quantised: `floor(v·N)` (switch positions, modes). Look for `vcvt` to an integer followed by a switch.

## Smoothing

* A one-pole per sample or per block (`cur += (target − cur)·k`), or a linear ramp over a block. Record `k` and the
  rate: per sample or per block.
* Coefficient updates may happen only when a value changes. Look for a compare with the previous value, and the
  recomputation (`sin`/`cos`/`tan`/`exp`) behind it.

## Record

Per parameter, write in `case.md`:
* the source, with its address;
* the raw range;
* the mapping formula, with the evidence for each constant;
* the smoothing;
* the DSP variable and the block it controls.

Mark each part observed, derived or inferred.
