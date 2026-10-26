"""Zweisprachigkeit: Deutsch und Englisch.

Alle sichtbaren Texte stehen hier unter stabilen Schlüsseln. Im übrigen Code
steht nie ein fertiger Satz, sondern immer ``t("schluessel")`` - sonst müsste
man beim Übersetzen jede Datei durchsuchen und würde Stellen übersehen.

Dasselbe gilt für die Auffälligkeiten eines Tracks: gespeichert werden
Schlüssel wie ``transcode``, nicht der deutsche Text. Die Empfehlungslogik
prüft auf diese Schlüssel und funktioniert dadurch in jeder Sprache gleich.
"""

from __future__ import annotations

import os

LANGUAGES = ("de", "en")
LANGUAGE_NAMES = {"de": "Deutsch", "en": "English"}

_current = "de"


def detect_language() -> str:
    """Rät die Sprache aus den Systemeinstellungen.

    Deutsch für Deutschland, Österreich und die Schweiz, sonst Englisch.
    """
    try:
        import ctypes

        # LANG_GERMAN ist 0x07; die oberen Bits unterscheiden nur DE/AT/CH.
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return "de" if (langid & 0x3FF) == 0x07 else "en"
    except Exception:
        pass

    for name in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(name, "")
        if value:
            return "de" if value.lower().startswith("de") else "en"

    try:
        import locale

        code = locale.getdefaultlocale()[0] or ""
        return "de" if code.lower().startswith("de") else "en"
    except Exception:
        return "en"


def set_language(code: str) -> str:
    """Setzt die Sprache. ``auto`` bedeutet: aus dem System übernehmen."""
    global _current
    if not code or code == "auto":
        code = detect_language()
    _current = code if code in LANGUAGES else "en"
    return _current


def language() -> str:
    return _current


def t(key: str, **values) -> str:
    """Text zu einem Schlüssel, notfalls auf Englisch, notfalls der Schlüssel."""
    text = TEXTS.get(_current, {}).get(key)
    if text is None:
        text = TEXTS["en"].get(key)
    if text is None:
        return key
    if values:
        try:
            return text.format(**values)
        except (KeyError, IndexError, ValueError):
            return text
    return text


# --------------------------------------------------------------------------
# Auffälligkeiten. Der Schlüssel wird gespeichert, der Text erst beim Anzeigen
# erzeugt - teilweise mit Zahlen aus dem Datensatz.
# --------------------------------------------------------------------------

FLAG_TRANSCODE = "transcode"
FLAG_HIRES_EMPTY = "hires_empty"
FLAG_CLIPPING = "clipping"
FLAG_MONO = "mono"
FLAG_LOW_BITRATE = "low_bitrate"
FLAG_QUIET = "quiet"


def flag_text(key: str, record: dict) -> str:
    """Baut den sichtbaren Text einer Auffälligkeit."""
    if key == FLAG_CLIPPING:
        return t("flag.clipping", value=(record.get("clip_ratio") or 0.0) * 100.0)
    return t("flag." + key)


def flag_texts(record: dict) -> list:
    return [flag_text(key, record) for key in (record.get("quality_flags") or [])]


