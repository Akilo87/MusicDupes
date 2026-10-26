@echo off
rem MusicDupes starten (ohne Konsolenfenster). /d setzt den Arbeitsordner,
rem sonst findet Python das Paket nicht, wenn die Verknuepfung woanders startet.
start "" /d "%~dp0" "%~dp0.venv\Scripts\pythonw.exe" -m musicdupes
