"""Fuzzy-Vergleich von Interpret und Titel.

Zustaendig fuer die zweite Sorte Duplikat: denselben Song in einer anderen
Fassung (Radio Edit, Live, Remix, anderes Mastering). Akustisch sind das
verschiedene Aufnahmen - erkennbar sind sie nur ueber die Beschriftung.

Diese Treffer sind naturgemaess unsicherer als die akustischen und werden im
Programm deshalb getrennt ausgewiesen.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# Zusaetze hinter einem " - ", die den Song nicht zu einem anderen Song
# machen: andere Fassungen ("- Radio Edit") und Beiwerk ("- Remastered 2011").
# Klammerzusaetze fallen ohnehin komplett weg.
_SUFFIX_WORDS = (
    "remix", "mix", "live", "acoustic", "unplugged", "radio edit", "edit",
    "extended", "dub", "instrumental", "karaoke", "cover", "demo", "session",
    "version", "reprise", "vip", "bootleg", "mashup", "rework", "flip",
    "mono", "stereo", "remaster", "explicit", "official", "lyrics",
)
# Nur am Wortanfang: sonst steckte "live" in "deliver" und "dub" in
# "doubt", und "Love - Delivered" verloere seinen halben Titel.
_SUFFIX_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(w) for w in _SUFFIX_WORDS) + r")"
)

# "feat." und Verwandte schneiden den Rest ab. "with" nur beim Interpreten
# ("X with Y") - in Titeln ist es fast immer Teil des Titels: aus "Stay With
# Me" wuerde sonst "Stay", und das passte zu jedem anderen "Stay".
_FEAT_RE = re.compile(r"\b(feat|ft|featuring)\.?\s+.*$", re.IGNORECASE)
_WITH_RE = re.compile(r"\bwith\s+.*$", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\d+")
# Mehrfach-Interpreten, wie ffprobe sie aus einem Tag mit mehreren Werten
# zusammensetzt: "Queen;David Bowie".
_ARTIST_SPLIT_RE = re.compile(r"\s*[;/]\s*|\s+&\s+|\s*,\s+")
_BRACKET_RE = re.compile(r"[\(\[\{]([^\)\]\}]*)[\)\]\}]")
_TRACKNUM_RE = re.compile(r"^\s*\d{1,3}\s*[-._)]\s*")
_NONWORD_RE = re.compile(r"[^a-z0-9\s]+")
_SPACE_RE = re.compile(r"\s+")

# Titel, die zu haeufig sind, um allein etwas zu beweisen.
_GENERIC_TITLES = {
    "intro", "outro", "untitled", "track", "interlude", "bonus",
    "hidden track", "unknown", "skit", "prelude",
}


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(text: str, artist: bool = False) -> str:
    """Bringt einen Feldwert auf eine vergleichbare Form."""
    if not text:
        return ""
    value = strip_accents(text).lower()
    value = value.replace("&", " and ").replace("+", " and ")
    value = _TRACKNUM_RE.sub("", value)
    value = _FEAT_RE.sub("", value)
    if artist:
        value = _WITH_RE.sub("", value)
    value = _NONWORD_RE.sub(" ", value)
    return _SPACE_RE.sub(" ", value).strip()


def strip_version(title: str) -> str:
    """Entfernt Fassungs- und Beiwerkzusaetze aus einem Titel.

    Klammern fallen komplett weg - "(Radio Edit)", "(Official Video)",
    "(Zeds Dead Remix)" -, damit Original, Remix und Edit zueinander finden.
    Dazu ein nachgestelltes "- Radio Edit" ohne Klammern.
    """
    if not title:
        return ""
    stripped = _BRACKET_RE.sub(" ", title)
    if " - " in stripped:
        head, _, tail = stripped.rpartition(" - ")
        tail_low = strip_accents(tail).lower()
        if head.strip() and _SUFFIX_RE.search(tail_low):
            stripped = head
    return stripped.strip()


def primary_artist(text: str) -> str:
    """Nur der erste Interpret einer Mehrfachangabe.

    Dieselbe Datei wird je nach Quelle als "Queen" oder als
    "Queen;David Bowie" beschriftet - ein Tag mit mehreren Werten sieht je
    nach Leseweg anders aus. Fuer den Vergleich zaehlt deshalb nur der
    Hauptinterpret; angezeigt wird weiterhin die vollstaendige Angabe.
    """
    if not text:
        return ""
    first = _ARTIST_SPLIT_RE.split(text.strip(), maxsplit=1)[0]
    return first.strip() or text.strip()


def tokens(text: str, artist: bool = False) -> frozenset:
    return frozenset(t for t in normalize(text, artist).split() if len(t) > 1)


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


class TrackName:
    """Vorberechnete Vergleichsform eines Tracks."""

    __slots__ = ("artist", "title", "numbers", "key", "title_tokens",
                 "artist_tokens", "usable", "generic")

    def __init__(self, artist: str, title: str, filename: str = "") -> None:
        base_title = strip_version(title or "")
        if not base_title and filename:
            # Ohne Titel-Tag bleibt nur der Dateiname.
            base_title = strip_version(filename)
        main_artist = primary_artist(artist or "")
        self.artist = normalize(main_artist, artist=True)
        self.title = normalize(base_title)
        self.numbers = frozenset(int(n) for n in _NUMBER_RE.findall(self.title))
        self.title_tokens = tokens(base_title)
        self.artist_tokens = tokens(main_artist, artist=True)
        self.key = (self.artist + " " + self.title).strip()
        self.generic = self.title in _GENERIC_TITLES or len(self.title) < 3
        # Ohne Titel ist jeder Vergleich Raten.
        self.usable = bool(self.title) and not self.generic


def similarity(a: TrackName, b: TrackName) -> float:
    """Aehnlichkeit zweier Beschriftungen, 0..1.

    Titel zaehlt schwerer als Interpret: bei Samplern und Features ist die
    Interpretenangabe oft unvollstaendig, der Titel aber stabil.
    """
    if not a.usable or not b.usable:
        return 0.0

    # Verschiedene Zahlen im Titel heissen verschiedene Stuecke: "Track 01"
    # und "Track 02", "Symphony No. 5" und "Symphony No. 9". Ohne diese Regel
    # sehen sich solche Titel zum Verwechseln aehnlich.
    if a.numbers and b.numbers and a.numbers != b.numbers:
        return 0.0

    # Zeichenfolge und Wortmenge werden gemittelt, nicht maximiert: sonst
    # reicht schon ein einziges gemeinsames Wort ("Source A" / "Source B",
    # beide mit Wortmenge {source}) fuer volle Punktzahl.
    ratio = _ratio(a.title, b.title)
    if a.title_tokens and b.title_tokens:
        title_score = 0.5 * ratio + 0.5 * _jaccard(a.title_tokens, b.title_tokens)
    else:
        title_score = ratio
    if title_score < 0.6:
        return 0.0

    if a.artist and b.artist:
        artist_score = 0.5 * _ratio(a.artist, b.artist) + 0.5 * _jaccard(
            a.artist_tokens, b.artist_tokens
        )
        return 0.7 * title_score + 0.3 * artist_score

    # Ohne Interpretenangabe ist der Titel der einzige Beleg - dann muss er
    # sitzen. Kurze Titel reichen hier grundsaetzlich nicht.
    if title_score < 0.95 or len(a.title) < 10 or len(b.title) < 10:
        return 0.0
    return title_score * 0.9


def blocking_tokens(name: TrackName) -> frozenset:
    """Tokens, ueber die Kandidaten vorgefiltert werden.

    Ohne das waeren es n^2 Textvergleiche; so werden nur Paare geprueft, die
    sich mindestens ein Titelwort teilen.
    """
    return name.title_tokens
