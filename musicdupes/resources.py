"""Findet mitgelieferte Dateien - Symbol und Lizenztexte.

Wo sie liegen, haengt davon ab, wie das Programm laeuft: als Einzeldatei
entpackt PyInstaller sie beim Start nach ``sys._MEIPASS``, als Ordnerfassung
liegen sie neben der EXE, und aus dem Quellcode heraus im Projektordner.
"""

from __future__ import annotations

import os
import sys

ICON_NAME = "musicdupes.ico"
# Die LGPL-3.0 verlangt, dass ihr Text *und* der der GPL-3.0 beiliegen.
LICENCE_NAMES = (
    "LICENSE", "THIRD-PARTY-LICENSES.md",
    os.path.join("licenses", "LGPL-3.0.txt"),
    os.path.join("licenses", "GPL-3.0.txt"),
    os.path.join("ffmpeg", "LICENSE.txt"),
)


def is_onefile() -> bool:
    """Laeuft die Einzeldatei-Fassung?

    Nur dort liegen die mitgelieferten Dateien in einem Temp-Ordner, der beim
    Beenden verschwindet. In der Ordnerfassung zeigt ``sys._MEIPASS`` auf den
    ``_internal``-Ordner neben der EXE.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass or not getattr(sys, "frozen", False):
        return False
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    try:
        return os.path.commonpath([exe_dir, os.path.abspath(meipass)]) != exe_dir
    except ValueError:  # verschiedene Laufwerke
        return True


def search_roots() -> list:
    """Alle Orte, an denen mitgelieferte Dateien liegen koennen.

    Es sind bewusst mehrere: PyInstaller legt Datendateien in den
    ``_internal``-Ordner (auf den ``sys._MEIPASS`` zeigt), das Build-Skript
    kopiert Lizenztexte und Anleitungen dagegen daneben zur EXE. Auf einen
    der beiden Orte zu wetten, geht genau einmal gut.
    """
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(meipass)
    if getattr(sys, "frozen", False):
        roots.append(os.path.dirname(os.path.abspath(sys.executable)))
    roots.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    unique = []
    for root in roots:
        if root and root not in unique and os.path.isdir(root):
            unique.append(root)
    return unique


def find_bundled(relative: str) -> str:
    """Sucht eine mitgelieferte Datei in allen Orten. "" wenn nicht da."""
    for root in search_roots():
        path = os.path.join(root, relative)
        if os.path.isfile(path):
            return path
    return ""


def icon_file() -> str:
    """Pfad zum Programmsymbol, oder "" wenn es nicht mitgeliefert wurde."""
    return find_bundled(ICON_NAME)


def licence_files() -> list:
    """Alle mitgelieferten Lizenztexte, die sich finden lassen."""
    found = []
    for name in LICENCE_NAMES:
        path = find_bundled(name)
        if path:
            found.append(path)
    return found
