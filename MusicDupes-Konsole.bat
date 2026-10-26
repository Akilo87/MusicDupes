@echo off
rem MusicDupes mit sichtbarer Konsole - fuer Fehlersuche und --cli
cd /d "%~dp0"
".venv\Scripts\python.exe" -m musicdupes %*
pause
