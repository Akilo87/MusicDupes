"""Die längeren Erklärtexte, in beiden Sprachen.

Getrennt von :mod:`i18n`, weil das hier fast nur Fließtext ist und die kurzen
Beschriftungen sonst darin untergehen. Beim Import wird der Inhalt in die
Tabelle von :mod:`i18n` eingehängt.
"""

from __future__ import annotations

from .i18n import DE, EN

_DE = {
    "help.col.file_group":
        "<b>Datei / Gruppe</b><br><br>"
        "Fette Zeilen sind Gruppen, darunter stehen die zugehörigen Dateien."
        "<br>Der mit <b>*</b> markierte, grün hinterlegte Eintrag ist der "
        "Vorschlag zum Behalten.<br><br>"
        "Die Gruppe wird nach ihrem <i>schwächsten</i> Bindeglied benannt. "
        "Steht dort &bdquo;Gleicher Titel&ldquo;, hängt mindestens eine Datei "
        "nur über ihre Beschriftung mit drin.",

    "help.col.hits":
        "<b>Treffer</b><br><br>"
        "So viel vom <b>kürzeren</b> der beiden Tracks steckt im längeren."
        "<br><br>"
        "Deshalb sind 100 % bei ungleicher Länge kein Widerspruch: der kurze "
        "Track ist dann vollständig im langen enthalten – etwa ein Track, der "
        "auch in einem Mix vorkommt.<br><br>"
        "Verglichen wird immer gegen den Behalten-Vorschlag der Gruppe, nicht "
        "gegen die Zeile darüber.<br><br>"
        "Steht dort <span style='color:#b8860b'><b>Name 96 %</b></span>, wurde "
        "der Track über Interpret und Titel gefunden und <i>nicht</i> über den "
        "Klang. Die akustische Übereinstimmung liegt in dem Fall meist nahe "
        "null.",

    "help.col.kind":
        "<b>Art des Treffers</b><br><br>"
        "<b>Identische Datei</b><br>Bit für Bit dieselbe Datei. Eine der "
        "beiden ist ohne jeden Verlust entbehrlich.<br><br>"
        "<b>Identischer Ton, andere Tags</b><br>Der dekodierte Ton ist Probe "
        "für Probe gleich, die Dateien unterscheiden sich nur in Tags oder "
        "Cover. Klanglich kein Unterschied.<br><br>"
        "<b>Gleiche Aufnahme</b><br>Dieselbe Aufnahme, neu kodiert: anderes "
        "Format, andere Bitrate, anderer Rip, anderer Schnitt. Klingt gleich, "
        "ist aber nicht dieselbe Datei.<br><br>"
        "<b>Gleicher Titel, andere Aufnahme</b><br>Nur die Beschriftung passt, "
        "der Klang nicht. Fast immer eine andere Fassung – Remix, Live, Radio "
        "Edit – oder ein fremder Song mit gleichem Titel. <b>Keine Duplikate "
        "im engeren Sinn.</b><br><br>"
        "<b>Vergleichsbasis</b><br>Der Behalten-Vorschlag selbst.",

    "help.col.quality":
        "<b>Qualitätsscore (0–100)</b><br><br>"
        "Zusammengesetzt aus:<br>"
        "&bull; gemessene Bandbreite &nbsp;55 %<br>"
        "&bull; Format und Bitrate &nbsp;25 %<br>"
        "&bull; Samplerate &nbsp;12 %<br>"
        "&bull; Kanäle &nbsp;8 %<br>"
        "abzüglich Abschlägen für Transcode-Verdacht, Übersteuerung und "
        "Hi-Res-Angaben ohne Inhalt.<br><br>"
        "<b>Der Score entscheidet nicht allein</b>, welche Datei empfohlen "
        "wird. Zuerst zählt die gemessene Bandbreite, dann echt verlustfrei, "
        "erst danach der Score. Sonst würde ein Abzug für Übersteuerung – den "
        "lautgemasterte Clubtracks praktisch immer kassieren – eine "
        "verlustbehaftete Datei nach vorn schieben.<br><br>"
        "Ein niedriger Wert bei alten oder absichtlich dumpfen Aufnahmen ist "
        "kein Fehler. Der Score misst den Datenträger, nicht die Musik.",

    "help.col.format":
        "<b>Format</b><br><br>"
        "Der tatsächlich verwendete Codec, ausgelesen aus dem Stream – nicht "
        "die Dateiendung.<br><br>"
        "Verlustfrei sind unter anderem FLAC, ALAC, WAV (PCM), APE, WavPack, "
        "TTA. Alles andere ist verlustbehaftet, auch bei hoher Bitrate: EAC3, "
        "AAC, MP3, Vorbis, Opus, WMA.",

    "help.col.bitrate":
        "<b>Bitrate</b><br><br>"
        "Ein <b>~</b> davor heißt: der Wert stammt aus dem Container und ist "
        "über die ganze Datei gemittelt. Bei VBR und bei verlustfreien "
        "Formaten ist das normal.<br><br>"
        "Die Bitrate sagt <i>nichts</i> darüber, wie gut der Ton wirklich ist "
        "– eine aus MP3 erzeugte FLAC hat eine hohe Bitrate und trotzdem den "
        "Inhalt der MP3. Verlass dich stattdessen auf die Bandbreite.",

    "help.col.bandwidth":
        "<b>Gemessene Bandbreite</b><br><br>"
        "Die höchste Frequenz, in der noch echtes Signal steckt – <b>am Ton "
        "gemessen</b>, nicht aus den Tags gelesen. Die verlässlichste Spalte "
        "der ganzen Liste.<br><br>"
        "Verlustbehaftete Codecs schneiden oben hart ab, und dieser Schnitt "
        "ist sichtbar:<br><br>"
        "&nbsp;&nbsp;15–16 kHz &nbsp;&rarr;&nbsp; etwa 96–128 kbps<br>"
        "&nbsp;&nbsp;19–20 kHz &nbsp;&rarr;&nbsp; etwa 256–320 kbps<br>"
        "&nbsp;&nbsp;über 20 kHz &nbsp;&rarr;&nbsp; verlustfrei oder sehr hohe "
        "Bitrate<br><br>"
        "Was hier steht, gilt – unabhängig davon, was Dateiendung, Bitrate "
        "oder Dateigröße behaupten.",

    "help.col.duration":
        "<b>Dauer</b><br><br>"
        "Spielzeit laut Container.<br><br>"
        "Deutlich unterschiedliche Längen in einer Gruppe sind der Normalfall "
        "bei Extended Mixes, Radio Edits und abgebrochenen Downloads. Die "
        "Spalte Versatz zeigt, wo die Tracks zueinander liegen.",

    "help.col.size":
        "<b>Dateigröße</b><br><br>"
        "Kein Qualitätsmerkmal. Eine aus einer MP3 erzeugte FLAC ist um ein "
        "Vielfaches größer als ihr Original und enthält exakt dieselbe Musik.",

    "help.col.offset":
        "<b>Zeitversatz</b><br><br>"
        "Um wie viel dieser Track gegenüber dem Behalten-Vorschlag verschoben "
        "liegt.<br><br>"
        "<b>+58,9 s</b> heißt: die gemeinsame Stelle beginnt im längeren Track "
        "erst nach knapp einer Minute. Typisch für Extended Mixes mit langem "
        "Intro, oder für einen Track innerhalb eines Sets.<br><br>"
        "Ein Strich bedeutet, dass beide Tracks am selben Punkt beginnen.",

    "help.col.flags":
        "<b>Auffälligkeiten</b><br><br>"
        "<b><span style='color:#c0392b'>Transcode-Verdacht</span></b><br>"
        "Verlustfreies Format, aber der Ton endet weit unter 20 kHz. Die Datei "
        "wurde sehr wahrscheinlich aus einer MP3 erzeugt. Sie belegt den Platz "
        "einer verlustfreien Datei und klingt wie das MP3, aus dem sie stammt. "
        "<b>Hier ist die größere Datei die schlechtere.</b><br><br>"
        "<b>Clipping x %</b><br>Anteil der Proben, die an der "
        "Aussteuerungsgrenze liegen. Bei modernen, lautgemasterten Clubtracks "
        "sind einige Prozent völlig normal und kein Fehler der Datei – das "
        "steckt schon im Master. Innerhalb einer Gruppe trifft der Abzug meist "
        "alle Beteiligten gleich und ändert die Empfehlung nicht.<br><br>"
        "<b>Hi-Res ohne Inhalt</b><br>Mehr als 48 kHz angegeben, aber "
        "oberhalb von 21 kHz ist nichts drin.<br><br>"
        "<b>Mono</b> &nbsp;/&nbsp; <b>Niedrige Bitrate</b> &nbsp;/&nbsp; "
        "<b>Sehr leise</b><br>Selbsterklärend.",

    "help.col.folder":
        "<b>Ordner</b><br><br>"
        "Wo die Datei liegt. Doppelklick auf eine Zeile öffnet sie im Explorer.",

    "help.col.similarity":
        "<b>Ähnlichkeit</b><br><br>"
        "Wie sehr sich die beiden Dateien <b>insgesamt</b> gleichen. Der "
        "gemeinsame Teil wird am <b>längeren</b> der beiden Tracks gemessen."
        "<br><br>"
        "Das ist die Antwort auf &bdquo;wie ähnlich sind die beiden "
        "Dateien?&ldquo; – und damit eine andere Frage als in der Spalte "
        "Deckung.",

    "help.col.coverage":
        "<b>Deckung</b><br><br>"
        "Wie viel vom <b>kürzeren</b> Track im längeren steckt. Das ist "
        "dieselbe Zahl wie im Reiter Duplikate.<br><br>"
        "<b>Der Unterschied beider Spalten ist die eigentliche Aussage:</b>"
        "<br><br>"
        "Deckung hoch, Ähnlichkeit niedrig &rarr; der kurze Track steckt "
        "komplett im langen, der lange hat aber viel mehr Material. Klassisch "
        "für Extended Mix gegen Original oder für einen Track in einem Set."
        "<br><br>"
        "Beide hoch &rarr; die Dateien sind praktisch dasselbe.<br><br>"
        "Beide niedrig &rarr; wenig gemeinsam; steht die Zeile trotzdem in "
        "einer Gruppe, kam sie über Interpret und Titel dazu.",

    "help.col.file_a":
        "<b>Datei A</b><br><br>"
        "Erste Datei des Paares. Die Auswahl einer Zeile zeigt ihre Details "
        "unten an.",
    "help.col.file_b": "<b>Datei B</b><br><br>Zweite Datei des Paares.",
    "help.col.group":
        "<b>Gruppe</b><br><br>"
        "Nummer der Duplikatgruppe aus dem ersten Reiter. Eine Gruppe mit vier "
        "Dateien ergibt hier sechs Paare.",

    "help.col.club":
        "<b>Club-Eignung (0–100)</b><br><br>"
        "Wie gut sich die Datei auf einer großen Anlage macht. Bewusst etwas "
        "anderes als der Qualitätsscore im ersten Reiter.<br><br>"
        "Entscheidend ist fast nur die <b>gemessene Bandbreite</b> – auf einer "
        "Clubanlage hört man einem 128er-MP3 sofort an, dass oben nichts mehr "
        "kommt. Dazu ein kleiner Bonus für echt verlustfrei, deutliche "
        "Abschläge für Mono und für Samplerates unter 44,1 kHz.<br><br>"
        "<b>Übersteuerung wird erst ab 5 % abgewertet.</b> Ein paar Prozent "
        "stecken bei modernen Clubtracks im Master und machen die Datei nicht "
        "untauglich – deshalb fällt der Abzug hier viel milder aus als beim "
        "allgemeinen Qualitätsscore.",

    "help.col.rating":
        "<b>Bewertung</b><br><br>"
        "&nbsp;&nbsp;<b>Sehr gut</b> &nbsp;ab 88 – verlustfrei oder volle "
        "Bandbreite<br>"
        "&nbsp;&nbsp;<b>Gut</b> &nbsp;ab 70 – etwa ab 256 kbps<br>"
        "&nbsp;&nbsp;<b>Brauchbar</b> &nbsp;ab 50 – etwa 192 kbps<br>"
        "&nbsp;&nbsp;<b>Notfalls</b> &nbsp;ab 30 – etwa 128 kbps, hörbar "
        "dumpf<br>"
        "&nbsp;&nbsp;<b>Ungeeignet</b> &nbsp;darunter – auf einer großen "
        "Anlage peinlich<br><br>"
        "Über die Auswahlfelder oben lässt sich gezielt filtern, etwa auf "
        "alles unterhalb von &bdquo;Gut&ldquo;.",

    "help.col.samplerate":
        "<b>Samplerate</b><br><br>"
        "Abtastrate des Streams. 44,1 kHz ist der CD-Standard und völlig "
        "ausreichend.<br><br>"
        "Weniger als 44,1 kHz begrenzt die Bandbreite hart und wird "
        "abgewertet. Mehr als 48 kHz bringt hörbar nichts – und wenn oberhalb "
        "von 21 kHz nichts drin ist, steht das als &bdquo;Hi-Res ohne "
        "Inhalt&ldquo; in den Auffälligkeiten.",

    "help.col.channels":
        "<b>Kanäle</b><br><br>"
        "Mono fällt auf einer Stereoanlage sofort auf und wird deutlich "
        "abgewertet.",

    "help.audio_threshold":
        "<b>Akustische Übereinstimmung</b><br><br>"
        "Ab wie viel Prozent zwei Tracks als dieselbe Aufnahme gelten.<br><br>"
        "Gemessen wird, wie viel vom <b>kürzeren</b> Track im längeren steckt. "
        "Verglichen wird der Klang selbst, nicht die Beschriftung – deshalb "
        "funktioniert es quer über Formate und Bitraten hinweg.<br><br>"
        "<b>90 %</b> ist die Voreinstellung: streng, findet praktisch nur "
        "echte Duplikate.<br><br>"
        "Gekürzte Fassungen und Tracks mit längerem Vorlauf findet schon die "
        "Voreinstellung: beide Tracks werden vor dem Vergleich zeitlich "
        "ausgerichtet.<br><br>"
        "<b>Niedriger</b> (70–85 %) findet zusätzlich Fassungen, die nur über "
        "weite Strecken übereinstimmen – etwa einen Extended Mix, der "
        "mittendrin Takte einfügt, oder ein deutlich anderes Mastering.<br>"
        "<b>Noch niedriger</b> (50–60 %) findet auch entfernte Verwandte – "
        "dafür musst du deutlich mehr selbst nachsehen.<br><br>"
        "Nach einer Änderung genügt <b>Neu gruppieren</b>. Das dauert "
        "Sekunden, weil nichts neu dekodiert wird.",

    "help.meta_threshold":
        "<b>Namensähnlichkeit</b><br><br>"
        "Ab wie viel Prozent zwei Tracks über Interpret und Titel "
        "zusammengehören – unabhängig davon, wie sie klingen.<br><br>"
        "Damit findest du andere Fassungen desselben Songs: Remix, Live, Radio "
        "Edit, anderes Mastering. Solche Treffer sind naturgemäß unsicher und "
        "stehen deshalb getrennt als "
        "<span style='color:#b8860b'><b>Name 96 %</b></span>.<br><br>"
        "Zusätze in Klammern wie &bdquo;(Official Video)&ldquo; oder "
        "&bdquo;(Zeds Dead Remix)&ldquo; und angehängte wie "
        "&bdquo;- Remastered 2011&ldquo; werden vor dem Vergleich entfernt – "
        "so finden Original und Remix zueinander. Verschiedene Zahlen im "
        "Titel (&bdquo;Track 1&ldquo; / &bdquo;Track 2&ldquo;) gelten als "
        "verschiedene Stücke.<br><br>"
        "Fehlt bei beiden der Interpret, muss der Titel nahezu gleich sein – "
        "sonst würden Dateinamen wie &bdquo;Track 01&ldquo; alles mit allem "
        "verbinden.<br><br>"
        "<b>Runter auf 60–70 %</b> nur, wenn deine Tags schlecht gepflegt "
        "sind. Rechne dann mit Fehltreffern.",

    "help.detection":
        "<b>So wird verglichen</b><br><br>"
        "Jede Datei wird einmal dekodiert. Der Vergleich läuft danach in zwei "
        "Stufen:<br><br>"
        "<b>1. Kandidatensuche.</b> Aus dem Spektrum werden markante Punkte "
        "gepickt und paarweise verknüpft. Ein Index findet damit aus tausenden "
        "Dateien in Millisekunden die wenigen Verdächtigen.<br><br>"
        "<b>2. Nachrechnung.</b> Nur diese Kandidaten werden dicht verglichen "
        "– zeitlich zueinander ausgerichtet und dann Stück für Stück geprüft. "
        "Erst diese Zahl steht in der Spalte Treffer.<br><br>"
        "Die zweite Stufe ist der Grund, warum die Prozentzahl etwas taugt: "
        "ein beschnittener Track kann in Stufe 1 auf 20 % fallen, obwohl es "
        "dieselbe Aufnahme ist. Stufe 2 kennt dieses Problem nicht.<br><br>"
        "<b>MusicDupes verändert und löscht nichts.</b>",

    "help.recommendation":
        "<b>Welche Datei behalten?</b><br><br>"
        "Der mit <b>*</b> markierte, grün hinterlegte Eintrag ist der "
        "Vorschlag. Entschieden wird in dieser Reihenfolge:<br><br>"
        "1. <b>Gemessene Bandbreite</b> – die einzige Angabe, die nicht lügen "
        "kann<br>"
        "2. <b>Echt verlustfrei</b> – ein Transcode-Verdacht zählt hier nicht "
        "als verlustfrei<br>"
        "3. Qualitätsscore<br>"
        "4. Dauer, dann Bitrate, dann Größe<br><br>"
        "Die Bandbreite steht bewusst vorn: eine aus MP3 erzeugte FLAC würde "
        "sonst allein wegen Format und Dateigröße ihr eigenes Original "
        "schlagen.",

    "help.tab_pairs":
        "<b>Paarvergleich</b><br><br>"
        "Jedes Dateipaar einer Gruppe einzeln – mit beiden Lesarten desselben "
        "Vergleichs nebeneinander.<br><br>"
        "<b>Deckung</b> misst am kürzeren Track: &bdquo;Wie viel davon steckt "
        "im längeren?&ldquo;<br>"
        "<b>Ähnlichkeit</b> misst am längeren: &bdquo;Wie sehr gleichen sich "
        "die Dateien insgesamt?&ldquo;<br><br>"
        "Beispiel: ein Original von 3:51 gegen seinen Extended Mix von 6:32. "
        "Das Original steckt fast vollständig im Extended – die Deckung ist "
        "hoch. Als Dateien gleichen sich die beiden trotzdem nur zur Hälfte, "
        "denn der Extended enthält viel Material, das im Original nicht "
        "vorkommt. Die Ähnlichkeit fällt entsprechend niedriger aus.<br><br>"
        "Zum Finden von Duplikaten taugt die Deckung, zum Beurteilen die "
        "Ähnlichkeit.<br><br>"
        "Jede Spalte lässt sich durch Klick auf die Überschrift sortieren.",

    "help.tab_quality":
        "<b>Dateiqualität</b><br><br>"
        "Alle eingelesenen Dateien, unabhängig davon, ob sie doppelt sind."
        "<br><br>"
        "Der Balken zeigt die Eignung für eine große Anlage: von <span "
        "style='color:#c85032'>rot</span> (ungeeignet) bis <span "
        "style='color:#50b050'>grün</span> (sehr gut). Maßgeblich ist die am "
        "Ton <b>gemessene</b> Bandbreite, nicht das Format und nicht die "
        "Dateigröße.<br><br>"
        "Sortiere nach <b>Club-Eignung</b>, um die schwachen Dateien nach oben "
        "zu holen, oder nach <b>Format</b>, um etwa alle MP3 zusammen zu "
        "sehen. Die Auswahlfelder filtern zusätzlich nach Format und "
        "Bewertung.<br><br>"
        "Achte auf <span style='color:#c0392b'><b>Transcode-Verdacht</b>"
        "</span>: diese Dateien sehen nach verlustfrei aus, klingen aber wie "
        "das MP3, aus dem sie gemacht wurden.",

    "help.dialog": """\
MusicDupes vergleicht den KLANG, nicht die Tags.

Jede Datei wird einmal dekodiert. Daraus entstehen zwei Dinge:

1. Ein Fingerabdruck aus markanten Punkten im Spektrum. Er dient dazu, aus
   tausenden Dateien schnell die wenigen Verdächtigen herauszufischen.
2. Ein dichtes Klangprofil. Nur dieses entscheidet über die Prozentzahl.
   Beide Tracks werden dabei zeitlich zueinander ausgerichtet – deshalb wird
   ein Duplikat auch dann erkannt, wenn es beschnitten ist oder mehr Vorlauf
   hat.

Die Prozentzahl im Reiter Duplikate bedeutet: so viel vom KÜRZEREN Track
steckt im längeren. 100 % bei ungleicher Länge heißt also "vollständig
enthalten". Im Reiter Paarvergleich steht daneben die Ähnlichkeit, die am
längeren Track misst und damit sagt, wie sehr sich die Dateien insgesamt
gleichen.

Trefferarten, von sicher nach unsicher:

  Identische Datei          Bit für Bit dieselbe Datei.
  Identischer Ton           Gleicher Klang, nur andere Tags.
  Gleiche Aufnahme          Anderes Format oder andere Bitrate.
  Gleicher Titel            Nur die Beschriftung passt – vermutlich eine
                            andere Fassung (Remix, Live, Radio Edit).
                            Diese Treffer bitte selbst prüfen.

WELCHE DATEI IST DIE BESSERE?

Der mit * markierte, grün hinterlegte Eintrag ist der Vorschlag. Wichtiger
als die Bitrate ist die Spalte "Bandbreite": sie wird am Ton GEMESSEN, nicht
aus den Tags gelesen.

  ca. 15-16 kHz   entspricht etwa 96-128 kbps
  ca. 19-20 kHz   entspricht etwa 256-320 kbps
  über 20 kHz     verlustfrei oder sehr hohe Bitrate

Steht bei einer FLAC oder WAV "Transcode-Verdacht", endet ihr Ton weit unter
20 kHz. Dann wurde sie sehr wahrscheinlich aus einer MP3 erzeugt: sie belegt
den Platz einer verlustfreien Datei, klingt aber wie das MP3, aus dem sie
stammt. In so einem Fall ist die große Datei die schlechtere.

MusicDupes verändert und löscht nichts. Es zeigt nur an.""",
}