DE = {
    # -- Fenster, Menü ----------------------------------------------------
    "menu.file": "&Datei",
    "menu.scan": "Scan starten",
    "menu.export_dupes": "Duplikate als CSV exportieren …",
    "menu.export_quality": "Qualitätsübersicht als CSV …",
    "menu.clear_cache": "Analyse-Cache leeren …",
    "menu.quit": "Beenden",
    "menu.help": "&Hilfe",
    "menu.how": "Wie die Erkennung funktioniert",
    "menu.licences": "Lizenzen und Mitwirkende",
    "lic.title": "Lizenzen",
    "lic.intro":
        "MusicDupes steht unter der MIT-Lizenz.\n\n"
        "Mitgeliefert werden außerdem Python (PSF), NumPy (BSD), "
        "Qt/PySide6 (LGPL-3.0) und FFmpeg (LGPL-3.0). Beide LGPL-Teile sind "
        "unverändert und austauschbar: in der Ordnerfassung liegen sie als "
        "einzelne Dateien bei, und der vollständige Quellcode dieses "
        "Programms steht offen, sodass sich jede Bibliothek ersetzen "
        "lässt.\n\n"
        "Quellen: https://ffmpeg.org/download.html und "
        "https://download.qt.io/",
    "lic.save": "Lizenztexte öffnen …",
    "lic.saved": "{count} Lizenzdatei(en) gespeichert unter:\n{path}",
    "lic.located": "Die {count} Lizenzdateien liegen unter:\n{path}",
    "lic.none": "Keine Lizenzdateien im Paket gefunden.",
    "menu.language": "&Sprache",
    "menu.lang_auto": "Automatisch (Systemsprache)",

    # -- Ordnerzeile -------------------------------------------------------
    "lbl.folder": "Ordner:",
    "ph.folder": "Ordner mit Musikdateien wählen …",
    "btn.browse": "Durchsuchen …",
    "btn.scan": "Scan starten",
    "btn.cancel": "Abbrechen",
    "dlg.choose_folder": "Musikordner wählen",

    # -- Einstellungen -----------------------------------------------------
    "grp.detection": "Erkennung",
    "lbl.audio_threshold": "Akustische Übereinstimmung ab {value} %",
    "lbl.audio_hint": "Wie viel vom kürzeren Track übereinstimmen muss",
    "lbl.meta_threshold": "Namensähnlichkeit ab {value} %",
    "chk.metadata": "Andere Fassungen über Interpret/Titel suchen",
    "chk.recursive": "Unterordner einbeziehen",
    "chk.cache": "Bekannte Dateien aus dem Cache nehmen",
    "btn.regroup": "Neu gruppieren",
    "tip.regroup": "Wendet geänderte Schwellwerte an, ohne noch einmal zu dekodieren.",
    "lbl.filter": "Filter:",
    "ph.filter": "Interpret, Titel oder Pfad …",
    "cmb.all_kinds": "Alle Trefferarten",
    "cmb.all_formats": "Alle Formate",
    "cmb.all_ratings": "Alle Bewertungen",
    "lbl.format": "Format:",
    "lbl.rating": "Bewertung:",
    "lbl.how_compared": "So wird verglichen",
    "lbl.which_keep": "Welche Datei behalten?",
    "lbl.pair_head": "Ähnlichkeit gegen Deckung",
    "lbl.quality_head": "Eignung für Club/Disco",

    # -- Reiter ------------------------------------------------------------
    "tab.duplicates": "Duplikate",
    "tab.pairs": "Paarvergleich",
    "tab.quality": "Dateiqualität",
    "tip.tab_duplicates": "Gefundene Duplikatgruppen mit Behalten-Vorschlag.",

    # -- Spalten -----------------------------------------------------------
    "col.file_group": "Datei / Gruppe",
    "col.hits": "Treffer",
    "col.kind": "Art",
    "col.quality": "Qualität",
    "col.format": "Format",
    "col.bitrate": "Bitrate",
    "col.bandwidth": "Bandbreite",
    "col.duration": "Dauer",
    "col.size": "Größe",
    "col.offset": "Versatz",
    "col.flags": "Auffälligkeiten",
    "col.folder": "Ordner",
    "col.group": "Gruppe",
    "col.file_a": "Datei A",
    "col.file_b": "Datei B",
    "col.similarity": "Ähnlichkeit",
    "col.coverage": "Deckung",
    "col.duration_a": "Dauer A",
    "col.duration_b": "Dauer B",
    "col.club": "Club-Eignung",
    "col.rating": "Bewertung",
    "col.samplerate": "Samplerate",
    "col.channels": "Kanäle",

    # -- Trefferarten ------------------------------------------------------
    "match.identical_file": "Identische Datei",
    "match.identical_audio": "Identischer Ton, andere Tags",
    "match.same_recording": "Gleiche Aufnahme",
    "match.same_title": "Gleicher Titel, andere Aufnahme",
    "match.reference": "Vergleichsbasis",

    "matchhelp.identical_file":
        "Bit für Bit dieselbe Datei – gleicher Prüfsummenwert über den "
        "gesamten Dateiinhalt.\n\nDas ist dieselbe Datei an zwei Orten. Eine "
        "der beiden ist ohne jeden Verlust entbehrlich.",
    "matchhelp.identical_audio":
        "Der dekodierte Ton ist Probe für Probe identisch, die Dateien "
        "unterscheiden sich aber – meist durch Tags, Cover oder den "
        "Zeitstempel.\n\nKlanglich gibt es keinen Unterschied. Behalte die "
        "Datei mit den besseren Tags.",
    "matchhelp.same_recording":
        "Dieselbe Aufnahme, aber neu kodiert: anderes Format, andere Bitrate, "
        "anderer Rip oder anderer Schnitt.\n\nKlingt gleich, ist aber nicht "
        "dieselbe Datei. Hier lohnt der Blick auf die Spalte Bandbreite.",
    "matchhelp.same_title":
        "Nur Interpret und Titel passen zusammen – der Klang nicht.\n\nFast "
        "immer eine andere Fassung: Remix, Live, Radio Edit oder ein anderer "
        "Künstler mit gleichem Songtitel. Das sind KEINE Duplikate im engeren "
        "Sinn. Bitte selbst prüfen.",
    "matchhelp.reference":
        "Der Vorschlag zum Behalten. Alle Prozentangaben dieser Gruppe "
        "beziehen sich auf diesen Track.",

    # -- Club-Eignung ------------------------------------------------------
    "club.very_good": "Sehr gut",
    "club.good": "Gut",
    "club.usable": "Brauchbar",
    "club.marginal": "Notfalls",
    "club.unsuitable": "Ungeeignet",

    # -- Auffälligkeiten ---------------------------------------------------
    "flag.transcode": "Transcode-Verdacht",
    "flag.hires_empty": "Hi-Res ohne Inhalt",
    "flag.clipping": "Clipping {value:.2f} %",
    "flag.mono": "Mono",
    "flag.low_bitrate": "Niedrige Bitrate",
    "flag.quiet": "Sehr leise",

    # -- Fortschritt -------------------------------------------------------
    "stage.find_files": "Suche Dateien",
    "stage.analyze": "Analysiere Dateien",
    "stage.hashes": "Vergleiche Datei-Hashes",
    "stage.candidates": "Suche Kandidaten",
    "stage.verify": "Prüfe Kandidaten",

    # -- Zustände, Meldungen ----------------------------------------------
    "state.ready": "Bereit",
    "state.done": "Fertig",
    "state.cancelling": "Wird abgebrochen …",
    "state.cancelled": "Abgebrochen",
    "state.failed": "Fehlgeschlagen",
    "state.no_data": "Keine Daten",
    "progress.of": "{stage} – {done} von {total} (%p %)",
    "progress.plain": "{stage} – {done}",
    "status.start": "Ordner wählen und Scan starten. {workers} Worker-Prozesse verfügbar.",
    "status.summary":
        "{tracks} Dateien geprüft ({cached} aus Cache, {fresh} neu analysiert) – "
        "{groups} Gruppen, {dupes} Duplikate, {versions} andere Fassungen, "
        "{wasted} redundant belegt – "
        "{seconds:.1f} s auf {workers} Prozessen",
    "status.errors": "  |  {count} Datei(en) nicht lesbar",
    "status.csv_written": "{rows} Zeilen nach {path} geschrieben",
    "status.cache_cleared": "Analyse-Cache geleert.",
    "msg.no_folder_title": "Ordner fehlt",
    "msg.no_folder": "Bitte zuerst einen gültigen Ordner wählen.",
    "msg.error": "Fehler",
    "msg.export": "Export",
    "msg.no_results": "Es gibt noch keine Ergebnisse zum Exportieren.",
    "msg.nothing_scanned": "Es wurde noch nichts eingelesen.",
    "msg.ffmpeg_missing": "ffmpeg fehlt",
    "msg.clear_cache_title": "Cache leeren",
    "msg.clear_cache":
        "Alle gespeicherten Analysen verwerfen?\n\nEs werden keine Musikdateien "
        "angerührt – nur die Datenbank unter\n{path}\n\nDer nächste Scan dauert "
        "dann wieder so lange wie der erste.",
    "msg.lang_title": "Sprache",
    "msg.lang_restart":
        "Die Sprache wird beim nächsten Start übernommen.\n\nDie Einstellung "
        "ist gespeichert – MusicDupes einfach schließen und neu öffnen.",
    "dlg.save_csv": "CSV speichern",
    "dlg.save_quality": "Qualitätsübersicht speichern",
    "dlg.csv_filter": "CSV-Dateien (*.csv)",
    "sel.none": "Keine Auswahl",
    "btn.play": "Abspielen",
    "btn.reveal": "Im Explorer zeigen",
    "btn.export": "CSV-Export …",
    "errors.header": "Nicht lesbar ({count} Dateien)",
    "errors.skipped": "übersprungen",
    "errors.detail_title": "Diese Datei konnte nicht gelesen werden.",
    "pairs.count": "{count} Paare",
    "pairs.visible": "{visible} von {total} Paaren",
    "quality.visible": "{visible} von {total} Dateien",
    "hits.by_name": "Name {value:.0f} %",
    "kept.tooltip":
        "Vorschlag zum Behalten: die beste Datei dieser Gruppe.\n"
        "Echte Duplikate daneben sind entbehrlich. Steht bei einer Datei\n"
        "„Gleicher Titel, andere Aufnahme“, ist sie eine andere Fassung –\n"
        "die bitte selbst prüfen.",

    # -- Detailanzeige -----------------------------------------------------
    "det.path": "Pfad",
    "det.artist": "Interpret",
    "det.title": "Titel",
    "det.album": "Album",
    "det.duration": "Dauer",
    "det.codec": "Codec",
    "det.lossless": "Verlustfrei",
    "det.bitrate": "Bitrate",
    "det.samplerate": "Samplerate",
    "det.channels": "Kanäle",
    "det.bitdepth": "Bittiefe",
    "det.bandwidth": "Gemessene Bandbreite",
    "det.peak": "Spitzenpegel",
    "det.rms": "Mittlerer Pegel",
    "det.clipping": "Übersteuerung",
    "det.score": "Qualitätsscore",
    "det.flags": "Auffälligkeiten",
    "det.size": "Größe",
    "val.yes": "ja",
    "val.no": "nein",
    "val.none": "keine",
    "val.mono": "Mono",
    "val.stereo": "Stereo",
    "val.score_of": "{value:.1f} von 100",

    # -- Zeilen-Tooltips ---------------------------------------------------
    "tip.by_name":
        "Über Interpret und Titel gefunden, nicht über den Klang.\n"
        "Akustisch stimmen nur {value:.0f} % überein – vermutlich eine\n"
        "andere Fassung. Bitte selbst prüfen.",
    "tip.offset":
        "Die gemeinsame Stelle liegt bei diesem Track um {value:.1f} s "
        "verschoben.\nTypisch für Extended Mixes mit langem Intro oder für\n"
        "einen Track innerhalb eines Sets.",
    "tip.lossy":
        "Verlustbehaftetes Format – auch bei hoher Bitrate.\n"
        "Verlustfrei sind FLAC, ALAC, WAV, APE, WavPack, TTA.",
    "tip.container_bitrate":
        "Mittelwert über die ganze Datei (aus dem Container).\n"
        "Bei VBR und verlustfreien Formaten normal.",
    "tip.bandwidth":
        "Am Ton gemessen, nicht aus den Tags gelesen.\n\n"
        "  15–16 kHz  →  etwa 96–128 kbps\n"
        "  19–20 kHz  →  etwa 256–320 kbps\n"
        "  über 20 kHz  →  verlustfrei oder sehr hohe Bitrate",
    "tip.flag_transcode":
        "Transcode-Verdacht: verlustfreies Format, aber der Ton endet\n"
        "weit unter 20 kHz. Sehr wahrscheinlich aus einer MP3 erzeugt.\n"
        "Die Dateigröße täuscht eine Qualität vor, die nicht drin ist –\n"
        "hier ist die größere Datei die schlechtere.",
    "tip.flag_clipping":
        "Clipping: Anteil der Proben an der Aussteuerungsgrenze.\n"
        "Bei lautgemasterten Clubtracks sind einige Prozent normal\n"
        "und kein Fehler der Datei – das steckt schon im Master.\n"
        "Innerhalb einer Gruppe trifft der Abzug meist alle gleich\n"
        "und ändert die Empfehlung nicht.",
    "tip.flag_hires":
        "Hi-Res ohne Inhalt: mehr als 48 kHz angegeben, aber\n"
        "oberhalb von 21 kHz steckt nichts drin.",
    "tip.pair_gap":
        "Deckung {coverage:.0f} %, Ähnlichkeit nur {similarity:.0f} %.\n\n"
        "Der kürzere Track steckt weitgehend im längeren,\n"
        "der längere enthält aber deutlich mehr Material.\n"
        "Typisch für Extended Mix gegen Original.",
    "tip.group_same_title":
        "\n\nDie Gruppe trägt diesen Namen, weil mindestens eine Datei\n"
        "nur über ihre Beschriftung dazugekommen ist.",
    "tip.headers": "Überschriften zeigen beim Überfahren, was die Spalte bedeutet.",

    # -- Engine ------------------------------------------------------------
    "engine.no_folder": "Ordner nicht gefunden: {path}",
    "engine.no_files": "Keine Audiodateien in diesem Ordner gefunden.",
    "engine.cancelled": "Abgebrochen.",
    "engine.no_audio": "Keine Audiodaten dekodierbar",
    "engine.ffprobe_failed": "ffprobe konnte die Datei nicht lesen",
    "engine.ffprobe_timeout": "ffprobe hat nach 2 Minuten nicht geantwortet",
    "engine.worker_failed": "Der Analyseprozess ist abgestürzt",
    "engine.no_stream": "Keine Audiospur gefunden",
    "engine.ffmpeg_missing":
        "ffmpeg wurde nicht gefunden. Lege einen FFmpeg-Build "
        "(win64-lgpl-shared von https://github.com/BtbN/FFmpeg-Builds) in den "
        "Ordner „ffmpeg“ neben dem Programm oder nimm ihn in den PATH auf.",
    "engine.ffprobe_missing":
        "ffprobe wurde nicht gefunden. Es gehört zur ffmpeg-Installation.",

    # -- CSV ---------------------------------------------------------------
    "csv.group": "Gruppe",
    "csv.group_kind": "Gruppenart",
    "csv.recommendation": "Empfehlung",
    "csv.keep": "behalten",
    "csv.acoustic": "Akustisch %",
    "csv.name_similarity": "Namensähnlichkeit %",
    "csv.match_kind": "Trefferart",
    "csv.artist": "Interpret",
    "csv.title": "Titel",
    "csv.album": "Album",
    "csv.duration": "Dauer",
    "csv.format": "Format",
    "csv.bitrate": "Bitrate kbps",
    "csv.lossless": "Verlustfrei",
    "csv.samplerate": "Samplerate",
    "csv.channels": "Kanäle",
    "csv.bandwidth": "Bandbreite Hz",
    "csv.score": "Qualitätsscore",
    "csv.flags": "Auffälligkeiten",
    "csv.offset": "Versatz s",
    "csv.size": "Größe Bytes",
    "csv.path": "Pfad",
    "csv.file": "Datei",
    "csv.club": "Club-Eignung",
    "csv.rating": "Bewertung",
    "csv.duration_s": "Dauer s",

    # -- Kommandozeile -----------------------------------------------------
    "cli.description": "Findet doppelte Musikdateien anhand ihres Klangs.",
    "cli.help_folder": "Ohne Oberfläche scannen",
    "cli.help_audio": "Schwelle für akustische Übereinstimmung (Standard {value})",
    "cli.help_meta": "Schwelle für Namensähnlichkeit (Standard {value})",
    "cli.help_nometa": "Nur akustisch vergleichen",
    "cli.help_flat": "Unterordner nicht einbeziehen",
    "cli.help_csv": "Ergebnis als CSV ablegen",
    "cli.help_lang": "Sprache: de, en oder auto",
    "cli.group_head": "=== {number}. {kind} – {name} ({count} Dateien)",
    "cli.keep": "   <= BEHALTEN",
    "cli.by_name": "[nur Name {value:.0f} %]",
    "cli.unreadable": "=== Nicht lesbar ({count} Dateien)",
    "cli.summary":
        "{tracks} Dateien, {groups} Gruppen, {dupes} Duplikate, "
        "{versions} andere Fassungen, {wasted} redundant belegt, {seconds:.1f} s",
    "cli.csv_written": "{rows} Zeilen nach {path} geschrieben",
}

