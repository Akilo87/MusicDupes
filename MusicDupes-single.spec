# -*- mode: python ; coding: utf-8 -*-
"""Alles in einer einzigen EXE - die Fassung zum Herunterladen und Starten.

Gemessen gegen die Ordnerfassung: 125 MB statt 306 MB entpackt, Start in
1,5 s statt 0,3 s, Temp wird beim Beenden sauber aufgeraeumt. Die gut
sekuendlich laengere Startzeit ist der Preis dafuer, dass Anwender nur eine
einzige Datei vor sich haben. Die Worker-Prozesse entpacken nichts erneut,
sie nutzen den Temp-Ordner des Hauptprozesses mit.

Die Ordnerfassung bleibt trotzdem bestehen: sie startet schneller, und bei
ihr lassen sich die LGPL-Bibliotheken (Qt, ffmpeg) als einzelne Dateien
austauschen - was die LGPL ausdruecklich vorsieht.

Der Unterschied zur Ordnerfassung: keine COLLECT-Stufe, stattdessen landet
alles im Archiv der EXE und wird bei jedem Start in einen Temp-Ordner
entpackt. ffmpeg kommt dabei als rohe DATA-Eintraege dazu und nicht ueber
``datas``, weil PyInstaller die DLLs sonst zusaetzlich analysiert und ein
zweites Mal einpackt.
"""

import os
import sys

sys.path.insert(0, os.path.join(SPECPATH, "packaging"))
from pyinstaller_common import EXCLUDES, version_info  # noqa: E402

ROOT = os.path.abspath(SPECPATH)
# build_portable.py reicht den fertig bestueckten ffmpeg-Ordner der
# Ordnerfassung herein; direkt aufgerufen gilt der Projektordner.
FFMPEG_DIR = os.environ.get("MUSICDUPES_FFMPEG_DIR") or os.path.join(ROOT, "ffmpeg")
if not os.path.isfile(os.path.join(FFMPEG_DIR, "ffmpeg.exe")):
    raise SystemExit("ffmpeg.exe not found in " + FFMPEG_DIR)

ICON = os.path.join(ROOT, "musicdupes.ico")

a = Analysis(
    [os.path.join(ROOT, "MusicDupes_start.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=["musicdupes"],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
)

# ffmpeg als reine Nutzdaten anhaengen, ohne Abhaengigkeitsanalyse.
for name in sorted(os.listdir(FFMPEG_DIR)):
    lower = name.lower()
    if lower.startswith("ffplay"):
        continue
    if lower.endswith((".exe", ".dll", ".txt")):
        a.datas += [(
            "ffmpeg/" + name, os.path.join(FFMPEG_DIR, name), "DATA"
        )]

# Lizenztexte muessen mit in die Datei: bei der Einzeldatei-Fassung gibt es
# sonst keinen Ort, an dem sie der Auslieferung beiliegen koennten. Der
# Lizenzdialog im Programm schreibt sie auf Wunsch heraus.
for name in ("LICENSE", "THIRD-PARTY-LICENSES.md", "musicdupes.ico",
             "licenses/LGPL-3.0.txt", "licenses/GPL-3.0.txt"):
    full = os.path.join(ROOT, *name.split("/"))
    if not os.path.isfile(full):
        raise SystemExit("Missing file for the single-file build: " + full)
    a.datas += [(name, full, "DATA")]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MusicDupes",
    icon=ICON,
    version=version_info(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
