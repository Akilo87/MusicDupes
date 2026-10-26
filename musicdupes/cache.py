"""SQLite-Ablage der Analyseergebnisse.

Der teure Teil ist das Dekodieren. Solange sich Groesse und Zeitstempel einer
Datei nicht geaendert haben, wird das Ergebnis wiederverwendet - ein zweiter
Durchlauf ueber dieselbe Sammlung dauert dadurch Sekunden statt Minuten.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from typing import Iterable, Iterator, Optional

SCHEMA_VERSION = 4

_COLUMNS = (
    "path", "size", "mtime", "file_hash", "audio_hash",
    "codec", "codec_long", "container", "duration", "bitrate",
    "bitrate_is_container", "sample_rate", "channels", "bits_per_sample",
    "lossless", "artist", "title", "album", "track_no", "date", "genre",
    "cutoff_hz", "peak_dbfs", "rms_dbfs", "clip_ratio", "quality_score",
    "quality_flags", "fingerprint", "fp_count", "profile", "profile_frames",
    "decoded_seconds", "error", "analyzed_at",
)

_CREATE = """
CREATE TABLE IF NOT EXISTS tracks (
    path                 TEXT PRIMARY KEY,
    size                 INTEGER NOT NULL DEFAULT 0,
    mtime                REAL    NOT NULL DEFAULT 0,
    file_hash            TEXT    NOT NULL DEFAULT '',
    audio_hash           TEXT    NOT NULL DEFAULT '',
    codec                TEXT    NOT NULL DEFAULT '',
    codec_long           TEXT    NOT NULL DEFAULT '',
    container            TEXT    NOT NULL DEFAULT '',
    duration             REAL    NOT NULL DEFAULT 0,
    bitrate              INTEGER NOT NULL DEFAULT 0,
    bitrate_is_container INTEGER NOT NULL DEFAULT 0,
    sample_rate          INTEGER NOT NULL DEFAULT 0,
    channels             INTEGER NOT NULL DEFAULT 0,
    bits_per_sample      INTEGER NOT NULL DEFAULT 0,
    lossless             INTEGER NOT NULL DEFAULT 0,
    artist               TEXT    NOT NULL DEFAULT '',
    title                TEXT    NOT NULL DEFAULT '',
    album                TEXT    NOT NULL DEFAULT '',
    track_no             TEXT    NOT NULL DEFAULT '',
    date                 TEXT    NOT NULL DEFAULT '',
    genre                TEXT    NOT NULL DEFAULT '',
    cutoff_hz            REAL    NOT NULL DEFAULT 0,
    peak_dbfs            REAL    NOT NULL DEFAULT 0,
    rms_dbfs             REAL    NOT NULL DEFAULT 0,
    clip_ratio           REAL    NOT NULL DEFAULT 0,
    quality_score        REAL    NOT NULL DEFAULT 0,
    quality_flags        TEXT    NOT NULL DEFAULT '[]',
    fingerprint          BLOB,
    fp_count             INTEGER NOT NULL DEFAULT 0,
    profile              BLOB,
    profile_frames       INTEGER NOT NULL DEFAULT 0,
    decoded_seconds      REAL    NOT NULL DEFAULT 0,
    error                TEXT    NOT NULL DEFAULT '',
    analyzed_at          REAL    NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_file_hash  ON tracks(file_hash);
CREATE INDEX IF NOT EXISTS idx_audio_hash ON tracks(audio_hash);
"""


def is_packaged() -> bool:
    """Laeuft das Programm aus einem MSIX-Paket (Microsoft Store)?

    Dort ist der Installationsordner schreibgeschuetzt, der Cache muss also
    ins Benutzerprofil. ``GetCurrentPackageFullName`` meldet 15700
    (APPMODEL_ERROR_NO_PACKAGE), wenn kein Paket dahintersteht.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        length = wintypes.UINT(0)
        code = ctypes.windll.kernel32.GetCurrentPackageFullName(
            ctypes.byref(length), None
        )
        return code != 15700
    except Exception:
        return False


def _writable(folder: str) -> bool:
    probe = os.path.join(folder, ".musicdupes-write-test")
    try:
        os.makedirs(folder, exist_ok=True)
        with open(probe, "w", encoding="utf-8") as handle:
            handle.write("x")
        os.remove(probe)
        return True
    except OSError:
        return False


def app_folder() -> str:
    """Der Ordner, in dem das Programm seine eigenen Daten ablegt.

    In der Portable-Fassung ist das der Ordner neben der EXE - nicht das
    Benutzerprofil und schon gar nicht das Entpackverzeichnis, das beim
    Beenden verschwindet. So wandert der Cache mit, wenn jemand den Ordner
    auf einen Stick kopiert.

    Aus dem Store installiert, oder wenn jemand das Paket nach
    "Programme" gelegt hat, ist daneben nichts zu schreiben. Dann weicht
    alles ins Benutzerprofil aus.
    """
    if not is_packaged():
        if getattr(sys, "frozen", False):
            beside = os.path.dirname(os.path.abspath(sys.executable))
        else:
            beside = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if _writable(beside):
            return beside

    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "MusicDupes")


def default_path() -> str:
    folder = os.path.join(app_folder(), "data")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "cache.db")


def settings_path() -> str:
    """Einstellungsdatei - bewusst eine INI und nicht die Registry."""
    folder = os.path.join(app_folder(), "data")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "MusicDupes.ini")


