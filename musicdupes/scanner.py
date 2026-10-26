"""Dateisuche im gewaehlten Ordner."""

from __future__ import annotations

import os
from typing import Iterator

from .audio import AUDIO_EXTENSIONS

# Ordner, in denen keine Musik liegt, die uns interessiert.
_SKIP_DIRS = {
    "$recycle.bin", "system volume information", ".git", ".svn",
    "__pycache__", ".cache", "node_modules",
}


def find_audio_files(
    root: str,
    recursive: bool = True,
    should_stop=None,
) -> Iterator[tuple]:
    """Liefert (Pfad, Groesse, mtime) fuer jede Audiodatei unter ``root``."""
    for folder, dirs, names in os.walk(root):
        if should_stop is not None and should_stop():
            return

        dirs[:] = [
            d for d in dirs
            if d.lower() not in _SKIP_DIRS and not d.startswith(".")
        ]
        if not recursive:
            dirs[:] = []

        for name in names:
            extension = os.path.splitext(name)[1].lower()
            if extension not in AUDIO_EXTENSIONS:
                continue
            path = os.path.join(folder, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            if stat.st_size <= 0:
                continue
            yield path, int(stat.st_size), float(stat.st_mtime)
