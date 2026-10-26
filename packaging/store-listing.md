# Microsoft Store listing

Copy-and-paste text for Partner Center. Both languages, because the app
ships both.

Field names follow Partner Center → *Store listings*.

---

## Submission checklist

1. **Register** (free) at <https://partner.microsoft.com/dashboard> →
   *Windows & Xbox*. Individual account: Microsoft account, photo ID and a
   selfie for identity verification. Allow a few days.
2. **Reserve the name** `MusicDupes` under *Create a new app*. This also
   tells you the three values the package needs:
   *Product identity* → **Package/Identity/Name**,
   **Package/Identity/Publisher**, **Package/Properties/PublisherDisplayName**.
3. Put those three into the repository as **Actions variables**
   (*Settings → Secrets and variables → Actions → Variables*):
   `STORE_IDENTITY`, `STORE_PUBLISHER`, `STORE_DISPLAY`.
   They are not secrets — Partner Center shows them publicly — but they do
   not belong hard-coded in the manifest either.
4. Push a tag (`v1.1.0`). The workflow builds `MusicDupes.msix` and attaches
   it as a build artifact.
5. Upload that file in Partner Center under *Packages*.
6. Fill in the listing from the text below, submit, wait for certification.

Microsoft signs the package after certification. That is what removes the
SmartScreen warning — you never buy or handle a certificate yourself.

### Notes for the certification report

* **Age rating:** the questionnaire will ask about user-generated content
  and data collection. MusicDupes collects nothing, sends nothing and has no
  network access at all. Expect a rating of 3+ / PEGI 3.
* **Privacy policy:** required even for apps that collect nothing. A single
  sentence hosted on the GitHub Pages of the repository is enough, see
  the draft at the bottom.
* **runFullTrust** is a restricted capability and triggers a justification
  prompt. Suggested wording: *"Desktop application that reads audio files
  from folders the user selects and invokes a bundled FFmpeg binary to
  decode them. No files are modified or deleted."*

---

## English listing

**Name**
```
MusicDupes
```

**Short description** (max. 100 characters)
```
Finds duplicate music files by the way they sound - and shows which copy to keep.
```

**Description**
```
MusicDupes finds duplicate music files by comparing the audio itself, not the
tags. The same track saved as FLAC and as MP3 is recognised as one recording
even when the file names and tags have nothing in common.

It also answers the question every duplicate finder leaves open: which of the
copies is actually the better one?

MEASURED, NOT READ

The "Bandwidth" column is derived from the audio signal rather than from the
tags. That exposes something no tag can tell you - a FLAC that was created
from an MP3. It takes up the space of a lossless file and still sounds like
the MP3 it came from. In that case the bigger file is the worse one.

  15-16 kHz   roughly 96-128 kbps
  19-20 kHz   roughly 256-320 kbps
  above 20 kHz   lossless or a very high bit rate

THREE VIEWS

- Duplicates: groups of files that belong together, with a suggestion which
  one to keep.
- Pair comparison: every file pair with two readings of the same
  measurement. "Coverage" asks how much of the shorter track sits inside the
  longer one; "Similarity" asks how much the files resemble each other
  overall. An original inside its extended mix has high coverage and only
  medium similarity.
- File quality: every file with a red-to-green rating for how well it holds
  up on a large PA system. Sortable and filterable.

BUILT FOR LARGE COLLECTIONS

Every file is decoded once. A fingerprint narrows thousands of files down to
a handful of candidates in milliseconds; only those are then compared in
detail, aligned in time against each other. Results are cached, so every
later scan takes seconds.

MusicDupes never modifies or deletes anything. It shows you what is there -
deleting stays your decision.

Free and open source: https://github.com/Akilo87/MusicDupes
```

**Features** (bullet list field)
```
Compares audio, not tags - works across formats and bit rates
Measures the real bandwidth and exposes MP3s disguised as FLAC
Tells you which copy of a duplicate is worth keeping
Finds trimmed versions and tracks hidden inside longer mixes
Rates every file for club and PA use
Exports everything to CSV
German and English, follows your Windows language
Never modifies or deletes a single file
```

