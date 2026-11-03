# Toolchain record

Pinned tools for L2A on the owner's Windows 11 machine. Never update them as a side effect. A version change is
its own small PR that updates this file.

Recorded on 2026-11-03 by Claude.

## Ghidra 12.1.4

| Field | Value |
| --- | --- |
| Install path | `C:\Tools\ghidra_12.1.4_PUBLIC` (installed about 2026-10-20) |
| Build | `application.build.date=2026-Sep-21 1613 UTC`, Java ≥ 21 (`Ghidra/application.properties`) |
| Official release | [Ghidra_12.1.4_build](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build), published 2026-09-21 |
| Official archive | `ghidra_12.1.4_PUBLIC_20260921.zip`, 569,649,598 bytes |
| Official SHA-256 (release notes and GitHub asset digest) | `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db` |
| Local tree | 5,219 files; manifest `D:\L2A-cases\_toolchain\ghidra_12.1.4_PUBLIC.sha256`; manifest SHA-256 `a72dd1a3473f48502d5378e3a0416596dda3286d1484a24f443ba491d96928fd` |
| Internal consistency | The module JAR SHA-1 matches the shipped `bom.json`, spot check on `68000.jar`. This proves integrity only, not provenance, because `bom.json` is part of the same tree |

**Provenance check against the official archive: VERIFIED on 2026-11-03.** Steps:

1. The official ZIP was downloaded from the GitHub release (`gh release download`). Its SHA-256 matched the published
   value `ddac49f9…d4db` exactly.
2. Every file in the ZIP was hashed and compared with the local manifest. Result: **5,219 of 5,219 files identical**;
   0 changed, 0 missing, 0 extra.
3. The ZIP was deleted afterwards.

The local install is byte-identical to the official Ghidra 12.1.4 release.

## JDK 21

| Field | Value |
| --- | --- |
| Install path | `C:\Tools\jdk-21.0.12.1+1` |
| Vendor | Eclipse Adoptium, `Temurin-21.0.12.1+1` (`release` file); `java -version` reports `21.0.12.1 2026-08-18 LTS` |
| Code signature | `bin\java.exe` and `bin\server\jvm.dll` have a **valid** Authenticode signature by *Eclipse Foundation* (issuer: DigiCert Trusted G4 Code Signing RSA4096 SHA384 2021 CA1). Checked with `Get-AuthenticodeSignature` on 2026-11-03 |
| Local tree | 490 files; manifest `D:\L2A-cases\_toolchain\jdk-21.0.12.1+1.sha256`; manifest SHA-256 `8f9d0b86f545c93673122a6a6ce7b021de2c0ee3b8892220dc4aea9722cd1a8f` |

The valid vendor signature on the main binaries is sufficient provenance evidence for this private project.

## Python and PyGhidra

| Field | Value |
| --- | --- |
| Python | CPython 3.12.10 (`C:\Users\ssche\AppData\Local\Programs\Python\Python312`) |
| PyGhidra | 3.1.0, installed offline from `C:\Tools\ghidra_12.1.4_PUBLIC\Ghidra\Features\PyGhidra\pypkg\dist` into a dedicated venv (roadmap step 3; **not yet installed**) |
| JPype | 1.5.2 (`cp312-win_amd64` wheel from the same folder) |

## Re-check

Recompute a manifest and compare it with the recorded one. In Git Bash:

```bash
cd /c/Tools && find ghidra_12.1.4_PUBLIC -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum
```

A different result means files in the install changed. The per-file manifest in `D:\L2A-cases\_toolchain\` shows which ones.
