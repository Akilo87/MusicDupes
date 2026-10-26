"""Stufe 2 der Duplikatpruefung: dichter Vergleich zweier Kandidaten.

Der Constellation-Index (:mod:`fingerprint`) ist gut darin, aus tausenden
Tracks die paar Verdaechtigen herauszufischen - aber seine Trefferzahl ist
als *Prozentangabe* unbrauchbar, weil sie stark davon abhaengt, wie die
Dateien zufaellig auf das STFT-Raster fallen.

Hier steht deshalb ein zweites, dichtes Verfahren: je Track ein schmales
Band-Profil (16 Baender, ~21 Bilder/s), pro Bild normiert. Zwei Profile
werden per Kreuzkorrelation ausgerichtet und danach Bild fuer Bild
verglichen. Das Ergebnis ist eine ehrliche Zahl:

    "So viel Prozent des kuerzeren Tracks steckt im laengeren."
"""

from __future__ import annotations

import numpy as np

from .fingerprint import BIN_HZ, FRAME_RATE

PROFILE_BANDS = 16
PROFILE_LOW_HZ = 200.0
PROFILE_HIGH_HZ = 4000.0

# Mehrere STFT-Frames werden zu einem Profilbild gemittelt. Das glaettet genau
# die Zappeligkeit, an der die Peak-Auswahl scheitert. Die Fenster ueberlappen
# (Fenster 4, Schritt 2), weil sonst schon ein halbes Fenster Versatz zwischen
# zwei Dateien die gemittelten Werte auseinanderzoege.
PROFILE_WINDOW = 4
PROFILE_HOP = 2
PROFILE_RATE = FRAME_RATE / PROFILE_HOP     # ~21.5 Bilder/s

# Ab welcher Aehnlichkeit ein einzelnes Bild als "gleich" zaehlt.
FRAME_MATCH_COSINE = 0.90
MIN_PROFILE_FRAMES = 24

_EDGES = np.geomspace(PROFILE_LOW_HZ, PROFILE_HIGH_HZ, PROFILE_BANDS + 1)
_BIN_EDGES = np.unique(np.round(_EDGES / BIN_HZ).astype(np.int64))


def band_matrix(spec: np.ndarray) -> np.ndarray:
    """Fasst ein Betragsspektrum (frames, bins) zu Bandenergien zusammen."""
    power = spec.astype(np.float32) ** 2
    summed = np.add.reduceat(power, _BIN_EDGES[:-1], axis=1)
    return summed[:, : _BIN_EDGES.size - 1]


def finalize_profile(
    chunks: list, window: int = PROFILE_WINDOW, hop: int = PROFILE_HOP
) -> np.ndarray:
    """Baut aus den Bandenergien aller Bloecke das fertige, normierte Profil.

    Rueckgabe: int8-Matrix (bilder, baender). Jede Zeile ist mittelwertfrei
    und auf Laenge 1 normiert - dadurch ist der Vergleich unabhaengig von
    Lautstaerke und grober Klangregelung.
    """
    if not chunks:
        return np.zeros((0, PROFILE_BANDS), dtype=np.int8)

    bands = np.concatenate(chunks, axis=0)
    if bands.shape[0] < window:
        return np.zeros((0, bands.shape[1]), dtype=np.int8)

    # (bilder, baender, fenster) -> Mittel ueber das Fenster
    strided = np.lib.stride_tricks.sliding_window_view(
        bands, window, axis=0
    )[::hop]
    bands = strided.mean(axis=-1)
    db = 10.0 * np.log10(bands.astype(np.float32) + 1e-12)

    db -= db.mean(axis=1, keepdims=True)
    norm = np.linalg.norm(db, axis=1, keepdims=True)
    np.maximum(norm, 1e-6, out=norm)
    db /= norm

    return np.clip(np.round(db * 127.0), -127, 127).astype(np.int8)


def pack_profile(profile: np.ndarray) -> bytes:
    return profile.astype(np.int8).tobytes()


