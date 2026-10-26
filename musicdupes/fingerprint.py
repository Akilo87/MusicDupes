"""Akustischer Fingerprint nach dem Constellation-/Landmark-Prinzip.

Aus dem Spektrogramm werden lokale Maxima ("Peaks") gepickt und paarweise zu
Hashes (f1, f2, dt) verknuepft. Zwei Dateien gelten als dieselbe Aufnahme, wenn
viele ihrer Hashes bei ein und demselben Zeitversatz uebereinstimmen.

Der Ansatz ist unempfindlich gegen Codec, Bitrate und Lautstaerke und erkennt
auch Teil-Ueberlappungen (gekuerzte Version, Track in einem DJ-Mix), weil der
Zeitversatz frei ist.
"""

from __future__ import annotations

import numpy as np

# --- Analyse-Parameter -----------------------------------------------------
SAMPLE_RATE = 44100
N_FFT = 4096
HOP = 1024
FRAME_RATE = SAMPLE_RATE / HOP          # ~43.07 Frames/s
BIN_HZ = SAMPLE_RATE / N_FFT            # ~10.77 Hz pro Bin

# Frequenzfenster fuer den Fingerprint. Tiefbass ist zu unspezifisch, Hoehen
# werden von verlustbehafteten Codecs weggeschnitten - beides waere fatal.
# Die Untergrenze liegt bewusst nicht ganz unten: dort ist ein FFT-Bin so
# schmal, dass die log-spaced Baender feiner werden als die Messgenauigkeit.
FP_LOW_HZ = 150.0
FP_HIGH_HZ = 2600.0
FP_BIN_LO = int(FP_LOW_HZ / BIN_HZ)       # 13
FP_BIN_HI = int(FP_HIGH_HZ / BIN_HZ) + 1  # 242
FP_BINS = FP_BIN_HI - FP_BIN_LO

# Peak-Picking. Die Dichte wird ueber die Groesse der Nachbarschaft geregelt
# und nicht ueber feste Zeitblöcke - Blockgrenzen ab Dateianfang wuerden bei
# einem beschnittenen Track andere Peaks ueberleben lassen.
PEAK_NEIGH_F = 14         # +/- Bins
PEAK_NEIGH_T = 8          # +/- Frames
LOCAL_REF_FRAMES = 87     # ~2 s gleitende Lautheitsreferenz
LOCAL_RANGE_DB = 42.0     # Dynamikfenster unter der lokalen Referenz
ABS_RANGE_DB = 72.0       # harte Untergrenze relativ zum lautesten Punkt

# Paarbildung
FAN_OUT = 4
DT_MIN = 2
DT_MAX = 63
# dt wird gruber gerastert als das Frame-Raster hergibt: ein Schnitt mitten
# im Frame verschiebt Peaks um +/-1 Frame, was bei exakter dt-Speicherung
# jeden Hash zerstoeren wuerde.
DT_QUANT = 2
DT_LEVELS = (DT_MAX - DT_MIN) // DT_QUANT + 1
FREQ_BANDS = 64           # log-spaced Baender, gepackt in je 7 Bit
F_SHIFT = 7
DT_SHIFT = 14
DT_STEP = 1 << DT_SHIFT   # Hash-Abstand zwischen benachbarten dt-Stufen

# Sicherheitsnetz beim Matching
MAX_BUCKET = 400          # Hashes, die oefter vorkommen, sind wertlos
MIN_MATCH_COUNT = 25      # darunter ist es Rauschen
OFFSET_SPAN = 1 << 17     # Platz fuer Zeitversaetze im kombinierten Schluessel

# Vorfilter vor dem Sortieren (siehe FingerprintIndex.query): grobe Zellen
# von 16 Zeitversaetzen, gezaehlt in einer festen Tabelle. Der Track wird
# multiplikativ gestreut, damit nicht immer dieselben Tracks kollidieren;
# benachbarte Zellen eines Tracks bleiben benachbarte Tabellenplaetze.
# Gemessen an 2059 Tracks: von gut einer Million Zwischentreffern je
# Abfrage bleiben 0,4 % zum Sortieren uebrig.
_CELL_SHIFT = 4
_PRUNE_TABLE = 1 << 19
_SLOT_MULT = 0x1E3779B1