**Search terms**
```
duplicate music
duplicate finder
audio fingerprint
music library
FLAC MP3 quality
DJ tools
transcode detection
```

---

## German listing

**Short description**
```
Findet doppelte Musikdateien anhand ihres Klangs - und zeigt, welche Kopie bleiben sollte.
```

**Description**
```
MusicDupes findet doppelte Musikdateien, indem es den Ton selbst vergleicht
und nicht die Tags. Derselbe Track als FLAC und als MP3 wird als eine
Aufnahme erkannt, auch wenn Dateiname und Beschriftung nichts gemeinsam
haben.

Und es beantwortet die Frage, die jedes andere Werkzeug offenlaesst: welche
der Kopien ist eigentlich die bessere?

GEMESSEN, NICHT ABGELESEN

Die Spalte "Bandbreite" stammt aus dem Tonsignal, nicht aus den Tags. Das
deckt etwas auf, das kein Tag verraet - eine FLAC, die aus einer MP3 erzeugt
wurde. Sie belegt den Platz einer verlustfreien Datei und klingt trotzdem wie
das MP3, aus dem sie stammt. In diesem Fall ist die groessere Datei die
schlechtere.

  15-16 kHz   entspricht etwa 96-128 kbps
  19-20 kHz   entspricht etwa 256-320 kbps
  ueber 20 kHz   verlustfrei oder sehr hohe Bitrate

DREI ANSICHTEN

- Duplikate: Gruppen zusammengehoerender Dateien mit Vorschlag, welche
  bleiben sollte.
- Paarvergleich: jedes Dateipaar mit zwei Lesarten derselben Messung.
  "Deckung" fragt, wie viel vom kuerzeren Track im laengeren steckt,
  "Aehnlichkeit", wie sehr sich die Dateien insgesamt gleichen. Ein Original
  in seinem Extended Mix hat hohe Deckung und nur mittlere Aehnlichkeit.
- Dateiqualitaet: jede Datei mit einer Bewertung von rot bis gruen, wie gut
  sie sich auf einer grossen Anlage macht. Sortier- und filterbar.

FUER GROSSE SAMMLUNGEN GEBAUT

Jede Datei wird einmal dekodiert. Ein Fingerabdruck engt tausende Dateien in
Millisekunden auf eine Handvoll Verdaechtige ein; nur die werden danach
genau verglichen und dabei zeitlich zueinander ausgerichtet. Ergebnisse
werden zwischengespeichert, jeder weitere Durchlauf dauert Sekunden.

MusicDupes veraendert und loescht nichts. Es zeigt, was da ist - geloescht
wird nach deiner Entscheidung.

Kostenlos und quelloffen: https://github.com/Akilo87/MusicDupes
```

**Features**
```
Vergleicht den Klang statt der Tags - quer ueber Formate und Bitraten
Misst die echte Bandbreite und entlarvt MP3s im FLAC-Gewand
Zeigt, welche Kopie eines Duplikats es wert ist zu bleiben
Findet beschnittene Fassungen und Tracks in laengeren Mixen
Bewertet jede Datei fuer den Einsatz auf grossen Anlagen
Exportiert alles als CSV
Deutsch und Englisch, folgt der Windows-Sprache
Veraendert und loescht niemals eine Datei
```

---

## Privacy policy draft

Required by the Store even when nothing is collected. Host it as
`docs/privacy.md` on GitHub Pages and link that URL.

```
MusicDupes privacy policy

MusicDupes does not collect, transmit or store any personal data.

The application has no network access. It reads the audio files in the
folder you select in order to analyse them, and writes its analysis results
to a local cache on your own computer. Nothing leaves your device.

MusicDupes never modifies or deletes your files.

Contact: <your e-mail address>
```
