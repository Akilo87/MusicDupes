"""Qualitaetsbewertung eines Tracks.

Der spannende Teil ist die *gemessene* Bandbreite: Tags und Container luegen
gern (eine FLAC, die aus einem 128-kbps-MP3 gemacht wurde, bleibt eine
128-kbps-Aufnahme). Die spektrale Grenzfrequenz verraet das.
"""

from __future__ import annotations

import math

import numpy as np

from . import i18n
from .fingerprint import BIN_HZ

# Ab hier gilt eine Aufnahme als "voll" - darueber sitzt bei Musik ohnehin
# kaum noch Energie.
FULL_BANDWIDTH_HZ = 20_500.0
MIN_USEFUL_HZ = 11_000.0

# Unterhalb dieser Grenze passt "verlustfrei" nicht zum Inhalt.
TRANSCODE_SUSPECT_HZ = 19_500.0


def spectral_cutoff(power_sum: np.ndarray, frames: int) -> float:
    """Schaetzt die hoechste Frequenz mit echtem Signalanteil (in Hz).

    Verlustbehaftete Codecs schneiden oben hart ab. Wir suchen genau diese
    Kante: das mittlere Leistungsspektrum wird geglaettet und von oben nach
    unten abgesucht, bis der Pegel wieder ueber die Schwelle steigt.
    """
    if frames <= 0 or power_sum.size == 0:
        return 0.0

    psd = power_sum / float(frames)
    total = float(psd.sum())
    if not math.isfinite(total) or total <= 0.0:
        return 0.0

    db = 10.0 * np.log10(psd + 1e-20)

    # Glaetten, damit einzelne Ausreisser die Kante nicht verschieben.
    window = 9
    kernel = np.ones(window, dtype=np.float64) / window
    smooth = np.convolve(db, kernel, mode="same")

    lo = int(1000.0 / BIN_HZ)
    hi = min(int(5000.0 / BIN_HZ), smooth.size - 1)
    if hi <= lo:
        return 0.0
    reference = float(np.median(smooth[lo:hi]))
    threshold = reference - 50.0

    above = np.flatnonzero(smooth > threshold)
    if above.size == 0:
        return 0.0
    return float(above[-1] * BIN_HZ)


def _bandwidth_score(cutoff_hz: float) -> float:
    if cutoff_hz <= 0:
        return 50.0  # unbekannt - nicht bestrafen, nur nicht belohnen
    span = FULL_BANDWIDTH_HZ - MIN_USEFUL_HZ
    value = (cutoff_hz - MIN_USEFUL_HZ) / span
    return float(np.clip(value, 0.0, 1.0) * 100.0)


def _format_score(lossless: bool, bitrate: int) -> float:
    if lossless:
        return 100.0
    if bitrate <= 0:
        return 55.0
    # 320 kbps gilt als Obergrenze des sinnvoll Unterscheidbaren.
    return float(np.clip(bitrate / 320.0, 0.0, 1.0) * 100.0)


def _rate_score(sample_rate: int) -> float:
    if sample_rate <= 0:
        return 60.0
    if sample_rate >= 44100:
        return 100.0
    if sample_rate >= 32000:
        return 65.0
    if sample_rate >= 22050:
        return 35.0
    return 15.0


def _channel_score(channels: int) -> float:
    if channels >= 2:
        return 100.0
    if channels == 1:
        return 55.0
    return 60.0


# Wie gut sich eine Datei auf einer grossen Anlage macht. Bewusst eine eigene
# Groesse und nicht der allgemeine Score: im Club zaehlt fast nur, wie weit
# oben der Ton noch da ist. Uebersteuerung dagegen steckt bei modernen
# Clubtracks schon im Master und macht die Datei nicht untauglich.
CLUB_BANDS = (
    (88.0, "club.very_good"),
    (70.0, "club.good"),
    (50.0, "club.usable"),
    (30.0, "club.marginal"),
    (0.0, "club.unsuitable"),
)

_CLUB_LOW_HZ = 13_000.0
_CLUB_FULL_HZ = 20_500.0


def club_rating(record: dict) -> tuple[float, str]:
    """Eignung fuer Club/Disco als Wert 0..100 und als Wort.

    Wird aus den gespeicherten Messwerten berechnet und nicht mitgespeichert -
    so laesst sich die Bewertung nachschaerfen, ohne die ganze Sammlung neu
    einlesen zu muessen.
    """
    flags = record.get("quality_flags") or []
    cutoff = float(record.get("cutoff_hz") or 0.0)

    if cutoff > 0:
        span = _CLUB_FULL_HZ - _CLUB_LOW_HZ
        score = float(np.clip((cutoff - _CLUB_LOW_HZ) / span, 0.0, 1.0)) * 100.0
    else:
        score = 50.0

    if record.get("lossless") and i18n.FLAG_TRANSCODE not in flags:
        score = min(100.0, score + 6.0)

    # Mono faellt auf einer Stereoanlage sofort auf.
    if int(record.get("channels") or 2) == 1:
        score *= 0.6

    sample_rate = int(record.get("sample_rate") or 44100)
    if 0 < sample_rate < 44100:
        score *= 0.75

    # Erst deutlich jenseits des ueblichen Masterings abwerten.
    clip_ratio = float(record.get("clip_ratio") or 0.0)
    if clip_ratio > 0.05:
        score -= min(10.0, (clip_ratio - 0.05) * 200.0)

    score = float(np.clip(score, 0.0, 100.0))
    for threshold, key in CLUB_BANDS:
        if score >= threshold:
            return score, i18n.t(key)
    return score, i18n.t(CLUB_BANDS[-1][1])


def evaluate(
    *,
    lossless: bool,
    bitrate: int,
    sample_rate: int,
    channels: int,
    bits_per_sample: int,
    cutoff_hz: float,
    clip_ratio: float,
    peak_dbfs: float,
) -> tuple[float, list[str]]:
    """Liefert (Score 0..100, Liste von Auffaelligkeiten)."""
    score = (
        0.55 * _bandwidth_score(cutoff_hz)
        + 0.25 * _format_score(lossless, bitrate)
        + 0.12 * _rate_score(sample_rate)
        + 0.08 * _channel_score(channels)
    )

    # Gespeichert werden Schluessel, kein fertiger Text. Die Empfehlungslogik
    # prueft darauf, und die Anzeige uebersetzt sie erst beim Darstellen -
    # sonst haetten dieselben Dateien je nach Sprache andere Ergebnisse.
    flags: list[str] = []

    if lossless and 0 < cutoff_hz < TRANSCODE_SUSPECT_HZ:
        # Verlustfreier Container, aber verlustbehafteter Inhalt.
        flags.append(i18n.FLAG_TRANSCODE)
        score -= 18.0

    if sample_rate > 48000 and 0 < cutoff_hz < 21_000:
        flags.append(i18n.FLAG_HIRES_EMPTY)
        score -= 6.0

    if clip_ratio > 0.001:
        flags.append(i18n.FLAG_CLIPPING)
        score -= min(12.0, clip_ratio * 1500.0)

    if channels == 1:
        flags.append(i18n.FLAG_MONO)

    if not lossless and 0 < bitrate < 128:
        flags.append(i18n.FLAG_LOW_BITRATE)

    if peak_dbfs < -12.0:
        flags.append(i18n.FLAG_QUIET)

    if bits_per_sample >= 24:
        score += 2.0

    return float(np.clip(score, 0.0, 100.0)), flags
