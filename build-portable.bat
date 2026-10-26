@echo off
rem Baut die Portable-Fassung nach dist\MusicDupes und die Einzeldatei nach dist-single
cd /d "%~dp0"
if not exist ".venv\Scripts\pyinstaller.exe" (
  echo PyInstaller fehlt. Wird nachinstalliert ...
  ".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
)
".venv\Scripts\python.exe" build_portable.py
pause
