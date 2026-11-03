"""Typed value decoding and search patterns. Standard library only (no Ghidra)."""

from __future__ import annotations

import math
import struct

from .case import CaseError

# name -> (struct code, size, scale); scale converts fixed point to float
TYPES = {
    "float32": ("f", 4, None),
    "float64": ("d", 8, None),
    "int8": ("b", 1, None),
    "uint8": ("B", 1, None),
    "int16": ("h", 2, None),
    "uint16": ("H", 2, None),
    "int32": ("i", 4, None),
    "uint32": ("I", 4, None),
    "q15": ("h", 2, 1 / 32768),
    "q31": ("i", 4, 1 / 2147483648),
}


def type_info(name: str) -> tuple[str, int, float | None]:
    if name not in TYPES:
        raise CaseError(f"unknown type {name!r}; choose from {', '.join(TYPES)}")
    return TYPES[name]


def fmt_value(value: float | int, scale: float | None, size: int) -> str:
    if scale is not None:
        return f"{value * scale:.9g} (raw {value})"
    if isinstance(value, float):
        return f"{value:.9g}"
    return f"{value} ({value & ((1 << (8 * size)) - 1):#0{2 + 2 * size}x})"


def decode(data: bytes, type_name: str, big_endian: bool = False, stride: int | None = None) -> list[str]:
    """Decode consecutive values; `stride` (bytes) defaults to the type size."""
    code, size, scale = type_info(type_name)
    step = stride or size
    order = ">" if big_endian else "<"
    out = []
    for off in range(0, len(data) - size + 1, step):
        (v,) = struct.unpack_from(order + code, data, off)
        out.append(fmt_value(v, scale, size))
    return out


def read_word(data: bytes, big_endian: bool = False) -> int:
    return struct.unpack((">" if big_endian else "<") + "I", data[:4])[0]


def float_bits_hint(word: int) -> str:
    """The float32 reading of a 32-bit word, if it looks like a plausible constant."""
    (f,) = struct.unpack("<f", struct.pack("<I", word & 0xFFFFFFFF))
    if math.isfinite(f) and f != 0.0 and 1e-9 <= abs(f) <= 1e9:
        return f"{f:.9g}"
    return ""


def pattern(kind: str, text: str, big_endian: bool = False) -> bytes:
    """Byte pattern for an exact search."""
    order = ">" if big_endian else "<"
    try:
        if kind == "float":
            return struct.pack(order + "f", float(text))
        if kind == "double":
            return struct.pack(order + "d", float(text))
        if kind == "int32":
            v = int(text, 0)
            return struct.pack(order + ("i" if v < 0 else "I"), v)
        if kind == "int16":
            v = int(text, 0)
            return struct.pack(order + ("h" if v < 0 else "H"), v)
        if kind == "bytes":
            return bytes.fromhex(text.replace(" ", ""))
        if kind == "string":
            return text.encode("utf-8")
    except (ValueError, struct.error) as e:
        raise CaseError(f"bad {kind} value {text!r}: {e}") from None
    raise CaseError(f"unknown search kind {kind!r}")


def find_all(data: bytes, needle: bytes, align: int = 1) -> list[int]:
    out, start = [], 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            return out
        if i % align == 0:
            out.append(i)
        start = i + 1


def find_floats(data: bytes, target: float, tol: float, base_align: int = 0, big_endian: bool = False) -> list[int]:
    """Offsets of 4-byte-aligned float32 values within `tol` of `target`.

    `base_align` is the block start address modulo 4, so alignment is by address, not by offset.
    """
    order = ">" if big_endian else "<"
    out = []
    first = (-base_align) % 4
    for off in range(first, len(data) - 3, 4):
        (v,) = struct.unpack_from(order + "f", data, off)
        if math.isfinite(v) and abs(v - target) <= tol:
            out.append(off)
    return out
