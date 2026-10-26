# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Bauplan fuer die Ordnerfassung (PyInstaller 6.x).

Neben der Einzeldatei (``MusicDupes-single.spec``) gibt es bewusst auch diese
Fassung als Ordner ("onedir"):

* Sie startet schneller, weil sich nichts erst in den Temp-Ordner entpacken
  muss.
* Qt und ffmpeg liegen darin als einzelne Dateien und lassen sich austauschen
  - was die LGPL ausdruecklich vorsieht.

Gebaut wird ueber ``build_portable.py``, das danach ffmpeg, Anleitungen und
Lizenztexte danebenlegt.
"""

import os
import sys

sys.path.insert(0, os.path.join(SPECPATH, "packaging"))
from pyinstaller_common import EXCLUDES, version_info  # noqa: E402

ROOT = os.path.abspath(SPECPATH)

# -- ffmpeg NICHT hier einsammeln ------------------------------------------
# ffmpeg wird bewusst erst nach dem Build danebenkopiert (siehe
# build_portable.py). Gibt man die DLLs hier als "datas" mit, stuft
# PyInstaller sie als Binaerdateien ein, analysiert ihre Abhaengigkeiten und
# legt sie ein zweites Mal im Hauptordner ab - allein avcodec sind 95 MB, die
# das Paket doppelt mit sich schleppen wuerde.
extra_data = []

# Das Symbol wird zur Laufzeit gebraucht: die EXE-Ressource gilt nur fuer
# die Datei im Explorer, Taskleiste und Fensterleiste brauchen die Datei.
ICON = os.path.join(ROOT, "musicdupes.ico")
if os.path.isfile(ICON):
    extra_data.append((ICON, "."))

a = Analysis(
    [os.path.join(ROOT, "MusicDupes_start.py")],
    pathex=[ROOT],
    binaries=[],
    datas=extra_data,
    hiddenimports=["musicdupes"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# Nur eine EXE, ohne Konsolenfenster. Eine zusaetzliche Konsolenfassung
# waere fuer Anwender nur ein zweiter Startknopf, bei dem sie raten
# muessten, welcher der richtige ist. Unbehandelte Fehler zeigt
# PyInstaller auch ohne Konsole als Meldungsfenster an.
exe_gui = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
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

coll = COLLECT(
    exe_gui,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MusicDupes",
)