def unpack_profile(blob: bytes) -> np.ndarray:
    if not blob:
        return np.zeros((0, PROFILE_BANDS), dtype=np.int8)
    flat = np.frombuffer(blob, dtype=np.int8)
    width = _BIN_EDGES.size - 1
    return flat[: (flat.size // width) * width].reshape(-1, width)


def _best_offset(a: np.ndarray, b: np.ndarray) -> int:
    """Bester Zeitversatz von b gegenueber a, per FFT-Kreuzkorrelation."""
    length = 1
    while length < a.shape[0] + b.shape[0]:
        length <<= 1
    fa = np.fft.rfft(a, n=length, axis=0)
    fb = np.fft.rfft(b, n=length, axis=0)
    corr = np.fft.irfft(np.conj(fa) * fb, n=length, axis=0).sum(axis=1)
    offset = int(np.argmax(corr))
    if offset > length // 2:
        offset -= length
    return offset


def compare(
    profile_a: np.ndarray,
    profile_b: np.ndarray,
    cosine: float = FRAME_MATCH_COSINE,
) -> tuple[float, float, float]:
    """Vergleicht zwei Profile.

    Rueckgabe: (Deckung, Aehnlichkeit, Zeitversatz in Sekunden).

    Beide Anteile stammen aus derselben Messung, nur der Nenner unterscheidet
    sich - und damit die Frage, die sie beantworten:

    * **Deckung** teilt durch den *kuerzeren* Track: "Wie viel davon steckt im
      laengeren?" Das ist die Zahl, die zum Finden von Duplikaten taugt, denn
      ein Radio Edit steckt vollstaendig in seinem Extended Mix.
    * **Aehnlichkeit** teilt durch den *laengeren*: "Wie sehr gleichen sich
      die beiden Dateien insgesamt?" Bei 3:51 gegen 6:32 kann die Deckung
      100 % betragen und die Aehnlichkeit trotzdem nur 59 %.
    """
    if (
        profile_a.shape[0] < MIN_PROFILE_FRAMES
        or profile_b.shape[0] < MIN_PROFILE_FRAMES
    ):
        return 0.0, 0.0, 0.0

    a = profile_a.astype(np.float32) / 127.0
    b = profile_b.astype(np.float32) / 127.0
    shorter = float(min(a.shape[0], b.shape[0]))
    longer = float(max(a.shape[0], b.shape[0]))

    # Die Profilbilder beider Dateien liegen auf einem festen Raster ab
    # Dateianfang. Ist eine Datei um einen Bruchteil dieses Rasters
    # verschoben - gekuerzt, mit anderem Vorlauf -, passt keine ganzzahlige
    # Ausrichtung genau: bei einem halben Raster fiel dieselbe Aufnahme so von
    # 100 % auf 79 %. Deshalb zusaetzlich gegen die Mittelwerte benachbarter
    # Bilder vergleichen, also um ein halbes Raster versetzt. Es zaehlt die
    # beste der drei Ausrichtungen.
    best = _matched(a, b, cosine, 0.0)
    for shifted_a, shifted_b, shift in (
        (_midpoints(a), b, -0.5),
        (a, _midpoints(b), 0.5),
    ):
        candidate = _matched(shifted_a, shifted_b, cosine, shift)
        if candidate[0] > best[0]:
            best = candidate

    matched, offset = best
    coverage = min(1.0, matched / shorter)
    similarity = min(1.0, matched / longer)
    return float(coverage), float(similarity), offset / PROFILE_RATE


def _midpoints(profile: np.ndarray) -> np.ndarray:
    """Profil um ein halbes Bild versetzt: Mittel je zweier Nachbarn, normiert.

    Beide Zeilen sind mittelwertfrei, ihre Summe ist es also auch - es muss
    nur die Laenge wieder auf 1 gebracht werden.
    """
    mid = profile[:-1] + profile[1:]
    norm = np.linalg.norm(mid, axis=1, keepdims=True)
    np.maximum(norm, 1e-6, out=norm)
    return mid / norm


def _matched(a: np.ndarray, b: np.ndarray, cosine: float, shift: float) -> tuple:
    """Gleiche Bilder bei bester Ausrichtung: (Anzahl, Versatz in Bildern).

    ``shift`` ist der Versatz, den die Halbbild-Variante selbst mitbringt;
    er wird auf den gefundenen Versatz aufgeschlagen.
    """
    offset = _best_offset(a, b)

    # Ueberlappenden Bereich ausschneiden. Die Korrelation liefert offset so,
    # dass a[i] und b[i + offset] dieselbe Stelle im Material sind.
    if offset >= 0:
        a_start, b_start = 0, offset
    else:
        a_start, b_start = -offset, 0
    span = min(a.shape[0] - a_start, b.shape[0] - b_start)
    if span < MIN_PROFILE_FRAMES:
        return 0, offset + shift

    # Beide Zeilen sind normiert - das Skalarprodukt *ist* der Kosinus.
    per_frame = np.einsum(
        "ij,ij->i", a[a_start:a_start + span], b[b_start:b_start + span]
    )
    return int(np.count_nonzero(per_frame >= cosine)), offset + shift
