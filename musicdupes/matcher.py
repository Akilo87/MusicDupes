"""Aus Einzelanalysen werden Duplikatgruppen.

Ablauf:

1. Gleiche Datei (Inhalts-Hash) und gleicher Ton bei anderen Tags (Audio-Hash)
   sind sichere Treffer und kosten nichts.
2. Der Constellation-Index schlaegt Kandidatenpaare vor.
3. Jedes Kandidatenpaar wird dicht nachgerechnet - erst diese Zahl entscheidet.
4. Uebrig bleibende, nur namentlich passende Paare werden getrennt ausgewiesen.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from . import i18n, verify
from .fingerprint import FingerprintIndex, unpack_fingerprint
from .textmatch import TrackName, blocking_tokens, similarity as name_similarity

MATCH_IDENTICAL_FILE = "identical_file"
MATCH_IDENTICAL_AUDIO = "identical_audio"
MATCH_SAME_RECORDING = "same_recording"
MATCH_SAME_TITLE = "same_title"
# Nur fuer die Anzeige: der Track, mit dem alle anderen verglichen wurden.
# Er ist mit sich selbst trivial identisch - stuende dort "Identische Datei",
# laese sich das wie "es gibt eine bitgleiche Kopie".
MATCH_REFERENCE = "reference"

def match_label(kind: str) -> str:
    """Sichtbarer Name einer Trefferart, in der eingestellten Sprache."""
    return i18n.t("match." + kind)


def match_help(kind: str) -> str:
    """Laengere Erklaerung einer Trefferart."""
    return i18n.t("matchhelp." + kind)


# Von sicher nach unsicher. Eine Gruppe wird nach ihrem *schwaechsten*
# Bindeglied benannt - alles andere waere geschoenigt.
MATCH_ORDER = [
    MATCH_IDENTICAL_FILE,
    MATCH_IDENTICAL_AUDIO,
    MATCH_SAME_RECORDING,
    MATCH_SAME_TITLE,
]
_RANK = {kind: i for i, kind in enumerate(MATCH_ORDER)}

# Ein Namenstreffer bei voellig anderer Spieldauer ist keiner.
MAX_DURATION_RATIO = 1.6


@dataclass
class Edge:
    a: int
    b: int
    kind: str
    score: float
    offset: float = 0.0


@dataclass
class PairScore:
    """Ein Vergleich zweier konkreter Dateien, beide Lesarten nebeneinander."""

    a: int
    b: int
    coverage: float     # Anteil des kuerzeren Tracks
    similarity: float   # Anteil des laengeren Tracks
    offset: float
    kind: str


@dataclass
class Group:
    members: list
    kind: str
    best: int
    # index -> gemessene akustische Uebereinstimmung mit ``best``
    scores: dict = field(default_factory=dict)
    # index -> Namensaehnlichkeit, nur wenn der Treffer darauf beruht.
    # Getrennt gefuehrt, weil beide Zahlen voellig Verschiedenes bedeuten
    # und eine gemeinsame Spalte zwangslaeufig in die Irre fuehrt.
    name_scores: dict = field(default_factory=dict)
    kinds: dict = field(default_factory=dict)    # index -> Art des Treffers
    offsets: dict = field(default_factory=dict)  # index -> Versatz in Sekunden
    # Jedes Paar innerhalb der Gruppe, fuer den Paarvergleich-Reiter.
    pairs: list = field(default_factory=list)

    @property
    def label(self) -> str:
        return match_label(self.kind)


class _UnionFind:
    def __init__(self, size: int) -> None:
        self._parent = list(range(size))

    def find(self, item: int) -> int:
        parent = self._parent
        root = item
        while parent[root] != root:
            root = parent[root]
        while parent[item] != root:
            parent[item], item = root, parent[item]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self._parent[rb] = ra
        return True


def _quality_sort_key(record: dict) -> tuple:
    """Womit ein Track als "der bessere" gilt.

    Die Reihenfolge ist bewusst gestuft und nicht ein einzelner Punktwert:

    1. Die *gemessene* Bandbreite in 2-kHz-Stufen. Sie ist die einzige Angabe,
       die nicht luegen kann.
    2. Echt verlustfrei. Nur bei gleicher Bandbreite - sonst wuerde eine aus
       MP3 erzeugte FLAC ihr eigenes Original schlagen. Ein Transcode-Verdacht
       zaehlt hier deshalb nicht als verlustfrei.
    3. Erst danach der Punktwert. Sonst kippt ein Abzug fuer Uebersteuerung -
       den ein lauter Master immer kassiert - die Entscheidung zugunsten einer
       verlustbehafteten Datei mit hoher Bitrate.
    4. Dauer vor Bitrate, damit eine abgebrochene Datei nicht wegen zufaellig
       hoeherer VBR-Rate gewinnt.
    """
    flags = record.get("quality_flags") or []
    genuine_lossless = (
        bool(record.get("lossless")) and i18n.FLAG_TRANSCODE not in flags
    )
    cutoff = float(record.get("cutoff_hz") or 0.0)
    return (
        int(cutoff // 2000),
        1 if genuine_lossless else 0,
        round(float(record.get("quality_score") or 0.0), 2),
        int(round(float(record.get("duration") or 0.0))),
        int(record.get("bitrate") or 0),
        int(record.get("size") or 0),
    )


def _query_threads() -> int:
    # NumPy gibt bei den grossen Array-Operationen den GIL frei; mehr als
    # vier Threads brachten gemessen kaum noch etwas, kosten aber je Abfrage
    # einige zehn MB Zwischenspeicher.
    return max(1, min(4, os.cpu_count() or 1))


def _stage1_candidates(
    records: list, usable: list, report: Callable, cache: Optional[dict]
) -> frozenset:
    """Kandidatenpaare aus dem Constellation-Index.

    Der mit Abstand teuerste Schritt der Gruppierung - und unabhaengig von
    den Schwellwerten. Deshalb parallel und, wenn der Aufrufer es anbietet,
    zwischengespeichert.
    """
    signature = tuple(
        (i, records[i].get("path"), records[i].get("fp_count")) for i in usable
    )
    if cache is not None and cache.get("signature") == signature:
        report("stage.candidates", len(usable), len(usable))
        return cache["candidates"]

    index = FingerprintIndex()
    for i in usable:
        hashes, times = unpack_fingerprint(records[i].get("fingerprint") or b"")
        index.add(i, hashes, times)
    index.build()

    def lookup(i: int) -> tuple:
        hashes, times = unpack_fingerprint(records[i].get("fingerprint") or b"")
        return i, index.query(i, hashes, times)

    found: set = set()
    pool = ThreadPoolExecutor(max_workers=_query_threads())
    try:
        for done, (i, hits) in enumerate(pool.map(lookup, usable)):
            if done % 64 == 0:
                report("stage.candidates", done, len(usable))
            for other, _count, _offset in hits:
                found.add((min(i, other), max(i, other)))
    finally:
        # Bei einem Abbruch nicht erst alle uebrigen Abfragen abarbeiten.
        pool.shutdown(wait=True, cancel_futures=True)
    report("stage.candidates", len(usable), len(usable))

    result = frozenset(found)
    if cache is not None:
        cache.clear()
        cache.update(signature=signature, candidates=result)
    return result


def _dur(record: dict) -> float:
    value = float(record.get("duration") or 0.0)
    if value <= 0:
        value = float(record.get("decoded_seconds") or 0.0)
    return value


def build_groups(
    records: list,
    audio_threshold: float = 0.90,
    meta_threshold: float = 0.82,
    use_metadata: bool = True,
    progress: Optional[Callable] = None,
    stage1_cache: Optional[dict] = None,
) -> tuple:
    """Gruppiert die Analyseergebnisse.

    ``audio_threshold`` und ``meta_threshold`` sind Anteile von 0..1.
    ``stage1_cache`` ist ein Dict, das der Aufrufer zwischen zwei Laeufen
    ueber *dieselben* Datensaetze aufhebt: die Kandidatensuche haengt von
    keinem Schwellwert ab, "Neu gruppieren" kann sie also wiederverwenden.
    Rueckgabe: (Gruppen, Statistik-Dict).
    """

    def report(stage: str, done: int, total: int) -> None:
        if progress is not None:
            progress(stage, done, total)

    usable = [
        i for i, rec in enumerate(records)
        if not rec.get("error") and rec.get("profile")
    ]
    edges: list[Edge] = []

    # -- 1. Bitgleiche Dateien und bitgleicher Ton -------------------------
    report("stage.hashes", 0, 1)
    by_file: dict = {}
    by_audio: dict = {}
    for i in usable:
        record = records[i]
        digest = record.get("file_hash") or ""
        if digest:
            by_file.setdefault(digest, []).append(i)
        digest = record.get("audio_hash") or ""
        if digest:
            by_audio.setdefault(digest, []).append(i)

    exact_pairs = set()
    for members in by_file.values():
        for other in members[1:]:
            edges.append(Edge(members[0], other, MATCH_IDENTICAL_FILE, 1.0))
            exact_pairs.add((min(members[0], other), max(members[0], other)))
    for members in by_audio.values():
        for other in members[1:]:
            pair = (min(members[0], other), max(members[0], other))
            if pair in exact_pairs:
                continue
            edges.append(Edge(members[0], other, MATCH_IDENTICAL_AUDIO, 1.0))
            exact_pairs.add(pair)

    # -- 2. Kandidaten aus dem Fingerprint-Index ---------------------------
    candidates = set(_stage1_candidates(records, usable, report, stage1_cache))
    stage1_candidates = len(candidates)

    # -- 3. Namensaehnliche Paare ------------------------------------------
    names = {i: TrackName(
        records[i].get("artist") or "",
        records[i].get("title") or "",
        _basename(records[i].get("path") or ""),
    ) for i in usable}

    meta_pairs = _name_candidate_pairs(
        records, names, usable, meta_threshold
    ) if use_metadata else {}
    # Auch namensaehnliche Paare akustisch nachrechnen: manchmal ist es
    # doch dieselbe Aufnahme, dann ist der Treffer sicher statt vage.
    candidates.update(meta_pairs)

    # -- 4. Kandidaten dicht nachrechnen -----------------------------------
    profiles: dict = {}

    def profile_of(idx: int) -> np.ndarray:
        cached = profiles.get(idx)
        if cached is None:
            cached = verify.unpack_profile(records[idx].get("profile") or b"")
            profiles[idx] = cached
        return cached

    todo = [pair for pair in candidates if pair not in exact_pairs]
    verified = 0
    for done, (a, b) in enumerate(todo):
        if done % 128 == 0:
            report("stage.verify", done, len(todo))
        ratio, _similar, offset = verify.compare(profile_of(a), profile_of(b))
        if ratio >= audio_threshold:
            edges.append(Edge(a, b, MATCH_SAME_RECORDING, ratio, offset))
            verified += 1
    report("stage.verify", len(todo), len(todo))

    acoustic_pairs = exact_pairs | {
        (e.a, e.b) for e in edges if e.kind == MATCH_SAME_RECORDING
    }

    # -- 5. Rein namentliche Treffer ---------------------------------------
    #
    # Diese Kanten sind die unsicheren. Wuerde man sie einfach mit in die
    # Union-Find werfen, koennte eine einzige falsche Kante zwei voellig
    # verschiedene Songs zu einer Gruppe verschmelzen - und ueber weitere
    # Kanten immer weiter. Deshalb verbinden sie nur fertige akustische
    # Cluster, und jedes Cluster muss zum *Startcluster* passen, nicht bloss
    # zu irgendeinem schon aufgenommenen Nachbarn.
    union = _UnionFind(len(records))
    for edge in edges:
        union.union(edge.a, edge.b)

    if use_metadata:
        for edge in _version_edges(
            records, names, usable, union, meta_pairs, meta_threshold
        ):
            edges.append(edge)
            union.union(edge.a, edge.b)

    # -- 6. Gruppen bilden --------------------------------------------------

    clusters: dict = {}
    edges_of: dict = {}
    for edge in edges:
        root = union.find(edge.a)
        clusters.setdefault(root, set()).update((edge.a, edge.b))
        edges_of.setdefault(root, []).append(edge)

    groups: list[Group] = []
    for root, members in clusters.items():
        if len(members) < 2:
            continue
        ordered = sorted(members)
        best = max(ordered, key=lambda i: _quality_sort_key(records[i]))

        member_edges = edges_of[root]
        weakest = max(
            (_RANK[e.kind] for e in member_edges), default=_RANK[MATCH_SAME_TITLE]
        )

        group = Group(members=ordered, kind=MATCH_ORDER[weakest], best=best)

        # Jedes Mitglied gegen den Favoriten - das ist die Zahl, die in der
        # Tabelle steht und die man vergleichen koennen muss.
        direct = {}
        for edge in member_edges:
            if edge.a == best:
                direct[edge.b] = edge
            elif edge.b == best:
                direct[edge.a] = edge

        for member in ordered:
            if member == best:
                group.scores[member] = 1.0
                group.kinds[member] = MATCH_REFERENCE
                group.offsets[member] = 0.0
                continue
            edge = direct.get(member)
            if edge is not None and edge.kind != MATCH_SAME_TITLE:
                group.scores[member] = edge.score
                group.kinds[member] = edge.kind
                group.offsets[member] = edge.offset
                continue
            # In der Spalte steht immer die *gemessene* Aehnlichkeit zum
            # Favoriten, auch wenn der Track nur ueber seinen Namen in die
            # Gruppe gekommen ist.
            ratio, _similar, offset = verify.compare(
                profile_of(best), profile_of(member)
            )
            group.scores[member] = ratio
            group.offsets[member] = offset
            if ratio >= audio_threshold:
                group.kinds[member] = MATCH_SAME_RECORDING
            else:
                group.kinds[member] = MATCH_SAME_TITLE
                group.name_scores[member] = (
                    edge.score if edge is not None
                    else name_similarity(names[best], names[member])
                )

        # Jedes Paar der Gruppe einzeln durchrechnen. Gruppen sind klein,
        # das kostet praktisch nichts - liefert aber die zweite Lesart, die
        # sich aus der Zeile "gegen den Favoriten" nicht ablesen laesst.
        edge_kinds = {}
        for edge in member_edges:
            edge_kinds[(min(edge.a, edge.b), max(edge.a, edge.b))] = edge.kind

        for pos, first in enumerate(ordered):
            for second in ordered[pos + 1:]:
                coverage, similar, offset = verify.compare(
                    profile_of(first), profile_of(second)
                )
                kind = edge_kinds.get((first, second))
                if kind is None or kind == MATCH_SAME_TITLE:
                    kind = (
                        MATCH_SAME_RECORDING if coverage >= audio_threshold
                        else MATCH_SAME_TITLE
                    )
                group.pairs.append(
                    PairScore(first, second, coverage, similar, offset, kind)
                )

        groups.append(group)

    groups.sort(
        key=lambda g: (_RANK[g.kind], -len(g.members),
                       records[g.best].get("artist") or "",
                       records[g.best].get("title") or "")
    )

    stats = {
        "tracks": len(records),
        "usable": len(usable),
        "errors": len(records) - len(usable),
        "stage1_candidates": stage1_candidates,
        "verified_pairs": len(todo),
        "acoustic_matches": verified,
        "metadata_matches": sum(
            1 for e in edges if e.kind == MATCH_SAME_TITLE
        ),
        "groups": len(groups),
        # Getrennt gezaehlt: eine andere Fassung (Remix, Live, Radio Edit)
        # ist kein Duplikat, auch wenn sie in derselben Gruppe steht.
        "duplicates": sum(
            1 for g in groups for m in g.members
            if m != g.best and g.kinds.get(m) != MATCH_SAME_TITLE
        ),
        "versions": sum(
            1 for g in groups for m in g.members
            if m != g.best and g.kinds.get(m) == MATCH_SAME_TITLE
        ),
    }
    return groups, stats


def redundant_bytes(records: list, groups: list) -> int:
    """Platz, den echte Duplikate neben dem Behalten-Vorschlag belegen.

    Andere Fassungen zaehlen nicht mit - wer einen Remix loescht, gewinnt
    keinen ueberfluessigen Platz zurueck, sondern verliert einen Track.
    """
    total = 0
    for group in groups:
        for member in group.members:
            if member != group.best and group.kinds.get(member) != MATCH_SAME_TITLE:
                total += int(records[member].get("size") or 0)
    return total


def _basename(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def _duration_fits(records: list, a: int, b: int) -> bool:
    da, db = _dur(records[a]), _dur(records[b])
    if da <= 0 or db <= 0:
        return True
    return max(da, db) / max(min(da, db), 1e-6) <= MAX_DURATION_RATIO


def _name_candidate_pairs(
    records: list, names: dict, usable: list, threshold: float
) -> dict:
    """Namensaehnliche Paare, vorgefiltert ueber gemeinsame Titelwoerter.

    Ohne diese Vorauswahl waeren es n^2 Textvergleiche.
    """
    buckets: dict = {}
    for i in usable:
        for token in blocking_tokens(names[i]):
            buckets.setdefault(token, []).append(i)

    pairs: dict = {}
    seen: set = set()
    for members in buckets.values():
        # Ein Wort, das die halbe Sammlung teilt, taugt nicht als Filter.
        if len(members) > 400:
            continue
        for pos, a in enumerate(members):
            for b in members[pos + 1:]:
                pair = (min(a, b), max(a, b))
                if pair in seen:
                    continue
                seen.add(pair)
                if not _duration_fits(records, a, b):
                    continue
                score = name_similarity(names[a], names[b])
                if score >= threshold:
                    pairs[pair] = score
    return pairs


def _version_edges(
    records: list,
    names: dict,
    usable: list,
    union: "_UnionFind",
    meta_pairs: dict,
    threshold: float,
) -> list:
    """Verbindet akustische Cluster, die denselben Song anders benennen.

    Bewusst *ohne* Verkettung: jedes weitere Cluster wird gegen das
    Startcluster geprueft. Damit kann aus A~B und B~C nicht faelschlich
    A~C werden.
    """
    clusters: dict = {}
    for i in usable:
        clusters.setdefault(union.find(i), []).append(i)

    # Ein Vertreter je Cluster - die beste Datei, denn ihre Tags sind meist
    # die gepflegtesten.
    reps: dict = {
        root: max(members, key=lambda i: _quality_sort_key(records[i]))
        for root, members in clusters.items()
    }

    linked: dict = {}
    for (a, b), score in meta_pairs.items():
        ra, rb = union.find(a), union.find(b)
        if ra == rb:
            continue
        key = (min(ra, rb), max(ra, rb))
        if score > linked.get(key, (0.0,))[0]:
            linked[key] = (score, a, b)

    neighbours: dict = {}
    for (ra, rb), value in linked.items():
        neighbours.setdefault(ra, {})[rb] = value
        neighbours.setdefault(rb, {})[ra] = value

    order = sorted(
        clusters, key=lambda r: (-len(clusters[r]), -_quality_sort_key(records[reps[r]])[0])
    )

    edges: list = []
    assigned: set = set()
    for seed in order:
        if seed in assigned or seed not in neighbours:
            continue
        assigned.add(seed)
        seed_rep = reps[seed]
        for other, (score, a, b) in neighbours[seed].items():
            if other in assigned:
                continue
            # Gegen den Startvertreter pruefen, nicht gegen den Nachbarn.
            direct = name_similarity(names[seed_rep], names[reps[other]])
            if direct < threshold or not _duration_fits(
                records, seed_rep, reps[other]
            ):
                continue
            assigned.add(other)
            edges.append(
                Edge(seed_rep, reps[other], MATCH_SAME_TITLE, max(score, direct))
            )
    return edges
