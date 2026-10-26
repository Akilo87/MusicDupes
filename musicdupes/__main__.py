"""Einstiegspunkt.

Ohne Argumente startet die Oberflaeche. Mit ``--cli ORDNER`` laeuft derselbe
Scan auf der Konsole - praktisch fuer sehr grosse Sammlungen oder Skripte.

Wichtig fuer Windows: die Worker-Prozesse importieren dieses Modul erneut.
Alles, was etwas *tut*, muss deshalb hinter dem __main__-Schutz stehen, sonst
startet jeder Worker seinerseits das Programm.
"""

from __future__ import annotations

import argparse
import multiprocessing
import os
import sys

from . import i18n
from .i18n import t

# Muessen zu den Voreinstellungen der Oberflaeche passen.
DEFAULT_AUDIO = 90
DEFAULT_META = 82


def _set_taskbar_identity() -> None:
    """Sagt Windows, dass dies eine eigenstaendige Anwendung ist.

    Ohne eigene AppUserModelID haengt Windows das Fenster an den Prozess,
    der es gestartet hat, und nimmt dessen Symbol fuer die Taskleiste.

    Nicht im Store-Paket: dort vergibt Windows die ID selbst, und eine
    eigene wuerde das Fenster von seiner angehefteten Kachel trennen.
    """
    from .cache import is_packaged

    if is_packaged():
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "MusicDupes.MusicDupes"
        )
    except Exception:
        pass


def _run_gui() -> int:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from .gui.main_window import MainWindow
    from .resources import icon_file

    _set_taskbar_identity()

    app = QApplication(sys.argv)
    app.setApplicationName("MusicDupes")
    app.setOrganizationName("MusicDupes")

    # Das Symbol in der EXE gilt nur fuer die Datei im Explorer. Taskleiste
    # und Fensterleiste nehmen das Fenstersymbol - das muss Qt gesetzt
    # bekommen, sonst zeigt es seinen eigenen Platzhalter.
    path = icon_file()
    if path:
        icon = QIcon(path)
        if not icon.isNull():
            app.setWindowIcon(icon)

    window = MainWindow()
    window.show()
    return app.exec()


def _run_cli(args: argparse.Namespace) -> int:
    # Windows-Konsolen laufen oft noch auf einer 8-Bit-Codepage, an der
    # Umlaute und Gedankenstriche zerbrechen.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    from . import formatting, i18n as _i18n
    from .engine import ScanEngine
    from .exporting import write_csv
    from .matcher import redundant_bytes

    engine = ScanEngine()
    last_stage = [""]

    def progress(stage: str, done: int, total: int) -> None:
        # Die Engine meldet Schlüssel, keine fertigen Sätze.
        label = t(stage)
        if stage != last_stage[0]:
            last_stage[0] = stage
            print("\n{} ...".format(label), end="", flush=True)
        elif total:
            print("\r{} ... {}/{}".format(label, done, total), end="", flush=True)

    result = engine.scan(
        args.folder,
        recursive=not args.flat,
        audio_threshold=args.audio / 100.0,
        meta_threshold=args.meta / 100.0,
        use_metadata=not args.no_metadata,
        progress=progress,
    )
    print()

    if result.message and not result.records:
        print(result.message)
        return 1

    for number, group in enumerate(result.groups, 1):
        best = result.records[group.best]
        print("\n" + t(
            "cli.group_head",
            number=number, kind=group.label,
            name=formatting.display_name(best), count=len(group.members),
        ))
        for member in group.members:
            record = result.records[member]
            flags = ", ".join(_i18n.flag_texts(record))
            if member in group.name_scores:
                marker = t("cli.by_name", value=group.name_scores[member] * 100)
                flags = (marker + " " + flags).strip()
            print("  {:>5.0f} %  {:<46} {:>9} {:>10} Q={:>5.1f}  {}{}".format(
                group.scores.get(member, 0.0) * 100,
                os.path.basename(record.get("path") or "")[:46],
                formatting.bitrate(record),
                formatting.bandwidth(record.get("cutoff_hz")),
                record.get("quality_score") or 0.0,
                flags,
                t("cli.keep") if member == group.best else "",
            ))

    broken = [r for r in result.records if r.get("error")]
    if broken:
        print("\n" + t("cli.unreadable", count=len(broken)))
        for record in broken:
            print("  {:<50} {}".format(
                os.path.basename(record.get("path") or "")[:50],
                t(record.get("error") or ""),
            ))

    stats = result.stats
    print("\n" + t(
        "cli.summary",
        tracks=stats.get("tracks", 0), groups=len(result.groups),
        dupes=stats.get("duplicates", 0), versions=stats.get("versions", 0),
        wasted=formatting.filesize(redundant_bytes(result.records, result.groups)),
        seconds=stats.get("seconds", 0.0),
    ))

    if args.csv:
        rows = write_csv(args.csv, result.records, result.groups)
        print(t("cli.csv_written", rows=rows, path=args.csv))
    return 0


def main() -> int:
    # Die Sprache muss vor dem Aufbau der Hilfe feststehen.
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--lang", default="auto")
    known, _rest = pre.parse_known_args()
    i18n.set_language(known.lang)

    parser = argparse.ArgumentParser(
        prog="MusicDupes", description=t("cli.description"),
    )
    parser.add_argument("--cli", dest="folder", metavar="FOLDER",
                        help=t("cli.help_folder"))
    parser.add_argument("--audio", type=int, default=DEFAULT_AUDIO, metavar="PERCENT",
                        help=t("cli.help_audio", value=DEFAULT_AUDIO))
    parser.add_argument("--meta", type=int, default=DEFAULT_META, metavar="PERCENT",
                        help=t("cli.help_meta", value=DEFAULT_META))
    parser.add_argument("--no-metadata", action="store_true",
                        help=t("cli.help_nometa"))
    parser.add_argument("--flat", action="store_true", help=t("cli.help_flat"))
    parser.add_argument("--csv", metavar="FILE", help=t("cli.help_csv"))
    parser.add_argument("--lang", default="auto", choices=["auto", "de", "en"],
                        help=t("cli.help_lang"))
    args = parser.parse_args()

    if args.folder:
        return _run_cli(args)
    return _run_gui()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
