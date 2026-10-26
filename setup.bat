@echo off
rem Einmalige Einrichtung: virtuelle Umgebung anlegen und Pakete laden
cd /d "%~dp0"
echo Richte virtuelle Umgebung ein ...
python -m venv .venv
if errorlevel 1 goto fehler
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fehler
echo.
echo Fertig. MusicDupes.bat startet das Programm.
goto ende
:fehler
echo.
echo Einrichtung fehlgeschlagen. Ist Python 3.10 oder neuer installiert?
:ende
pause
