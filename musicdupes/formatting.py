"""Kleine Umrechnungen fuer die Anzeige."""

from __future__ import annotations


def duration(seconds: float) -> str:
    seconds = max(0.0, float(seconds or 0.0))
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return "{}:{:02d}:{:02d}".format(hours, minutes, secs)
    return "{}:{:02d}".format(minutes, secs)


def filesize(num_bytes: int) -> str:
    value = float(num_bytes or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0 or unit == "GB":
            if unit == "B":
                return "{:.0f} {}".format(value, unit)
            return "{:.1f} {}".format(value, unit)
        value /= 1024.0
    return "{:.1f} GB".format(value)


def bitrate(record: dict) -> str:
    value = int(record.get("bitrate") or 0)
    if value <= 0:
        return "-"
    suffix = "~" if record.get("bitrate_is_container") else ""
    return "{}{} kbps".format(suffix, value)


def bandwidth(cutoff_hz: float) -> str:
    value = float(cutoff_hz or 0.0)
    if value <= 0:
        return "-"
    return "{:.1f} kHz".format(value / 1000.0)


def percent(value: float) -> str:
    return "{:.1f} %".format(float(value or 0.0) * 100.0)


def offset(seconds: float) -> str:
    value = float(seconds or 0.0)
    if abs(value) < 0.05:
        return "-"
    return "{:+.1f} s".format(value)


def display_name(record: dict) -> str:
    """Interpret - Titel, sonst der Dateiname."""
    import os

    artist = (record.get("artist") or "").strip()
    title = (record.get("title") or "").strip()
    if artist and title:
        return "{} - {}".format(artist, title)
    if title:
        return title
    return os.path.basename(record.get("path") or "")


def search_text(record: dict) -> str:
    """Wonach das Filterfeld sucht - in allen drei Reitern dasselbe."""
    return " ".join([
        record.get("artist") or "", record.get("title") or "",
        record.get("album") or "", record.get("path") or "",
    ]).lower()
