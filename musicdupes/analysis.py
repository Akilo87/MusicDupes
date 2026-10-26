"""Pro-Datei-Analyse: laeuft in Worker-Prozessen, einer je CPU-Thread.

Eine Datei wird genau einmal dekodiert. Aus demselben Spektrogramm entstehen
sowohl der Fingerprint (unterer Frequenzbereich) als auch die Qualitaetsdaten
(volles Spektrum) - zweimal dekodieren waere die Haelfte der Geschwindigkeit.
"""

from __future__ import annotations

import hashlib
import math
import os
import traceback

import numpy as np

from . import audio, quality, verify
from .fingerprint import (
    FP_BIN_HI, FP_BIN_LO, HOP, N_FFT, SAMPLE_RATE,
    find_peaks, pack_fingerprint, peaks_to_hashes,
)

# Deckel gegen stundenlange DJ-Mixe: 20 Minuten reichen fuer eine sichere
# Identifikation bei weitem und begrenzen den Speicher je Worker.
MAX_ANALYSIS_SECONDS = 1200.0

_HASH_CHUNK = 1 << 20
_CLIP_LEVEL = 0.9995


def file_digest(path: str) -> str:
    """Schneller Inhalts-Hash der Datei (blake2b, 128 Bit)."""
    hasher = hashlib.blake2b(digest_size=16)
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(_HASH_CHUNK)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _to_dbfs(value: float) -> float:
    if value <= 0.0:
        return -120.0
    return float(max(-120.0, 20.0 * math.log10(value)))


def analyze_file(path: str) -> dict:
    """Analysiert eine Datei vollstaendig. Wirft nie - Fehler landen im Dict."""
    result: dict = {"path": path, "error": ""}
    try:
        stat = os.stat(path)
        result["size"] = int(stat.st_size)
        result["mtime"] = float(stat.st_mtime)

        result["file_hash"] = file_digest(path)

        info = audio.probe(path)
        merged = info.tags

        result.update(
            codec=info.codec,
            codec_long=info.codec_long,
            container=info.container,
            duration=info.duration,
            bitrate=info.bitrate,
            bitrate_is_container=info.bitrate_is_container,
            sample_rate=info.sample_rate,
            channels=info.channels,
            bits_per_sample=info.bits_per_sample,
            lossless=info.lossless,
            artist=merged.get("artist", ""),
            title=merged.get("title", ""),
            album=merged.get("album", ""),
            track_no=merged.get("track", ""),
            date=merged.get("date", ""),
            genre=merged.get("genre", ""),
        )

        window = np.hanning(N_FFT).astype(np.float32)
        power_sum = np.zeros(N_FFT // 2 + 1, dtype=np.float64)
        frames_total = 0
        fp_chunks: list[np.ndarray] = []
        profile_chunks: list[np.ndarray] = []

        audio_hasher = hashlib.blake2b(digest_size=16)
        peak_abs = 0.0
        sum_sq = 0.0
        n_samples = 0
        clipped = 0

        tail = np.empty(0, dtype=np.float32)

        for block in audio.decode_blocks(
            path, SAMPLE_RATE, max_seconds=MAX_ANALYSIS_SECONDS
        ):
            audio_hasher.update(block.tobytes())

            magnitude = np.abs(block)
            if magnitude.size:
                peak_abs = max(peak_abs, float(magnitude.max()))
                clipped += int(np.count_nonzero(magnitude >= _CLIP_LEVEL))
            sum_sq += float(np.dot(block.astype(np.float64), block.astype(np.float64)))
            n_samples += int(block.size)

            data = np.concatenate((tail, block)) if tail.size else block
            if data.size >= N_FFT:
                strided = np.lib.stride_tricks.sliding_window_view(data, N_FFT)[::HOP]
                frames = strided * window
                spec = np.abs(np.fft.rfft(frames, axis=1))
                power_sum += np.einsum("ij,ij->j", spec, spec, dtype=np.float64)
                frames_total += spec.shape[0]

                band = spec[:, FP_BIN_LO:FP_BIN_HI]
                fp_chunks.append(
                    (20.0 * np.log10(band + 1e-10)).astype(np.float32)
                )
                profile_chunks.append(verify.band_matrix(spec))
                consumed = spec.shape[0] * HOP
                tail = np.array(data[consumed:], dtype=np.float32, copy=True)
            else:
                tail = np.array(data, dtype=np.float32, copy=True)

        if n_samples == 0:
            # Schluessel statt Text: der Cache soll sprachneutral bleiben.
            result["error"] = "engine.no_audio"
            return result

        result["audio_hash"] = audio_hasher.hexdigest()
        result["decoded_seconds"] = n_samples / float(SAMPLE_RATE)

        if fp_chunks:
            fp_spec = np.concatenate(fp_chunks, axis=0)
            del fp_chunks
            times, refined, bands = find_peaks(fp_spec)
            del fp_spec
            hashes, anchors = peaks_to_hashes(times, refined, bands)
        else:
            hashes = np.empty(0, np.uint32)
            anchors = np.empty(0, np.uint16)

        result["fingerprint"] = pack_fingerprint(hashes, anchors)
        result["fp_count"] = int(hashes.size)

        profile = verify.finalize_profile(profile_chunks)
        del profile_chunks
        result["profile"] = verify.pack_profile(profile)
        result["profile_frames"] = int(profile.shape[0])

        cutoff = quality.spectral_cutoff(power_sum, frames_total)
        peak_dbfs = _to_dbfs(peak_abs)
        rms_dbfs = _to_dbfs(math.sqrt(sum_sq / n_samples)) if n_samples else -120.0
        clip_ratio = clipped / float(n_samples)

        score, flags = quality.evaluate(
            lossless=info.lossless,
            bitrate=info.bitrate,
            sample_rate=info.sample_rate,
            channels=info.channels,
            bits_per_sample=info.bits_per_sample,
            cutoff_hz=cutoff,
            clip_ratio=clip_ratio,
            peak_dbfs=peak_dbfs,
        )

        result.update(
            cutoff_hz=cutoff,
            peak_dbfs=peak_dbfs,
            rms_dbfs=rms_dbfs,
            clip_ratio=clip_ratio,
            quality_score=score,
            quality_flags=flags,
        )
        return result

    except audio.AudioError as exc:
        # Bekannte Fehler als Schluessel: der Worker kennt die eingestellte
        # Sprache nicht, und der Cache soll sprachneutral bleiben.
        result["error"] = exc.key
        return result
    except Exception as exc:  # noqa: BLE001 - Worker darf nie sterben
        result["error"] = "{}: {}".format(type(exc).__name__, exc)
        result["traceback"] = traceback.format_exc(limit=4)
        return result
