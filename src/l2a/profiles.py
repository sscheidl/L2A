"""Import profiles for `l2a open`. Standard library only (no Ghidra)."""

from __future__ import annotations

from dataclasses import dataclass

from .case import CaseError

# Executable format strings as Ghidra reports them (Program.getExecutableFormat()).
FORMAT_RAW = "Raw Binary"
FORMAT_ELF = "Executable and Linking Format (ELF)"
FORMAT_PE = "Portable Executable (PE)"


@dataclass(frozen=True)
class Profile:
    name: str
    loader: str
    format: str
    language: str | None = None  # None: the loader decides
    needs_base: bool = False
    vector_table: bool = False
    help: str = ""


PROFILES = {p.name: p for p in (
    Profile("cortex-m", "BinaryLoader", FORMAT_RAW, "ARM:LE:32:Cortex", needs_base=True, vector_table=True,
            help="raw Cortex-M image; needs --base; reads the vector table and creates the handler functions"),
    Profile("cortex-m-elf", "ElfLoader", FORMAT_ELF, "ARM:LE:32:Cortex",
            help="Cortex-M ELF with the Cortex (Thumb-only) language"),
    Profile("elf", "ElfLoader", FORMAT_ELF, help="generic ELF; language from the file unless --language"),
    Profile("pe", "PeLoader", FORMAT_PE, help="Windows PE (EXE/DLL, for example a VST3 binary)"),
    Profile("raw", "BinaryLoader", FORMAT_RAW, needs_base=True, help="raw image; needs --language and --base"),
)}


@dataclass(frozen=True)
class ImportSettings:
    profile: Profile
    language: str | None
    compiler: str | None
    base: int | None
    block_name: str

    def loader_args(self) -> list[tuple[str, str]]:
        # Ghidra skips unknown loader argument names silently, so the names carry the "-loader-" prefix
        # (docs/PYGHIDRA_CHECK.md) and `l2a open` verifies the imported program afterwards.
        if self.profile.loader != "BinaryLoader":
            return []
        return [("-loader-baseAddr", hex(self.base)), ("-loader-blockName", self.block_name)]


def parse_addr(text: str) -> int:
    """Addresses are always hexadecimal, as in Ghidra: `0x24000000` or `24000000`."""
    t = text.strip().lower()
    t = t[2:] if t.startswith("0x") else t
    try:
        return int(t, 16)
    except ValueError:
        raise CaseError(f"not a hexadecimal address: {text!r}") from None


def resolve(profile: str, language: str | None, compiler: str | None, base: str | None) -> ImportSettings:
    if profile not in PROFILES:
        raise CaseError(f"unknown profile {profile!r}; choose from {', '.join(PROFILES)}")
    p = PROFILES[profile]
    lang = language or p.language
    if p.name == "raw" and not lang:
        raise CaseError("profile raw needs --language, for example ARM:LE:32:Cortex")
    base_int = parse_addr(base) if base is not None else None
    if p.needs_base and base_int is None:
        raise CaseError(f"profile {p.name} needs --base, for example --base 0x24000000")
    if not p.needs_base and base_int is not None:
        raise CaseError(f"profile {p.name} takes its addresses from the file; --base is only for raw images")
    comp = compiler or ("default" if lang else None)
    return ImportSettings(p, lang, comp, base_int, "image")
