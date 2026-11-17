@echo off
setlocal
py -m pip install --upgrade pip pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "ARK-Cheat-Detector" src\main.py
echo Build complete. Executable: dist\ARK-Cheat-Detector.exe
pause
