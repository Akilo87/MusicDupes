"""ffmpeg/ffprobe-Anbindung: Metadaten lesen und Audio streamend dekodieren."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Iterator, Optional

import numpy as np

from .i18n import t

# Alle Formate, die wir einlesen. ffmpeg kann mehr, aber das hier ist Musik.
AUDIO_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".m4a", ".aac", ".ogg", ".oga", ".opus",
    ".wma", ".aiff", ".aif", ".aifc", ".alac", ".ape", ".wv", ".mpc",
    ".m4b", ".mka", ".dsf", ".dff", ".tta", ".ac3", ".eac3", ".dts",
    ".amr", ".mp4", ".webm",
}

LOSSLESS_CODECS = {
    "flac", "alac", "pcm_s16le", "pcm_s24le", "pcm_s32le", "pcm_f32le",
    "pcm_f64le", "pcm_s16be", "pcm_s24be", "pcm_s32be", "pcm_u8",
    "ape", "wavpack", "tta", "shorten", "truehd", "mlp",
    "dsd_lsbf", "dsd_msbf", "dsd_lsbf_planar", "dsd_msbf_planar",
}

_CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


class AudioError(RuntimeError):
    """Fehler mit Textschluessel statt fertigem Satz.

    Die Analyse laeuft in Worker-Prozessen, die die eingestellte Sprache
    nicht kennen, und ihr Ergebnis landet im Cache. Gespeichert wird deshalb
    der Schluessel; uebersetzt wird erst beim Anzeigen.
    """

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


class FFmpegMissing(AudioError):
    pass


def _bundle_dirs() -> list:
    """Orte, an denen ein mitgeliefertes ffmpeg liegen kann."""
    places = []
    # Von PyInstaller entpackte Daten.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        places.append(os.path.join(meipass, "ffmpeg"))
    # Neben der EXE bzw. neben dem Paket.
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    places.append(os.path.join(exe_dir, "ffmpeg"))
    project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    places.append(os.path.join(project, "ffmpeg"))
    return places


def _find_tool(name: str) -> Optional[str]:
    """Sucht ffmpeg bzw. ffprobe.

    Ein mitgeliefertes Exemplar hat Vorrang vor dem System: in der
    Portable-Fassung soll das Programm genau die Version benutzen, mit der es
    ausgeliefert wurde - und nicht ein zufaellig vorhandenes, womoeglich
    unvollstaendiges ffmpeg aus dem PATH.
    """
    filename = name + ".exe" if sys.platform == "win32" else name
    for folder in _bundle_dirs():
        candidate = os.path.join(folder, filename)
        if os.path.isfile(candidate):
            return candidate

    found = shutil.which(name)
    if found:
        return found

    candidates = [
        r"C:\Program Files\ffmpeg\bin\{}.exe".format(name),
        r"C:\Program Files (x86)\ffmpeg\bin\{}.exe".format(name),
        r"C:\ffmpeg\bin\{}.exe".format(name),
        os.path.join(os.path.dirname(sys.executable), filename),
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None


_FFMPEG: Optional[str] = None
_FFPROBE: Optional[str] = None


def ffmpeg_path() -> str:
    global _FFMPEG
    if _FFMPEG is None:
        _FFMPEG = _find_tool("ffmpeg")
    if not _FFMPEG:
        raise FFmpegMissing("engine.ffmpeg_missing")
    return _FFMPEG


def ffprobe_path() -> str:
    global _FFPROBE
    if _FFPROBE is None:
        _FFPROBE = _find_tool("ffprobe")
    if not _FFPROBE:
        raise FFmpegMissing("engine.ffprobe_missing")
    return _FFPROBE


def tools_available() -> tuple[bool, str]:
    """Prueft einmalig, ob ffmpeg + ffprobe erreichbar sind."""
    try:
        ffmpeg_path()
        ffprobe_path()
    except FFmpegMissing as exc:
        return False, t(exc.key)
    return True, ""


@dataclass
class TechInfo:
    """Technische Kenndaten, wie sie im Container stehen."""

    codec: str = ""
    codec_long: str = ""
    container: str = ""
    duration: float = 0.0
    bitrate: int = 0            # kbps
    bitrate_is_container: bool = False
    sample_rate: int = 0
    channels: int = 0
    bits_per_sample: int = 0
    lossless: bool = False
    tags: dict = field(default_factory=dict)


def _first(source: dict, *keys: str) -> str:
    lowered = {str(k).lower(): v for k, v in source.items()}
    for key in keys:
        val = lowered.get(key.lower())
        if val:
            return str(val).strip()
    return ""


def probe(path: str) -> TechInfo:
    """Liest Container- und Streaminfos via ffprobe."""
    cmd = [
        ffprobe_path(), "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", "-select_streams", "a:0", path,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, creationflags=_CREATE_NO_WINDOW, timeout=120
        )
    except subprocess.TimeoutExpired:
        raise AudioError("engine.ffprobe_timeout") from None
    if proc.returncode != 0 or not proc.stdout:
        raise AudioError("engine.ffprobe_failed")

    data = json.loads(proc.stdout.decode("utf-8", "replace"))
    streams = data.get("streams") or []
    if not streams:
        raise AudioError("engine.no_stream")
    stream = streams[0]
    fmt = data.get("format") or {}

    info = TechInfo()
    info.codec = str(stream.get("codec_name") or "")
    info.codec_long = str(stream.get("codec_long_name") or "")
    info.container = str(fmt.get("format_name") or "").split(",")[0]

    for src in (stream, fmt):
        try:
            dur = float(src.get("duration") or 0.0)
        except (TypeError, ValueError):
            dur = 0.0
        if dur > 0:
            info.duration = dur
            break

    try:
        if stream.get("bit_rate"):
            info.bitrate = int(round(int(stream["bit_rate"]) / 1000))
        elif fmt.get("bit_rate"):
            info.bitrate = int(round(int(fmt["bit_rate"]) / 1000))
            info.bitrate_is_container = True
    except (TypeError, ValueError):
        info.bitrate = 0

    try:
        info.sample_rate = int(stream.get("sample_rate") or 0)
    except (TypeError, ValueError):
        info.sample_rate = 0
    try:
        info.channels = int(stream.get("channels") or 0)
    except (TypeError, ValueError):
        info.channels = 0

    for key in ("bits_per_raw_sample", "bits_per_sample"):
        try:
            bits = int(stream.get(key) or 0)
        except (TypeError, ValueError):
            bits = 0
        if bits > 0:
            info.bits_per_sample = bits
            break

    info.lossless = info.codec.lower() in LOSSLESS_CODECS

    raw_tags = {}
    raw_tags.update(fmt.get("tags") or {})
    raw_tags.update(stream.get("tags") or {})
    info.tags = {
        "artist": _first(raw_tags, "artist", "album_artist", "albumartist", "performer"),
        "title": _first(raw_tags, "title"),
        "album": _first(raw_tags, "album"),
        "track": _first(raw_tags, "track", "tracknumber"),
        "date": _first(raw_tags, "date", "year", "originalyear"),
        "genre": _first(raw_tags, "genre"),
    }
    return info


def decode_blocks(
    path: str,
    sample_rate: int,
    block_samples: int = 1 << 18,
    max_seconds: float = 0.0,
) -> Iterator[np.ndarray]:
    """Dekodiert die Datei zu Mono-float32 und liefert sie blockweise.

    Bewusst streamend statt am Stueck: bei 16 parallelen Workern und langen
    DJ-Mixes waeren das sonst schnell mehrere GB im RAM.
    """
    cmd = [
        ffmpeg_path(), "-v", "quiet", "-nostdin",
        "-i", path,
        "-map", "0:a:0",
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-ac", "1", "-ar", str(sample_rate),
    ]
    if max_seconds > 0:
        cmd += ["-t", "{:.3f}".format(max_seconds)]
    cmd.append("-")

    chunk_bytes = block_samples * 4
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        creationflags=_CREATE_NO_WINDOW,
    )
    try:
        pending = b""
        while True:
            data = proc.stdout.read(chunk_bytes)
            if not data:
                break
            if pending:
                data = pending + data
                pending = b""
            usable = len(data) - (len(data) % 4)
            if usable != len(data):
                pending = data[usable:]
                data = data[:usable]
            if usable:
                yield np.frombuffer(data, dtype="<f4")
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=30)
        except Exception:
            proc.kill()
            proc.wait()
