"""Gemeinsame Bausteine der beiden PyInstaller-Specs.

Beide Fassungen sollen dasselbe Programm enthalten. Stuende die Liste der
ausgeschlossenen Module zweimal da, liefen die Fassungen beim naechsten
Nachtrag auseinander.
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# PySide6 bringt weit mehr mit, als eine Tabellenoberflaeche braucht.
EXCLUDES = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick", "PySide6.QtWebChannel", "PySide6.QtWebSockets",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras", "PySide6.Qt3DInput", "PySide6.Qt3DLogic",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtGraphs",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQuickWidgets",
    "PySide6.QtQml", "PySide6.QtQuickControls2", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.QtBluetooth", "PySide6.QtNfc",
    "PySide6.QtPositioning", "PySide6.QtLocation", "PySide6.QtSerialPort",
    "PySide6.QtSerialBus", "PySide6.QtSensors", "PySide6.QtRemoteObjects",
    "PySide6.QtScxml", "PySide6.QtSpatialAudio", "PySide6.QtTextToSpeech",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtTest",
    "PySide6.QtSql", "PySide6.QtUiTools", "PySide6.QtStateMachine",
    "tkinter", "unittest", "pydoc_data", "distutils",
    "matplotlib", "scipy", "pandas", "PIL", "IPython", "pytest",
]


def app_version() -> str:
    """Die Versionsnummer aus ``musicdupes/__init__.py``.

    Gelesen statt importiert: der Import wuerde das halbe Programm laden.
    """
    path = os.path.join(ROOT, "musicdupes", "__init__.py")
    with open(path, encoding="utf-8") as handle:
        match = re.search(r'__version__\s*=\s*"([^"]+)"', handle.read())
    if not match:
        raise SystemExit("__version__ not found in " + path)
    return match.group(1)


def copyright_line() -> str:
    """Die Copyright-Zeile aus ``LICENSE`` - damit sie nur dort gepflegt wird."""
    with open(os.path.join(ROOT, "LICENSE"), encoding="utf-8") as handle:
        for line in handle:
            if line.strip().lower().startswith("copyright"):
                return line.strip() + " - MIT License"
    return "MIT License"


def version_info():
    """Windows-Versionsressource: Produktname und Version in der EXE.

    Ohne sie zeigt *Eigenschaften -> Details* leere Felder, und SignPath
    signiert nur Dateien, deren Produktname und -version feststehen.
    """
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable,
        VarFileInfo, VarStruct, VSVersionInfo,
    )

    version = app_version()
    numbers = [int(part) for part in re.findall(r"\d+", version)[:4]]
    numbers += [0] * (4 - len(numbers))
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=tuple(numbers), prodvers=tuple(numbers)),
        kids=[
            StringFileInfo([StringTable("040904B0", [
                StringStruct("ProductName", "MusicDupes"),
                StringStruct("FileDescription", "MusicDupes"),
                StringStruct("ProductVersion", version),
                StringStruct("FileVersion", version),
                StringStruct("InternalName", "MusicDupes"),
                StringStruct("OriginalFilename", "MusicDupes.exe"),
                StringStruct("LegalCopyright", copyright_line()),
            ])]),
            VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
        ],
    )
