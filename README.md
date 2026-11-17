# ARK Cheat Detector

Read-only Windows utility starter for reviewing a user's own PC for possible ARK: Survival Evolved (Microsoft Store / Xbox app edition) cheat-related indicators.

## Features
- Dark gaming-style desktop interface.
- User selects folders and explicitly approves each scan.
- Checks visible process names and filenames for broad review keywords.
- Calculates SHA-256 for files up to 200 MiB and compares against a local signature list.
- Exports a local JSON report to Documents.
- No telemetry, uploads, file deletion, or file modification.

## Limitations
This is not an official ARK, BattlEye, or Easy Anti-Cheat product. It cannot prove cheating or guarantee a clean system. Broad keyword matches are weak indicators and may be false positives. The starter signature database is empty. Microsoft Store/Xbox package folders may be protected; choose only folders Windows allows you to inspect. The app does not bypass permissions, inspect protected process memory, inject into processes, or change game files.

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
`data/signatures.json` accepts SHA-256 strings. Only add independently verified signatures from sources you are authorized to use; record provenance and review dates when maintaining a public database.

Only scan devices and folders you own or have clear permission to inspect. Share reports only with the computer owner.
