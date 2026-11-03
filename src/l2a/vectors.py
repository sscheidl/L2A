"""Cortex-M vector table decoding. Standard library only (no Ghidra)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

SYSTEM_NAMES = {
    1: "reset", 2: "nmi", 3: "hardfault", 4: "memmanage", 5: "busfault", 6: "usagefault",
    11: "svcall", 12: "debugmon", 14: "pendsv", 15: "systick",
}
MAX_ENTRIES = 16 + 496  # ARMv7-M/v8-M allow up to 496 external interrupts


def vector_name(index: int) -> str:
    if index in SYSTEM_NAMES:
        return SYSTEM_NAMES[index]
    return f"irq{index - 16}" if index >= 16 else f"vector{index}"


@dataclass
class VectorTable:
    initial_sp: int
    length: int  # number of 32-bit slots, including the stack pointer slot
    entries: list[tuple[int, str, int]] = field(default_factory=list)  # (index, name, handler address without Thumb bit)

    def targets(self) -> dict[int, list[str]]:
        """Handler address -> vector names that point to it, in table order."""
        out: dict[int, list[str]] = {}
        for _, name, addr in self.entries:
            out.setdefault(addr, []).append(name)
        return out


def decode(words: list[int], is_code: Callable[[int], bool]) -> VectorTable:
    """Decode a vector table from its 32-bit words.

    A handler slot holds an odd (Thumb) address inside executable memory. Zero is allowed for reserved or unused
    slots. The table ends at the first slot from index 16 on that is neither, or after MAX_ENTRIES. Trailing zero
    slots (padding) are not counted, but the 16 system slots always belong to the table.
    Raises ValueError if the reset vector is not a valid handler.
    """
    if len(words) < 2:
        raise ValueError("image too small for a vector table")
    table = VectorTable(initial_sp=words[0], length=1)
    for index in range(1, min(len(words), MAX_ENTRIES)):
        value = words[index]
        valid = bool(value & 1) and is_code(value & ~1)
        if index == 1 and not valid:
            raise ValueError(f"reset vector {value:#010x} is not a Thumb address in executable memory")
        if not valid and value != 0 and index >= 16:
            break
        if value != 0:
            table.length = index + 1  # odd system slots stay in the table but are not followed
        if valid:
            table.entries.append((index, vector_name(index), value & ~1))
    table.length = min(max(table.length, 16), len(words))
    return table


def handler_name(names: list[str], addr: int) -> str:
    """Function name for a handler that one or more vectors point to."""
    if len(names) == 1:
        return f"{names[0]}_handler"
    system = [n for n in names if not n.startswith("irq")]
    if system:
        return f"{system[0]}_handler"
    return f"irq_shared_{addr:08x}"