_LOG_EDGES = np.logspace(
    np.log10(FP_BIN_LO + 1.0), np.log10(FP_BIN_HI + 1.0), FREQ_BANDS + 1
)


def band_of_bin(bins: np.ndarray) -> np.ndarray:
    """Bildet FFT-Bins log-spaced auf FREQ_BANDS Baender ab.

    Log-Skalierung, weil musikalische Information logarithmisch verteilt ist
    und kleine Bin-Verschiebungen durch Codec-Unterschiede so weniger oft
    ueber eine Bandgrenze rutschen.
    """
    idx = np.searchsorted(_LOG_EDGES, bins + 1.0, side="right") - 1
    return np.clip(idx, 0, FREQ_BANDS - 1).astype(np.int64)


def _max_filter_1d(arr: np.ndarray, radius: int, axis: int) -> np.ndarray:
    """Gleitendes Maximum mit Fensterbreite 2*radius+1 (Randbehandlung: edge)."""
    if radius <= 0:
        return arr
    width = 2 * radius + 1
    pad = [(0, 0), (0, 0)]
    pad[axis] = (radius, radius)
    padded = np.pad(arr, pad, mode="edge")
    view = np.lib.stride_tricks.sliding_window_view(padded, width, axis=axis)
    return view.max(axis=-1)


def _moving_average(values: np.ndarray, width: int) -> np.ndarray:
    """Gleitender Mittelwert mit Randfortsetzung, Laenge bleibt erhalten."""
    if width <= 1 or values.size <= 1:
        return values.astype(np.float32, copy=False)
    width = min(width, values.size if values.size % 2 else values.size - 1)
    if width < 3:
        return values.astype(np.float32, copy=False)
    if width % 2 == 0:
        width -= 1
    radius = width // 2
    padded = np.pad(values.astype(np.float64), (radius, radius), mode="edge")
    kernel = np.ones(width, dtype=np.float64) / width
    return np.convolve(padded, kernel, mode="valid").astype(np.float32)


def _parabolic_offset(
    before: np.ndarray, center: np.ndarray, after: np.ndarray
) -> np.ndarray:
    """Scheitelpunkt einer Parabel durch drei Punkte, als Versatz in [-0.5, 0.5].

    Die Werte kommen in dB herein - auf logarithmierten Betraegen ist die
    parabolische Naeherung fuer Spektralpeaks am genauesten.
    """
    denom = before - 2.0 * center + after
    offset = np.where(
        np.abs(denom) > 1e-9, 0.5 * (before - after) / denom, 0.0
    )
    return np.clip(offset, -0.5, 0.5)