class Cache:
    """Duenne Schicht ueber SQLite. Nicht threadsicher - je Thread eine Instanz."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or default_path()
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._ensure_schema()
        self._normalise_paths()

    def _normalise_paths(self) -> None:
        """Gleicht alte Eintraege an die Windows-Schreibweise an.

        Fruehere Versionen speicherten Pfade so, wie der Auswahldialog sie
        lieferte ("V:/Musik\\Album\\Titel.flac"). Heute wird der Ordner vorher
        vereinheitlicht. Ohne diese Angleichung passte kein alter Eintrag mehr
        und die ganze Sammlung wuerde neu analysiert. Kollidiert ein Eintrag
        mit einem schon vorhandenen, gewinnt der vorhandene.
        """
        if os.sep != "\\":
            return
        self.conn.execute(
            "UPDATE OR IGNORE tracks SET path = replace(path, '/', '\\') "
            "WHERE path LIKE '%/%'"
        )
        self.conn.execute("DELETE FROM tracks WHERE path LIKE '%/%'")
        self.conn.commit()

    def _ensure_schema(self) -> None:
        cur = self.conn.execute("PRAGMA user_version")
        version = int(cur.fetchone()[0])
        if version and version != SCHEMA_VERSION:
            # Aeltere Fingerprints sind mit den heutigen nicht vergleichbar;
            # neu einlesen ist billiger als eine Migration zu erfinden.
            self.conn.executescript("DROP TABLE IF EXISTS tracks")
            version = 0
        self.conn.executescript(_CREATE)
        if version != SCHEMA_VERSION:
            self.conn.execute("PRAGMA user_version = {}".format(SCHEMA_VERSION))
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.commit()
        finally:
            self.conn.close()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- Lesen --------------------------------------------------------------

    def fresh_paths(self, entries: Iterable[tuple]) -> set:
        """Liefert die Pfade, deren Eintrag noch zu Groesse und mtime passt."""
        wanted = {}
        for path, size, mtime in entries:
            wanted[path] = (int(size), float(mtime))
        if not wanted:
            return set()

        fresh = set()
        cur = self.conn.execute(
            "SELECT path, size, mtime, error FROM tracks"
        )
        for row in cur:
            expect = wanted.get(row["path"])
            if expect is None:
                continue
            # Fehlerhafte Dateien noch einmal versuchen - vielleicht lag es
            # an einem fehlenden Codec, der inzwischen da ist.
            if row["error"]:
                continue
            if row["size"] == expect[0] and abs(row["mtime"] - expect[1]) < 1e-6:
                fresh.add(row["path"])
        return fresh

    def load(self, paths: Iterable[str]) -> Iterator[dict]:
        """Laedt Eintraege in Bloecken (SQLite begrenzt die Parameterzahl)."""
        chunk: list[str] = []
        for path in paths:
            chunk.append(path)
            if len(chunk) >= 400:
                yield from self._load_chunk(chunk)
                chunk = []
        if chunk:
            yield from self._load_chunk(chunk)

    def _load_chunk(self, paths: list) -> Iterator[dict]:
        marks = ",".join("?" * len(paths))
        cur = self.conn.execute(
            "SELECT * FROM tracks WHERE path IN ({})".format(marks), paths
        )
        for row in cur:
            yield self._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        data = {key: row[key] for key in row.keys()}
        data["lossless"] = bool(data.get("lossless"))
        data["bitrate_is_container"] = bool(data.get("bitrate_is_container"))
        try:
            data["quality_flags"] = json.loads(data.get("quality_flags") or "[]")
        except (ValueError, TypeError):
            data["quality_flags"] = []
        data["fingerprint"] = bytes(data.get("fingerprint") or b"")
        data["profile"] = bytes(data.get("profile") or b"")
        return data

    # -- Schreiben ----------------------------------------------------------

    def store_many(self, results: Iterable[dict]) -> int:
        rows = [self._to_row(item) for item in results]
        if not rows:
            return 0
        marks = ",".join("?" * len(_COLUMNS))
        self.conn.executemany(
            "INSERT OR REPLACE INTO tracks ({}) VALUES ({})".format(
                ",".join(_COLUMNS), marks
            ),
            rows,
        )
        self.conn.commit()
        return len(rows)

    @staticmethod
    def _to_row(item: dict) -> tuple:
        values = []
        for column in _COLUMNS:
            if column == "quality_flags":
                values.append(json.dumps(item.get("quality_flags") or []))
            elif column == "analyzed_at":
                values.append(item.get("analyzed_at") or time.time())
            elif column in ("lossless", "bitrate_is_container"):
                values.append(1 if item.get(column) else 0)
            elif column in ("fingerprint", "profile"):
                values.append(item.get(column) or b"")
            elif column == "path":
                values.append(item.get("path") or "")
            else:
                default = "" if column in (
                    "file_hash", "audio_hash", "codec", "codec_long",
                    "container", "artist", "title", "album", "track_no",
                    "date", "genre", "error",
                ) else 0
                values.append(item.get(column, default) or default)
        return tuple(values)

    def clear(self) -> None:
        self.conn.execute("DELETE FROM tracks")
        self.conn.commit()
        self.conn.execute("VACUUM")

    def stats(self) -> dict:
        cur = self.conn.execute(
            "SELECT COUNT(*) AS n, SUM(LENGTH(fingerprint)) AS fp,"
            " SUM(LENGTH(profile)) AS pr FROM tracks"
        )
        row = cur.fetchone()
        size = os.path.getsize(self.path) if os.path.exists(self.path) else 0
        return {
            "tracks": int(row["n"] or 0),
            "fingerprint_bytes": int(row["fp"] or 0),
            "profile_bytes": int(row["pr"] or 0),
            "db_bytes": size,
        }
