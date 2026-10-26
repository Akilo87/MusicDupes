"""CSV-Export der gefundenen Gruppen."""

from __future__ import annotations

import csv

from . import formatting, i18n
from .i18n import t
from .matcher import match_label
from .quality import club_rating

_QUALITY_KEYS = [
    "csv.file", "csv.club", "csv.rating", "csv.artist", "csv.title",
    "csv.album", "csv.format", "csv.bitrate", "csv.lossless",
    "csv.samplerate", "csv.channels", "csv.bandwidth", "csv.score",
    "csv.flags", "csv.duration_s", "csv.size", "csv.path",
]


def write_quality_csv(path: str, records: list) -> int:
    """Schreibt die Qualitaetsuebersicht aller Dateien."""
    import os

    rows = 0
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow([t(k) for k in _QUALITY_KEYS])
        for record in records:
            if record.get("error"):
                continue
            score, label = club_rating(record)
            writer.writerow([
                os.path.basename(record.get("path") or ""),
                "{:.0f}".format(score),
                label,
                record.get("artist") or "",
                record.get("title") or "",
                record.get("album") or "",
                record.get("codec") or "",
                record.get("bitrate") or 0,
                t("val.yes") if record.get("lossless") else t("val.no"),
                record.get("sample_rate") or 0,
                record.get("channels") or 0,
                "{:.0f}".format(record.get("cutoff_hz") or 0.0),
                "{:.1f}".format(record.get("quality_score") or 0.0),
                ", ".join(i18n.flag_texts(record)),
                "{:.1f}".format(record.get("duration") or 0.0),
                record.get("size") or 0,
                record.get("path") or "",
            ])
            rows += 1
    return rows

_HEADER_KEYS = [
    "csv.group", "csv.group_kind", "csv.recommendation", "csv.acoustic",
    "csv.name_similarity", "csv.match_kind", "csv.artist", "csv.title",
    "csv.album", "csv.duration", "csv.format", "csv.bitrate", "csv.lossless",
    "csv.samplerate", "csv.channels", "csv.bandwidth", "csv.score",
    "csv.flags", "csv.offset", "csv.size", "csv.path",
]


def write_csv(path: str, records: list, groups: list) -> int:
    """Schreibt alle Gruppen als CSV. Rueckgabe: Anzahl Datenzeilen."""
    rows = 0
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow([t(k) for k in _HEADER_KEYS])

        for number, group in enumerate(groups, 1):
            for member in group.members:
                record = records[member]
                writer.writerow([
                    number,
                    match_label(group.kind),
                    t("csv.keep") if member == group.best else "",
                    "{:.1f}".format(group.scores.get(member, 0.0) * 100.0),
                    ("{:.1f}".format(group.name_scores[member] * 100.0)
                     if member in group.name_scores else ""),
                    match_label(group.kinds.get(member, "")),
                    record.get("artist") or "",
                    record.get("title") or "",
                    record.get("album") or "",
                    formatting.duration(record.get("duration")),
                    record.get("codec") or "",
                    record.get("bitrate") or 0,
                    t("val.yes") if record.get("lossless") else t("val.no"),
                    record.get("sample_rate") or 0,
                    record.get("channels") or 0,
                    "{:.0f}".format(record.get("cutoff_hz") or 0.0),
                    "{:.1f}".format(record.get("quality_score") or 0.0),
                    ", ".join(i18n.flag_texts(record)),
                    "{:.2f}".format(group.offsets.get(member, 0.0)),
                    record.get("size") or 0,
                    record.get("path") or "",
                ])
                rows += 1
    return rows
