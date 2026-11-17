# ARK Cheat Detector

A read-only Windows utility for reviewing a user's own PC for possible ARK: Survival Evolved (Microsoft Store / Xbox app edition) cheat-related indicators.

## Research-informed indicator categories

Public ARK developer communications have specifically discussed third-party aimbot and ESP software. ARK's published Code of Conduct also identifies game-file modification and exploits as rule violations. This project therefore labels broad local indicators in these categories:

- Aim assistance terms (aimbot / triggerbot)
- ESP, wall-information, and radar terms
- Movement or weapon-modification terms (for example, speed or recoil modifications)
- Trainer and memory-modification terminology
- Code-injection terminology
- Generic cheat labels

These are **filename and visible process-name keyword checks**, not signatures for particular cheat products. They can produce false positives and can be evaded by renaming files. A match is not proof that a person cheated.

## Features

- Dark gaming-style desktop interface.
- Automatically detects all Windows fixed drives and recursively scans their accessible files after the user explicitly approves the whole-PC scan.
- Checks visible process names and filenames across accessible fixed-drive locations for the categories above.
- Reports the number of files scanned and inaccessible items skipped.
- Calculates SHA-256 for files up to 200 MiB and compares against a local signature list.
- Exports a local JSON report to Documents.
- No telemetry, uploads, file deletion, or file modification.

## Important limitations

This is not an official ARK, BattlEye, or Easy Anti-Cheat product. It cannot prove cheating or guarantee a clean system. The starter SHA-256 database is intentionally empty: no hash has been added unless it can be independently verified and safely attributed. Do not label users as cheaters based only on a local scan.

The whole-PC scan covers detected fixed drives, but it is not guaranteed to read every item: Windows-protected folders, inaccessible files, and some Microsoft Store/Xbox package locations may be skipped when Windows denies access. The scanner does not request elevation, bypass Windows permissions, inspect protected process memory, inject into processes, or change game files. It cannot reliably detect server-side exploits such as meshing, duplication, or suspicious in-game behavior. Those require server-side telemetry, game-owner investigation, or official anti-cheat systems.

## Run

Windows 10/11, Python 3.10+:

```powershell
py src\main.py
```

## Build EXE

Run `build_windows.bat`. The executable is written to `dist\ARK-Cheat-Detector.exe`.

## GitHub Actions

Run the **Build Windows app** workflow manually, or push a version tag like `v0.1.0`. The workflow uploads a Windows EXE artifact. Create a GitHub Release and attach the artifact for a public download.

## Signature database

`data/signatures.json` accepts SHA-256 strings. Only add independently verified signatures from sources you are authorized to use; record provenance and review dates when maintaining a public database. This project does not download signatures from third parties automatically.

## Research references

- [Studio Wildcard: Third-Party Software (Aimbot/ESP etc.)](https://survivetheark.com/index.php?/forums/topic/528772-community-crunch-223-genesis-transfers-fixes-and-on-the-horizon/)
- [Studio Wildcard: Code of Conduct / Hacking and Exploiting](https://store.steampowered.com/news/posts/?appids=346110&enddate=1527722920&feed=steam_community_announcements)
- [Studio Wildcard: BattlEye introduction for ARK](https://steamcommunity.com/app/346110/discussions/7/405691491126048213/)

Only scan devices and folders you own or have clear permission to inspect. Share reports only with the computer owner.
