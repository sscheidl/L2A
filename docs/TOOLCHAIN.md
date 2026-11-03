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
| PyGhidra | 3.1.0, installed offline on 2026-11-03 from `C:\Tools\ghidra_12.1.4_PUBLIC\Ghidra\Features\PyGhidra\pypkg\dist` into the venv `D:\L2A-cases\_toolchain\pyghidra-venv` (`pip install --no-index --find-links <dist> pyghidra==3.1.0`). Wheel SHA-256 `f4c138098e63f7d6b3648ff8fba0619aabf088ce1d1e8692808fa1df9d8921a0` |
| JPype | 1.5.2 (`cp312-win_amd64` wheel from the same folder), SHA-256 `c7b1c2d76d211cab60be16505d32a6b3c9fffc51ce79c68e81a3d48e5effff2d` |
| packaging | 25.0 (same folder), SHA-256 `29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484` |
| setuptools | 80.9.0 (same folder), SHA-256 `062d34222ad13e0cc312a4c02d73f059e86a4acbfbdea8f8f76b28c99f306922`; only for the offline editable install of `l2a` ([L2A_CLI.md](L2A_CLI.md)) |
| Environment | Set `GHIDRA_INSTALL_DIR=C:\Tools\ghidra_12.1.4_PUBLIC` and `JAVA_HOME=C:\Tools\jdk-21.0.12.1+1`; run the venv Python with `-I`. Check results: [PYGHIDRA_CHECK.md](PYGHIDRA_CHECK.md) |

The wheels are part of the verified Ghidra tree, so their provenance follows from the Ghidra check above.
The venv lies outside the repository and is not a pinned artefact itself; it can be recreated with the command above.

## Re-check

Recompute a manifest and compare it with the recorded one. In Git Bash:

```bash
cd /c/Tools && find ghidra_12.1.4_PUBLIC -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum
```

A different result means files in the install changed. The per-file manifest in `D:\L2A-cases\_toolchain\` shows which ones.