EN = {
    "menu.file": "&File",
    "menu.scan": "Start scan",
    "menu.export_dupes": "Export duplicates as CSV …",
    "menu.export_quality": "Export quality overview as CSV …",
    "menu.clear_cache": "Clear analysis cache …",
    "menu.quit": "Quit",
    "menu.help": "&Help",
    "menu.how": "How detection works",
    "menu.licences": "Licences and credits",
    "lic.title": "Licences",
    "lic.intro":
        "MusicDupes is released under the MIT licence.\n\n"
        "It additionally ships Python (PSF), NumPy (BSD), Qt/PySide6 "
        "(LGPL-3.0) and FFmpeg (LGPL-3.0). Both LGPL components are "
        "unmodified and replaceable: in the folder build they ship as "
        "individual files, and the full source of this program is public, "
        "so any library can be swapped out.\n\n"
        "Sources: https://ffmpeg.org/download.html and "
        "https://download.qt.io/",
    "lic.save": "Open licence texts …",
    "lic.saved": "{count} licence file(s) saved to:\n{path}",
    "lic.located": "The {count} licence files are in:\n{path}",
    "lic.none": "No licence files found in the package.",
    "menu.language": "&Language",
    "menu.lang_auto": "Automatic (system language)",

    "lbl.folder": "Folder:",
    "ph.folder": "Choose a folder containing music files …",
    "btn.browse": "Browse …",
    "btn.scan": "Start scan",
    "btn.cancel": "Cancel",
    "dlg.choose_folder": "Choose music folder",

    "grp.detection": "Detection",
    "lbl.audio_threshold": "Acoustic match from {value} %",
    "lbl.audio_hint": "How much of the shorter track has to match",
    "lbl.meta_threshold": "Name similarity from {value} %",
    "chk.metadata": "Also find other versions via artist/title",
    "chk.recursive": "Include subfolders",
    "chk.cache": "Reuse known files from the cache",
    "btn.regroup": "Regroup",
    "tip.regroup": "Applies changed thresholds without decoding anything again.",
    "lbl.filter": "Filter:",
    "ph.filter": "Artist, title or path …",
    "cmb.all_kinds": "All match types",
    "cmb.all_formats": "All formats",
    "cmb.all_ratings": "All verdicts",
    "lbl.format": "Format:",
    "lbl.rating": "Verdict:",
    "lbl.how_compared": "How comparison works",
    "lbl.which_keep": "Which file to keep?",
    "lbl.pair_head": "Similarity versus coverage",
    "lbl.quality_head": "Suitability for club/disco",

    "tab.duplicates": "Duplicates",
    "tab.pairs": "Pair comparison",
    "tab.quality": "File quality",
    "tip.tab_duplicates": "Duplicate groups found, with a suggestion which to keep.",

    "col.file_group": "File / group",
    "col.hits": "Match",
    "col.kind": "Type",
    "col.quality": "Quality",
    "col.format": "Format",
    "col.bitrate": "Bit rate",
    "col.bandwidth": "Bandwidth",
    "col.duration": "Length",
    "col.size": "Size",
    "col.offset": "Offset",
    "col.flags": "Findings",
    "col.folder": "Folder",
    "col.group": "Group",
    "col.file_a": "File A",
    "col.file_b": "File B",
    "col.similarity": "Similarity",
    "col.coverage": "Coverage",
    "col.duration_a": "Length A",
    "col.duration_b": "Length B",
    "col.club": "Club rating",
    "col.rating": "Verdict",
    "col.samplerate": "Sample rate",
    "col.channels": "Channels",

    "match.identical_file": "Identical file",
    "match.identical_audio": "Identical audio, different tags",
    "match.same_recording": "Same recording",
    "match.same_title": "Same title, different recording",
    "match.reference": "Reference",

    "matchhelp.identical_file":
        "Byte for byte the same file – identical checksum over the entire "
        "file.\n\nThis is one file in two places. Either one can go without "
        "losing anything.",
    "matchhelp.identical_audio":
        "The decoded audio is identical sample for sample, but the files "
        "differ – usually in tags, cover art or timestamp.\n\nThere is no "
        "audible difference. Keep the one with the better tags.",
    "matchhelp.same_recording":
        "The same recording, re-encoded: different format, different bit "
        "rate, a different rip or a different edit.\n\nIt sounds the same but "
        "is not the same file. This is where the bandwidth column pays off.",
    "matchhelp.same_title":
        "Only artist and title match – the audio does not.\n\nAlmost always a "
        "different version: remix, live, radio edit, or a different artist "
        "with the same song title. These are NOT duplicates in the strict "
        "sense. Please check them yourself.",
    "matchhelp.reference":
        "The file suggested for keeping. Every percentage in this group is "
        "measured against this track.",

    "club.very_good": "Very good",
    "club.good": "Good",
    "club.usable": "Usable",
    "club.marginal": "At a pinch",
    "club.unsuitable": "Unsuitable",

    "flag.transcode": "Suspected transcode",
    "flag.hires_empty": "Hi-res without content",
    "flag.clipping": "Clipping {value:.2f} %",
    "flag.mono": "Mono",
    "flag.low_bitrate": "Low bit rate",
    "flag.quiet": "Very quiet",

    "stage.find_files": "Finding files",
    "stage.analyze": "Analysing files",
    "stage.hashes": "Comparing file hashes",
    "stage.candidates": "Finding candidates",
    "stage.verify": "Verifying candidates",

    "state.ready": "Ready",
    "state.done": "Done",
    "state.cancelling": "Cancelling …",
    "state.cancelled": "Cancelled",
    "state.failed": "Failed",
    "state.no_data": "No data",
    "progress.of": "{stage} – {done} of {total} (%p %)",
    "progress.plain": "{stage} – {done}",
    "status.start": "Choose a folder and start the scan. {workers} worker processes available.",
    "status.summary":
        "{tracks} files checked ({cached} from cache, {fresh} newly analysed) – "
        "{groups} groups, {dupes} duplicates, {versions} other versions, "
        "{wasted} redundantly occupied – "
        "{seconds:.1f} s on {workers} processes",
    "status.errors": "  |  {count} file(s) unreadable",
    "status.csv_written": "{rows} rows written to {path}",
    "status.cache_cleared": "Analysis cache cleared.",
    "msg.no_folder_title": "No folder",
    "msg.no_folder": "Please choose a valid folder first.",
    "msg.error": "Error",
    "msg.export": "Export",
    "msg.no_results": "There are no results to export yet.",
    "msg.nothing_scanned": "Nothing has been scanned yet.",
    "msg.ffmpeg_missing": "ffmpeg missing",
    "msg.clear_cache_title": "Clear cache",
    "msg.clear_cache":
        "Discard all stored analyses?\n\nNo music file is touched – only the "
        "database at\n{path}\n\nThe next scan will then take as long as the "
        "first one did.",
    "msg.lang_title": "Language",
    "msg.lang_restart":
        "The language will be applied on the next start.\n\nThe setting is "
        "saved – just close MusicDupes and open it again.",
    "dlg.save_csv": "Save CSV",
    "dlg.save_quality": "Save quality overview",
    "dlg.csv_filter": "CSV files (*.csv)",
    "sel.none": "Nothing selected",
    "btn.play": "Play",
    "btn.reveal": "Show in Explorer",
    "btn.export": "Export CSV …",
    "errors.header": "Unreadable ({count} files)",
    "errors.skipped": "skipped",
    "errors.detail_title": "This file could not be read.",
    "pairs.count": "{count} pairs",
    "pairs.visible": "{visible} of {total} pairs",
    "quality.visible": "{visible} of {total} files",
    "hits.by_name": "Name {value:.0f} %",
    "kept.tooltip":
        "Suggested keeper: the best file in this group.\n"
        "True duplicates next to it are expendable. A file marked\n"
        "\"Same title, different recording\" is another version –\n"
        "please check those yourself.",

    "det.path": "Path",
    "det.artist": "Artist",
    "det.title": "Title",
    "det.album": "Album",
    "det.duration": "Length",
    "det.codec": "Codec",
    "det.lossless": "Lossless",
    "det.bitrate": "Bit rate",
    "det.samplerate": "Sample rate",
    "det.channels": "Channels",
    "det.bitdepth": "Bit depth",
    "det.bandwidth": "Measured bandwidth",
    "det.peak": "Peak level",
    "det.rms": "Average level",
    "det.clipping": "Clipping",
    "det.score": "Quality score",
    "det.flags": "Findings",
    "det.size": "Size",
    "val.yes": "yes",
    "val.no": "no",
    "val.none": "none",
    "val.mono": "Mono",
    "val.stereo": "Stereo",
    "val.score_of": "{value:.1f} out of 100",

    "tip.by_name":
        "Found via artist and title, not via the audio.\n"
        "Acoustically only {value:.0f} % match – most likely a\n"
        "different version. Please check it yourself.",
    "tip.offset":
        "The shared passage sits {value:.1f} s off in this track.\n"
        "Typical for extended mixes with a long intro, or for a\n"
        "track inside a set.",
    "tip.lossy":
        "Lossy format – even at a high bit rate.\n"
        "Lossless formats are FLAC, ALAC, WAV, APE, WavPack, TTA.",
    "tip.container_bitrate":
        "Average across the whole file (taken from the container).\n"
        "Normal for VBR and for lossless formats.",
    "tip.bandwidth":
        "Measured from the audio, not read from the tags.\n\n"
        "  15–16 kHz  →  roughly 96–128 kbps\n"
        "  19–20 kHz  →  roughly 256–320 kbps\n"
        "  above 20 kHz  →  lossless or a very high bit rate",
    "tip.flag_transcode":
        "Suspected transcode: a lossless format, but the audio ends\n"
        "far below 20 kHz. Almost certainly made from an MP3.\n"
        "The file size pretends a quality that is not in there –\n"
        "here the bigger file is the worse one.",
    "tip.flag_clipping":
        "Clipping: share of samples sitting at full scale.\n"
        "For loudly mastered club tracks a few percent are normal\n"
        "and not a fault of the file – it is already in the master.\n"
        "Within a group the penalty usually hits everyone equally\n"
        "and does not change the recommendation.",
    "tip.flag_hires":
        "Hi-res without content: more than 48 kHz declared, but there\n"
        "is nothing above 21 kHz.",
    "tip.pair_gap":
        "Coverage {coverage:.0f} %, similarity only {similarity:.0f} %.\n\n"
        "The shorter track sits almost entirely inside the longer one,\n"
        "but the longer one holds considerably more material.\n"
        "Typical for an extended mix versus the original.",
    "tip.group_same_title":
        "\n\nThe group carries this name because at least one file joined\n"
        "it through its labelling alone.",
    "tip.headers": "Hover a heading to see what the column means.",

    "engine.no_folder": "Folder not found: {path}",
    "engine.no_files": "No audio files found in this folder.",
    "engine.cancelled": "Cancelled.",
    "engine.no_audio": "No decodable audio data",
    "engine.ffprobe_failed": "ffprobe could not read the file",
    "engine.ffprobe_timeout": "ffprobe did not respond within 2 minutes",
    "engine.worker_failed": "The analysis process crashed",
    "engine.no_stream": "No audio stream found",
    "engine.ffmpeg_missing":
        "ffmpeg was not found. Put an FFmpeg build (win64-lgpl-shared from "
        "https://github.com/BtbN/FFmpeg-Builds) into the \"ffmpeg\" folder next "
        "to the program, or add it to your PATH.",
    "engine.ffprobe_missing":
        "ffprobe was not found. It is part of the ffmpeg installation.",

    "csv.group": "Group",
    "csv.group_kind": "Group type",
    "csv.recommendation": "Recommendation",
    "csv.keep": "keep",
    "csv.acoustic": "Acoustic %",
    "csv.name_similarity": "Name similarity %",
    "csv.match_kind": "Match type",
    "csv.artist": "Artist",
    "csv.title": "Title",
    "csv.album": "Album",
    "csv.duration": "Length",
    "csv.format": "Format",
    "csv.bitrate": "Bit rate kbps",
    "csv.lossless": "Lossless",
    "csv.samplerate": "Sample rate",
    "csv.channels": "Channels",
    "csv.bandwidth": "Bandwidth Hz",
    "csv.score": "Quality score",
    "csv.flags": "Findings",
    "csv.offset": "Offset s",
    "csv.size": "Size bytes",
    "csv.path": "Path",
    "csv.file": "File",
    "csv.club": "Club rating",
    "csv.rating": "Verdict",
    "csv.duration_s": "Length s",

    "cli.description": "Finds duplicate music files by the way they sound.",
    "cli.help_folder": "Scan without the user interface",
    "cli.help_audio": "Threshold for acoustic match (default {value})",
    "cli.help_meta": "Threshold for name similarity (default {value})",
    "cli.help_nometa": "Compare acoustically only",
    "cli.help_flat": "Do not include subfolders",
    "cli.help_csv": "Write the result to a CSV file",
    "cli.help_lang": "Language: de, en or auto",
    "cli.group_head": "=== {number}. {kind} – {name} ({count} files)",
    "cli.keep": "   <= KEEP",
    "cli.by_name": "[name only {value:.0f} %]",
    "cli.unreadable": "=== Unreadable ({count} files)",
    "cli.summary":
        "{tracks} files, {groups} groups, {dupes} duplicates, "
        "{versions} other versions, {wasted} redundantly occupied, {seconds:.1f} s",
    "cli.csv_written": "{rows} rows written to {path}",
}

TEXTS = {"de": DE, "en": EN}
