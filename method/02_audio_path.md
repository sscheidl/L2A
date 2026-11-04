# 2. Finding the audio path

Goal: find the function that processes one audio block, together with its inputs, outputs, block size and sample format.
Everything else (UI, MIDI, storage) hangs off it.

## Cortex-M firmware (Daisy, other STM32)

1. **Vector table.** With `--profile cortex-m`, `l2a open` has already created `reset_handler`, the system handlers and
   `irqN_handler` functions. Handlers shared by many vectors are named `irq_shared_<addr>`; they are usually the
   default "do nothing" handler.
2. **Interrupts that move audio.** Audio arrives from a serial audio interface (SAI or I2S) through DMA. The DMA
   interrupt fires at half and full buffer (double buffering). Candidates:
   * IRQ handlers that are not shared;
   * handlers that clear DMA interrupt flags, which shows up as writes to peripheral addresses in `0x4000_0000–0x5FFF_FFFF`.

   `l2a query <case> xrefs <irq handler> --from` lists what a handler touches.
3. **Peripheral addresses** [A, verify in the chip's reference manual]: on STM32H7 (Daisy Seed), DMA1 is at
   `0x40020000`, DMA2 at `0x40020400` and SAI1 at `0x40015800`. Stream `n` of a DMA controller has its registers at
   `base + 0x10 + 0x18·n`. A handler that writes a DMA flag-clear register and then calls through a pointer is the
   strongest candidate.

   [F: MEASURED 2026-11-03 on our own Daisy build `PhysicalModeling-v0.1.0.bin`] IRQ 11 and IRQ 12 are 6-byte
   trampolines (`ldr r0,[pc…]; b.w …`). Each loads a handle pointer from RAM and branches to one shared DMA interrupt
   routine. That routine compares the handle's stream address with `0x40020010` and `0x40020028`, which are DMA1
   streams 0 and 1. So with HAL-style code, follow the shared routine and the handle structures, not the tiny vector
   targets.
4. **Callback indirection.** HAL-style drivers store the user callback as a function pointer in RAM and call it with
   `blx rN`. Follow the call through the decompiled handler to the pointer, then find who writes that pointer, using
   `xrefs` on its RAM address. The writer gets the callback address as a constant.
5. **What the callback looks like.** Typical signs:
   * a loop over a block size (powers of two such as 4–256, or a size read from a struct);
   * interleaved buffer access (`[i*2]`, `[i*2+1]`);
   * conversions from integers to float or back: `vcvt` with `1/8388608` (24-bit) or `1/2147483648` (32-bit), and
     saturation ([4](04_constants.md)).
6. **Main loop vs callback.** The main loop polls controls (ADC, encoder, MIDI UART) and writes parameters into RAM. The
   callback reads them ([6](06_parameter_paths.md)). Separate the two early.

Raw images have no symbols, so the decompiler shows `FUN_…` and `DAT_…` names. Name them in `case.md` as you go.

## VST3 plugins (Windows PE)

1. The exported `GetPluginFactory` returns the factory object (`l2a query <case> disasm GetPluginFactory`). The factory
   holds class entries. Each has a 16-byte class ID, the name, a category such as `Audio Module Class`, and a create
   function.
2. The processor class implements the audio processor interface. In its vtable, look for the function that takes the
   process-data structure: sample count, inputs, outputs, and per-channel `float**` buffers. That function is
   `process()`, and the DSP hangs below it.
3. Framework wrappers are common [A]. JUCE plugins forward `process()` to the plugin's `processBlock`, iPlug to
   `ProcessBlock`, and so on. Skip the wrapper layer quickly. Framework strings and RTTI names, which are target data,
   help to recognise it.
4. Parameters arrive as change queues inside the process data ([6](06_parameter_paths.md)).
5. For 64-bit x86, floating-point code uses SSE/AVX. Look at `fpops`, and expect vector instructions such as `mulps`
   and `addps` in SIMD kernels.

## Korg logue SDK units

* drumlogue units are stripped ARM ELF shared objects [F: concept §2]. Their exported entry points (unit header,
  init, render, parameter set) give the render function directly: `l2a query <case> functions --name render`.
* Older platforms (prologue, minilogue xd, NTS-1) ship Cortex-M code inside a unit package [A]. Unpack it first, then
  look for the fixed header and its hook function pointers.

## ESP32 (AMYboard and similar)

* Audio usually runs in a FreeRTOS task that writes blocks to the I2S driver [A]. Find calls to the task-create
  function: its function-pointer argument is the task body. Then find the I2S write call inside a loop. The Xtensa
  module quality in Ghidra is still [O].

## Linux boards with an audio engine (Raspberry Pi and similar)

Some modules run a full Linux system. A general-purpose audio engine (Csound, Pure Data, SuperCollider, or a
JACK/ALSA program) does the DSP, while a script language polls the controls. The "firmware" is then often an update
package of scripts, engine code and a few shared objects, not an image. Ghidra is only needed for the native parts.

1. **Unpack safely.** Check the real format with `file`; the extension can lie.

   [F: observed 2026-11-03 in a third-party update package] A file named `.zip` was a gzip-compressed tar, and the
   device's update script unpacked it with `tar`.

   List the archive before extracting it. Refuse links, absolute paths and `..` entries, extract into a new empty
   folder in the case, and write a hash manifest.
2. **Boot chain.** Follow the start from the init system to the engine:
   * systemd units (`ExecStart`, `User=`, `WorkingDirectory=`), `rc.local`, cron `@reboot`;
   * then the start-up scripts, the update step, and the main program.

   Note every script that the package calls but does not contain. It lives in the base image and is an open question [O].
3. **Platform evidence without a binary.** Boot configuration (`config.txt` device-tree overlays such as `i2s`, `spi`,
   codec overlays, clock settings), mixer-control names in `amixer` calls, fstab, CPU-governor writes for the core
   count, and `readelf -A` attributes of the shipped shared objects (CPU architecture, float ABI, compiler string in
   `.comment`). Shared objects built for the wrong architecture are a finding in themselves: they cannot run on the
   device.
4. **Engine start = audio-path entry.** Find where the main program starts the engine and with which options:
   * device (`hw:0,0`), sample rate, block and buffer sizes, real-time flags;
   * for Csound: `sr`, `ksmps`, `-b`/`-B`, `-+rtaudio`;
   * for Pd: `-audiobuf`, `-callback`.

   Code that is generated at run time, such as an orchestra assembled from strings, has to be reconstructed from the
   generator. Record which parts are fixed and which come from files.
5. **DSP code.** The DSP sits in the engine language (instrument or patch files), not in native code. Read it like
   decompiler output:
   * find the block-rate main instrument or patch;
   * list its opcodes or objects, map them to building blocks ([3](03_building_blocks.md)) and recompute its constants
     ([4](04_constants.md)).

   The opcode semantics come from the engine's documentation and source *for the version on the device*. Until that
   version is known, label them [A].
6. **Control bridge.** The script side reads the ADCs (SPI), shift registers and encoders (GPIO), then writes into
   named engine channels. Examples: Csound `chnexport`/`chnset`, which the API reaches through channel pointers; Pd
   `netreceive`/`send`, or OSC. Map each hardware input to its channel name, then follow the name into the DSP code
   ([6](06_parameter_paths.md)). Smoothing, hysteresis and calibration usually live on the script side.
7. **Engine semantics are part of the evidence.** Init-time vs performance-time execution, table allocation and memory
   footprint depend on the engine version. Write such points as open questions with "what would decide it" (the
   engine source of that version, or a measurement), instead of assuming one behaviour.

The program loop is not a real-time callback: its poll rate, and so the control latency, is NOT MEASURED until
someone measures it on the device.

## Record

In `case.md`, record the callback address, block size, channel count, sample format, sample rate (with evidence) and
the call chain from the interrupt or entry point to the DSP. For Linux boards, also record the boot chain, the engine
version (or [O]), the engine options and the channel names that connect controls to DSP.