def find_peaks(spec: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Findet Constellation-Peaks im Spektrogramm.

    ``spec`` hat die Form (frames, FP_BINS) und enthaelt Amplituden in dB.
    Rueckgabe: (frame_indices, verfeinerte_zeiten, band_indices), zeitlich
    sortiert.

    Alle Kriterien sind bewusst *lokal* formuliert. Ein Peak muss sich nur
    gegen seine unmittelbare Umgebung behaupten, nie gegen die ganze Datei.
    Nur so liefert ein beschnittener Track dieselben Peaks wie das Original.
    """
    if spec.shape[0] < 3:
        # Drei Werte wie unten - sonst scheitert der Aufrufer beim Entpacken,
        # und eine sehr kurze Datei erscheint als "nicht lesbar".
        return (
            np.empty(0, np.int64), np.empty(0, np.float32), np.empty(0, np.int64)
        )

    # Separables Maximum-Filter == 2D-Maximum bei rechteckiger Nachbarschaft,
    # aber deutlich billiger. Die Fenstergroesse regelt zugleich die Dichte.
    local_max = _max_filter_1d(spec, PEAK_NEIGH_F, axis=1)
    local_max = _max_filter_1d(local_max, PEAK_NEIGH_T, axis=0)

    # Gleitende Lautheitsreferenz statt globalem Schwellwert: in leisen
    # Passagen sollen trotzdem Peaks entstehen, in Stille aber keine.
    frame_peak = spec.max(axis=1)
    reference = _moving_average(frame_peak, LOCAL_REF_FRAMES)
    hard_floor = float(spec.max()) - ABS_RANGE_DB
    threshold = np.maximum(reference - LOCAL_RANGE_DB, hard_floor)

    mask = (spec >= local_max) & (spec > threshold[:, None])
    t_idx, f_idx = np.nonzero(mask)
    if t_idx.size == 0:
        return (
            np.empty(0, np.int64), np.empty(0, np.float32), np.empty(0, np.int64)
        )

    # Parabolische Interpolation um das Maximum, in beiden Achsen.
    #
    # Zeit: liegt ein Schnitt mitten in einem Frame, verschieben sich alle
    # Peaks um denselben Bruchteil - die Differenz zweier Peaks bleibt gleich.
    #
    # Frequenz: die eigentliche Teiltonfrequenz liegt fast nie exakt auf einem
    # FFT-Bin. Welcher Nachbarbin gewinnt, kippt schon bei minimal anderer
    # Fensterlage - und wirft den Peak dann in ein anderes Band. Das war der
    # groesste Einzelverlust bei nicht rasterkonform geschnittenen Dateien.
    last_t = spec.shape[0] - 1
    last_f = spec.shape[1] - 1
    center = spec[t_idx, f_idx]

    before = spec[np.maximum(t_idx - 1, 0), f_idx]
    after = spec[np.minimum(t_idx + 1, last_t), f_idx]
    refined_t = t_idx + _parabolic_offset(before, center, after)

    below = spec[t_idx, np.maximum(f_idx - 1, 0)]
    above = spec[t_idx, np.minimum(f_idx + 1, last_f)]
    refined_f = f_idx + _parabolic_offset(below, center, above)

    # np.nonzero liefert zeilenweise, also bereits nach Zeit sortiert.
    return (
        t_idx.astype(np.int64),
        refined_t.astype(np.float32),
        band_of_bin(refined_f + FP_BIN_LO),
    )


def peaks_to_hashes(
    times: np.ndarray, refined: np.ndarray, bands: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Verknuepft jeden Anker-Peak mit den naechsten FAN_OUT Peaks.

    ``dt`` wird aus den subframe-genauen Zeiten gebildet und erst danach
    gerastert - das macht den Hash unabhaengig davon, wo im Frame eine Datei
    beginnt. Die Ankerzeit bleibt ganzzahlig; ihr Restfehler faellt beim
    Abstimmen ueber den Zeitversatz ohnehin in benachbarte Bins.

    Hash-Layout (20 Bit): f1 (7) | f2 << F_SHIFT | dt-Stufe << DT_SHIFT
    Rueckgabe: (hashes uint32, ankerzeiten uint16)
    """
    n = times.size
    if n < 2:
        return np.empty(0, np.uint32), np.empty(0, np.uint16)

    hash_parts = []
    time_parts = []
    for step in range(1, FAN_OUT + 1):
        if n <= step:
            break
        t1 = times[:-step]
        f1 = bands[:-step]
        f2 = bands[step:]
        dt = refined[step:] - refined[:-step]
        level = np.round((dt - DT_MIN) / DT_QUANT)
        ok = (level >= 0) & (level < DT_LEVELS) & (t1 < 65536)
        if not np.any(ok):
            continue
        dt_level = level[ok].astype(np.uint32)
        packed = (
            f1[ok].astype(np.uint32)
            | (f2[ok].astype(np.uint32) << F_SHIFT)
            | (dt_level << DT_SHIFT)
        )
        hash_parts.append(packed)
        time_parts.append(t1[ok].astype(np.uint16))

    if not hash_parts:
        return np.empty(0, np.uint32), np.empty(0, np.uint16)

    hashes = np.concatenate(hash_parts)
    anchors = np.concatenate(time_parts)
    order = np.argsort(anchors, kind="stable")
    return hashes[order], anchors[order]


def pack_fingerprint(hashes: np.ndarray, times: np.ndarray) -> bytes:
    """Serialisiert einen Fingerprint fuer die SQLite-Ablage."""
    return hashes.astype("<u4").tobytes() + times.astype("<u2").tobytes()


def unpack_fingerprint(blob: bytes) -> tuple[np.ndarray, np.ndarray]:
    """Gegenstueck zu :func:`pack_fingerprint`."""
    if not blob:
        return np.empty(0, np.uint32), np.empty(0, np.uint16)
    count = len(blob) // 6
    if count == 0:
        return np.empty(0, np.uint32), np.empty(0, np.uint16)
    split = count * 4
    hashes = np.frombuffer(blob[:split], dtype="<u4", count=count)
    times = np.frombuffer(blob[split:split + count * 2], dtype="<u2", count=count)
    return hashes, times


def _expand_dt(
    hashes: np.ndarray, times: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Ergaenzt jeden Hash um seine dt+1- und dt-1-Variante."""
    if hashes.size == 0:
        return hashes, times
    dt = hashes >> DT_SHIFT
    parts_h = [hashes]
    parts_t = [times]
    lower = dt > 0
    if np.any(lower):
        parts_h.append(hashes[lower] - DT_STEP)
        parts_t.append(times[lower])
    upper = dt < np.uint32(DT_LEVELS - 1)
    if np.any(upper):
        parts_h.append(hashes[upper] + DT_STEP)
        parts_t.append(times[upper])
    return np.concatenate(parts_h), np.concatenate(parts_t)


class FingerprintIndex:
    """Invertierter Index ueber alle Fingerprints, fuer das Alle-gegen-alle."""

    def __init__(self) -> None:
        self._h: list[np.ndarray] = []
        self._t: list[np.ndarray] = []
        self._k: list[np.ndarray] = []
        self._built = False
        self.hashes = np.empty(0, np.uint32)
        self.tracks = np.empty(0, np.int32)
        self.times = np.empty(0, np.int32)

    def add(self, key: int, hashes: np.ndarray, times: np.ndarray) -> None:
        if hashes.size == 0:
            return
        self._h.append(np.asarray(hashes, dtype=np.uint32))
        self._t.append(np.asarray(times, dtype=np.int32))
        self._k.append(np.full(hashes.size, key, dtype=np.int32))
        self._built = False

    def build(self) -> None:
        """Sortiert nach Hash und wirft nichtssagende Massen-Hashes raus."""
        if not self._h:
            self.hashes = np.empty(0, np.uint32)
            self.tracks = np.empty(0, np.int32)
            self.times = np.empty(0, np.int32)
            self._built = True
            return

        hashes = np.concatenate(self._h)
        tracks = np.concatenate(self._k)
        times = np.concatenate(self._t)

        order = np.argsort(hashes, kind="stable")
        hashes = hashes[order]
        tracks = tracks[order]
        times = times[order]

        # Ein Hash, der in der halben Sammlung vorkommt, unterscheidet nichts -
        # er kostet nur Rechenzeit und produziert Fehltreffer.
        uniq, starts, counts = np.unique(
            hashes, return_index=True, return_counts=True
        )
        too_common = counts > MAX_BUCKET
        if np.any(too_common):
            drop = np.zeros(hashes.size, dtype=bool)
            for start, count in zip(starts[too_common], counts[too_common]):
                drop[start:start + count] = True
            keep = ~drop
            hashes = hashes[keep]
            tracks = tracks[keep]
            times = times[keep]

        self.hashes = hashes
        self.tracks = tracks
        self.times = times
        self._built = True

    def query(
        self, key: int, hashes: np.ndarray, times: np.ndarray
    ) -> list[tuple[int, int, int]]:
        """Sucht Treffer fuer einen Track.

        Rueckgabe: Liste aus (anderer_key, treffer_anzahl, zeitversatz),
        absteigend nach Trefferanzahl.
        """
        if not self._built:
            self.build()
        if hashes.size == 0 or self.hashes.size == 0:
            return []

        # Ein um Sekundenbruchteile verschobener Schnitt legt die STFT-Frames
        # anders auf den Ton, wodurch dt um einen Frame wackeln kann. Deshalb
        # fragen wir zusaetzlich mit dt+/-1 an - der Index bleibt schlank, nur
        # die Abfrage wird breiter.
        q_hash, q_time = _expand_dt(
            np.asarray(hashes, dtype=np.uint32),
            np.asarray(times, dtype=np.int32),
        )

        lo = np.searchsorted(self.hashes, q_hash, side="left")
        hi = np.searchsorted(self.hashes, q_hash, side="right")
        counts = (hi - lo).astype(np.int64)
        total = int(counts.sum())
        if total == 0:
            return []
        # Bei absurd vielen Treffern lieber abschneiden als den RAM sprengen.
        if total > 40_000_000:
            return []

        valid = counts > 0
        lo = lo[valid]
        counts = counts[valid]
        q_time = q_time[valid]

        # "Ragged range": aus (start, laenge)-Paaren einen flachen
        # Indexvektor bauen, ohne Python-Schleife. Innerhalb eines Bereichs
        # zaehlt die Folge um eins hoch, an jedem Bereichsanfang springt sie.
        step = np.ones(total, dtype=np.int64)
        starts = np.cumsum(counts) - counts
        step[starts[1:]] = lo[1:] - (lo[:-1] + counts[:-1]) + 1
        step[0] = lo[0]
        flat = np.cumsum(step)

        # Treffer des Tracks auf sich selbst bleiben bis zum Schluss drin und
        # werden erst bei der Auswertung uebersprungen - sie hier schon
        # herauszufiltern, kostete mehr, als es spart.
        cand = self.tracks[flat]
        shifted = self.times[flat] - np.repeat(q_time, counts)
        shifted += 65536

        # Vorfilter. Fast alle Eintraege sind Zufallstreffer, verstreut ueber
        # tausende Zeitversaetze - sie alle zu sortieren kostete den Grossteil
        # der Rechenzeit. Ein Versatz samt seinen beiden Nachbarn liegt immer
        # in einer groben Zelle und hoechstens einer angrenzenden. Erreichen
        # eine Zelle und ihre staerkere Nachbarin zusammen MIN_MATCH_COUNT
        # nicht, kann keiner ihrer Versaetze es erreichen - weg damit. Die
        # Tabelle ist fest bemessen; Kollisionen erhoehen die Zaehlung nur und
        # lassen dann hoechstens etwas mehr durch. Das Ergebnis aendert sich
        # dadurch nicht, nur der Aufwand.
        slot = (
            cand.astype(np.int64) * _SLOT_MULT + (shifted >> _CELL_SHIFT)
        ) & (_PRUNE_TABLE - 1)
        table = np.bincount(slot, minlength=_PRUNE_TABLE)
        neighbour = np.empty_like(table)
        neighbour[1:-1] = np.maximum(table[:-2], table[2:])
        neighbour[0] = max(table[-1], table[1])
        neighbour[-1] = max(table[-2], table[0])
        dense = ((table + neighbour) >= MIN_MATCH_COUNT)[slot]
        if not np.any(dense):
            return []

        # (Track, Zeitversatz) in einen Schluessel packen und zaehlen. Nach
        # dem Sortieren liegen gleiche Schluessel hintereinander.
        combined = cand[dense].astype(np.int64) * OFFSET_SPAN + shifted[dense]
        combined.sort()
        run_starts = np.flatnonzero(np.r_[True, combined[1:] != combined[:-1]])
        uniq = combined[run_starts]
        run_counts = np.diff(np.r_[run_starts, combined.size])

        cand_track = (uniq // OFFSET_SPAN).astype(np.int64)
        cand_delta = (uniq % OFFSET_SPAN) - 65536

        # Benachbarte Zeitversaetze zusammenzaehlen. Liegt der echte Versatz
        # zwischen zwei Frames - etwa weil jemand bei Sekunde 8,0 geschnitten
        # hat und das keine ganze Framebreite ist -, verteilen sich die
        # Treffer sonst auf zwei Bins und keiner davon sieht ueberzeugend aus.
        smoothed = run_counts.astype(np.int64)
        for shift in (-1, 1):
            probe = uniq + shift
            pos = np.minimum(np.searchsorted(uniq, probe), uniq.size - 1)
            hit = (uniq[pos] == probe) & (cand_track[pos] == cand_track)
            smoothed = smoothed + np.where(hit, run_counts[pos], 0)

        # Pro Kandidat den staerksten Zeitversatz behalten.
        group_bounds = np.flatnonzero(
            np.r_[True, cand_track[1:] != cand_track[:-1]]
        )
        best_counts = np.maximum.reduceat(smoothed, group_bounds)

        results: list[tuple[int, int, int]] = []
        for gi, start in enumerate(group_bounds):
            end = group_bounds[gi + 1] if gi + 1 < group_bounds.size else uniq.size
            best = int(best_counts[gi])
            if best < MIN_MATCH_COUNT or int(cand_track[start]) == key:
                continue
            local = start + int(np.argmax(smoothed[start:end]))
            results.append((int(cand_track[start]), best, int(cand_delta[local])))

        results.sort(key=lambda item: item[1], reverse=True)
        return results