_EN = {
    "help.col.file_group":
        "<b>File / group</b><br><br>"
        "Bold rows are groups; the files belonging to them sit underneath."
        "<br>The entry marked with <b>*</b> and highlighted green is the one "
        "suggested for keeping.<br><br>"
        "A group is named after its <i>weakest</i> link. If it says "
        "&ldquo;Same title&rdquo;, at least one file got in through its "
        "labelling alone.",

    "help.col.hits":
        "<b>Match</b><br><br>"
        "How much of the <b>shorter</b> of the two tracks sits inside the "
        "longer one.<br><br>"
        "That is why 100 % at different lengths is no contradiction: the short "
        "track is then fully contained in the long one – a track that also "
        "appears inside a mix, for instance.<br><br>"
        "The comparison is always against the group's keep suggestion, not "
        "against the row above.<br><br>"
        "If it reads <span style='color:#b8860b'><b>Name 96 %</b></span>, the "
        "track was found via artist and title and <i>not</i> via the audio. "
        "The acoustic match is usually close to zero in that case.",

    "help.col.kind":
        "<b>Match type</b><br><br>"
        "<b>Identical file</b><br>Byte for byte the same file. Either one can "
        "go without losing anything.<br><br>"
        "<b>Identical audio, different tags</b><br>The decoded audio is the "
        "same sample for sample; the files differ only in tags or cover art. "
        "No audible difference.<br><br>"
        "<b>Same recording</b><br>The same recording, re-encoded: different "
        "format, bit rate, rip or edit. Sounds the same but is not the same "
        "file.<br><br>"
        "<b>Same title, different recording</b><br>Only the labelling matches, "
        "the audio does not. Almost always a different version – remix, live, "
        "radio edit – or an unrelated song with the same title. <b>Not "
        "duplicates in the strict sense.</b><br><br>"
        "<b>Reference</b><br>The keep suggestion itself.",

    "help.col.quality":
        "<b>Quality score (0–100)</b><br><br>"
        "Made up of:<br>"
        "&bull; measured bandwidth &nbsp;55 %<br>"
        "&bull; format and bit rate &nbsp;25 %<br>"
        "&bull; sample rate &nbsp;12 %<br>"
        "&bull; channels &nbsp;8 %<br>"
        "minus penalties for suspected transcodes, clipping and hi-res claims "
        "without content.<br><br>"
        "<b>The score does not decide alone</b> which file gets recommended. "
        "Measured bandwidth comes first, then genuinely lossless, and only "
        "then the score. Otherwise a clipping penalty – which loudly mastered "
        "club tracks collect almost every time – would push a lossy file "
        "ahead.<br><br>"
        "A low value on old or deliberately dull recordings is not a fault. "
        "The score measures the carrier, not the music.",

    "help.col.format":
        "<b>Format</b><br><br>"
        "The codec actually in use, read from the stream – not the file "
        "extension.<br><br>"
        "Lossless formats include FLAC, ALAC, WAV (PCM), APE, WavPack and TTA. "
        "Everything else is lossy, even at a high bit rate: EAC3, AAC, MP3, "
        "Vorbis, Opus, WMA.",

    "help.col.bitrate":
        "<b>Bit rate</b><br><br>"
        "A leading <b>~</b> means the value comes from the container and is "
        "averaged across the whole file. That is normal for VBR and for "
        "lossless formats.<br><br>"
        "The bit rate says <i>nothing</i> about how good the audio really is – "
        "a FLAC made from an MP3 has a high bit rate and still holds the "
        "content of that MP3. Rely on the bandwidth instead.",

    "help.col.bandwidth":
        "<b>Measured bandwidth</b><br><br>"
        "The highest frequency that still carries real signal – <b>measured "
        "from the audio</b>, not read from the tags. The most trustworthy "
        "column in the whole list.<br><br>"
        "Lossy codecs cut off hard at the top, and that cut is visible:<br><br>"
        "&nbsp;&nbsp;15–16 kHz &nbsp;&rarr;&nbsp; roughly 96–128 kbps<br>"
        "&nbsp;&nbsp;19–20 kHz &nbsp;&rarr;&nbsp; roughly 256–320 kbps<br>"
        "&nbsp;&nbsp;above 20 kHz &nbsp;&rarr;&nbsp; lossless or a very high "
        "bit rate<br><br>"
        "What stands here holds – no matter what the extension, the bit rate "
        "or the file size claim.",

    "help.col.duration":
        "<b>Length</b><br><br>"
        "Playing time according to the container.<br><br>"
        "Clearly different lengths within a group are the normal case for "
        "extended mixes, radio edits and interrupted downloads. The offset "
        "column shows how the tracks sit relative to each other.",

    "help.col.size":
        "<b>File size</b><br><br>"
        "Not a mark of quality. A FLAC made from an MP3 is many times larger "
        "than its original and holds exactly the same music.",

    "help.col.offset":
        "<b>Time offset</b><br><br>"
        "How far this track sits shifted against the keep suggestion.<br><br>"
        "<b>+58.9 s</b> means the shared passage only starts about a minute "
        "into the longer track. Typical for extended mixes with a long intro, "
        "or for a track inside a set.<br><br>"
        "A dash means both tracks start at the same point.",

    "help.col.flags":
        "<b>Findings</b><br><br>"
        "<b><span style='color:#c0392b'>Suspected transcode</span></b><br>"
        "A lossless format, but the audio ends far below 20 kHz. The file was "
        "almost certainly made from an MP3. It occupies the space of a lossless "
        "file and sounds like the MP3 it came from. <b>Here the bigger file is "
        "the worse one.</b><br><br>"
        "<b>Clipping x %</b><br>Share of samples sitting at full scale. For "
        "modern, loudly mastered club tracks a few percent are entirely normal "
        "and not a fault of the file – it is already in the master. Within a "
        "group the penalty usually hits everyone equally and does not change "
        "the recommendation.<br><br>"
        "<b>Hi-res without content</b><br>More than 48 kHz declared, but there "
        "is nothing above 21 kHz.<br><br>"
        "<b>Mono</b> &nbsp;/&nbsp; <b>Low bit rate</b> &nbsp;/&nbsp; "
        "<b>Very quiet</b><br>Self-explanatory.",

    "help.col.folder":
        "<b>Folder</b><br><br>"
        "Where the file lives. Double-clicking a row opens it in Explorer.",

    "help.col.similarity":
        "<b>Similarity</b><br><br>"
        "How much the two files resemble each other <b>overall</b>. The shared "
        "part is measured against the <b>longer</b> of the two tracks.<br><br>"
        "This answers &ldquo;how similar are these two files?&rdquo; – a "
        "different question from the coverage column.",

    "help.col.coverage":
        "<b>Coverage</b><br><br>"
        "How much of the <b>shorter</b> track sits inside the longer one. Same "
        "number as in the Duplicates tab.<br><br>"
        "<b>The gap between the two columns is the actual message:</b><br><br>"
        "High coverage, low similarity &rarr; the short track sits entirely "
        "inside the long one, but the long one holds far more material. "
        "Classic for an extended mix versus the original, or a track inside a "
        "set.<br><br>"
        "Both high &rarr; the files are practically the same thing.<br><br>"
        "Both low &rarr; little in common; if the row still sits in a group, "
        "it got there via artist and title.",

    "help.col.file_a":
        "<b>File A</b><br><br>"
        "First file of the pair. Selecting a row shows its details below.",
    "help.col.file_b": "<b>File B</b><br><br>Second file of the pair.",
    "help.col.group":
        "<b>Group</b><br><br>"
        "Number of the duplicate group from the first tab. A group of four "
        "files produces six pairs here.",

    "help.col.club":
        "<b>Club rating (0–100)</b><br><br>"
        "How well the file holds up on a big system. Deliberately something "
        "different from the quality score in the first tab.<br><br>"
        "What matters is almost exclusively the <b>measured bandwidth</b> – on "
        "a club rig you hear immediately that a 128 kbps MP3 has nothing left "
        "at the top. Plus a small bonus for genuinely lossless, and clear "
        "penalties for mono and for sample rates below 44.1 kHz.<br><br>"
        "<b>Clipping is only penalised above 5 %.</b> A few percent are baked "
        "into the master of modern club tracks and do not make the file "
        "unusable – which is why the penalty is far milder here than in the "
        "general quality score.",

    "help.col.rating":
        "<b>Verdict</b><br><br>"
        "&nbsp;&nbsp;<b>Very good</b> &nbsp;from 88 – lossless or full "
        "bandwidth<br>"
        "&nbsp;&nbsp;<b>Good</b> &nbsp;from 70 – roughly 256 kbps upwards<br>"
        "&nbsp;&nbsp;<b>Usable</b> &nbsp;from 50 – around 192 kbps<br>"
        "&nbsp;&nbsp;<b>At a pinch</b> &nbsp;from 30 – around 128 kbps, "
        "audibly dull<br>"
        "&nbsp;&nbsp;<b>Unsuitable</b> &nbsp;below that – embarrassing on a "
        "big system<br><br>"
        "The drop-downs above filter specifically, for example to everything "
        "below &ldquo;Good&rdquo;.",

    "help.col.samplerate":
        "<b>Sample rate</b><br><br>"
        "Sampling rate of the stream. 44.1 kHz is the CD standard and "
        "perfectly sufficient.<br><br>"
        "Below 44.1 kHz the bandwidth is hard-limited and gets penalised. "
        "Above 48 kHz brings nothing audible – and if there is nothing above "
        "21 kHz, it shows up as &ldquo;Hi-res without content&rdquo; in the "
        "findings.",

    "help.col.channels":
        "<b>Channels</b><br><br>"
        "Mono stands out immediately on a stereo rig and is penalised "
        "considerably.",

    "help.audio_threshold":
        "<b>Acoustic match</b><br><br>"
        "From what percentage two tracks count as the same recording.<br><br>"
        "What is measured is how much of the <b>shorter</b> track sits inside "
        "the longer one. The audio itself is compared, not the labelling – "
        "which is why it works across formats and bit rates.<br><br>"
        "<b>90 %</b> is the default: strict, and finds essentially only real "
        "duplicates.<br><br>"
        "Shortened versions and tracks with a longer lead-in are already found "
        "at the default: both tracks are aligned in time before they are "
        "compared.<br><br>"
        "<b>Lower</b> (70–85 %) additionally finds versions that only match "
        "over long stretches – an extended mix that inserts bars in the middle, "
        "say, or a clearly different master.<br>"
        "<b>Lower still</b> (50–60 %) also finds distant relatives – but you "
        "will have to check considerably more by hand.<br><br>"
        "After a change, <b>Regroup</b> is enough. It takes seconds, because "
        "nothing is decoded again.",

    "help.meta_threshold":
        "<b>Name similarity</b><br><br>"
        "From what percentage two tracks belong together by artist and title – "
        "regardless of how they sound.<br><br>"
        "This finds other versions of the same song: remix, live, radio edit, "
        "a different master. Such matches are inherently uncertain and are "
        "therefore shown separately as "
        "<span style='color:#b8860b'><b>Name 96 %</b></span>.<br><br>"
        "Additions in brackets such as &ldquo;(Official Video)&rdquo; or "
        "&ldquo;(Zeds Dead Remix)&rdquo;, and appended ones such as "
        "&ldquo;- Remastered 2011&rdquo;, are stripped before comparing – "
        "that is how an original and its remix find each other. Different "
        "numbers in the title (&ldquo;Track 1&rdquo; / &ldquo;Track 2&rdquo;) "
        "count as different pieces.<br><br>"
        "If neither side has an artist, the titles have to be near-identical – "
        "otherwise file names like &ldquo;Track 01&rdquo; would connect "
        "everything with everything.<br><br>"
        "<b>Go down to 60–70 %</b> only if your tags are poorly maintained. "
        "Expect false matches then.",

    "help.detection":
        "<b>How comparison works</b><br><br>"
        "Every file is decoded once. The comparison then runs in two stages:"
        "<br><br>"
        "<b>1. Candidate search.</b> Prominent points are picked from the "
        "spectrum and linked in pairs. An index uses these to fish the few "
        "suspects out of thousands of files in milliseconds.<br><br>"
        "<b>2. Verification.</b> Only those candidates are compared densely – "
        "aligned in time against each other and then checked piece by piece. "
        "Only this number appears in the Match column.<br><br>"
        "The second stage is why the percentage is worth anything: a trimmed "
        "track can drop to 20 % in stage 1 even though it is the same "
        "recording. Stage 2 does not have that problem.<br><br>"
        "<b>MusicDupes changes and deletes nothing.</b>",

    "help.recommendation":
        "<b>Which file to keep?</b><br><br>"
        "The entry marked with <b>*</b> and highlighted green is the "
        "suggestion. It is decided in this order:<br><br>"
        "1. <b>Measured bandwidth</b> – the one figure that cannot lie<br>"
        "2. <b>Genuinely lossless</b> – a suspected transcode does not count "
        "as lossless here<br>"
        "3. Quality score<br>"
        "4. Length, then bit rate, then size<br><br>"
        "Bandwidth deliberately comes first: otherwise a FLAC made from an MP3 "
        "would beat its own original purely on format and file size.",

    "help.tab_pairs":
        "<b>Pair comparison</b><br><br>"
        "Every file pair of a group on its own – with both readings of the "
        "same comparison side by side.<br><br>"
        "<b>Coverage</b> measures against the shorter track: &ldquo;how much "
        "of it sits inside the longer one?&rdquo;<br>"
        "<b>Similarity</b> measures against the longer one: &ldquo;how much do "
        "the files resemble each other overall?&rdquo;<br><br>"
        "Example: an original of 3:51 against its extended mix of 6:32. The "
        "original sits almost entirely inside the extended version – coverage "
        "is high. As files the two still only match halfway, because the "
        "extended version holds a lot of material the original does not. "
        "Similarity comes out correspondingly lower.<br><br>"
        "Coverage is what finds duplicates; similarity is what judges them."
        "<br><br>"
        "Every column sorts by clicking its heading.",

    "help.tab_quality":
        "<b>File quality</b><br><br>"
        "All files read in, whether or not they are duplicates.<br><br>"
        "The bar shows suitability for a big system: from <span "
        "style='color:#c85032'>red</span> (unsuitable) to <span "
        "style='color:#50b050'>green</span> (very good). What counts is the "
        "bandwidth <b>measured</b> from the audio, not the format and not the "
        "file size.<br><br>"
        "Sort by <b>Club rating</b> to pull the weak files to the top, or by "
        "<b>Format</b> to see all MP3s together. The drop-downs filter "
        "additionally by format and verdict.<br><br>"
        "Watch out for <span style='color:#c0392b'><b>Suspected transcode</b>"
        "</span>: those files look lossless but sound like the MP3 they were "
        "made from.",

    "help.dialog": """\
MusicDupes compares the SOUND, not the tags.

Every file is decoded once. Two things come out of that:

1. A fingerprint made of prominent points in the spectrum. It is used to fish
   the few suspects out of thousands of files quickly.
2. A dense sound profile. Only this decides the percentage. Both tracks are
   aligned in time against each other first - which is why a duplicate is
   recognised even when it is trimmed or has a longer lead-in.

The percentage in the Duplicates tab means: this much of the SHORTER track
sits inside the longer one. So 100 % at different lengths means "fully
contained". The Pair comparison tab adds the similarity next to it, which
measures against the longer track and therefore says how much the files
resemble each other overall.

Match types, from certain to uncertain:

  Identical file        Byte for byte the same file.
  Identical audio       Same sound, only different tags.
  Same recording        Different format or different bit rate.
  Same title            Only the labelling matches - most likely a different
                        version (remix, live, radio edit). Please check these
                        yourself.

WHICH FILE IS THE BETTER ONE?

The entry marked with * and highlighted green is the suggestion. More telling
than the bit rate is the "Bandwidth" column: it is MEASURED from the audio,
not read from the tags.

  approx. 15-16 kHz   corresponds to roughly 96-128 kbps
  approx. 19-20 kHz   corresponds to roughly 256-320 kbps
  above 20 kHz        lossless or a very high bit rate

If a FLAC or WAV says "Suspected transcode", its audio ends far below 20 kHz.
It was almost certainly made from an MP3: it occupies the space of a lossless
file but sounds like the MP3 it came from. In that case the big file is the
worse one.

MusicDupes changes and deletes nothing. It only shows.""",
}

DE.update(_DE)
EN.update(_EN)
