MusicDupes
==========

Finds duplicate music files by the way they SOUND - not by their tags.
Recognises the same track across formats and bit rates, and shows which of
the copies is the better one.


GETTING STARTED
---------------

1. Extract this folder somewhere.
2. Double-click MusicDupes.exe.
3. Pick the folder holding your music, press "Start scan".

No installation, no Python, no ffmpeg needed - everything is in here. It also
runs from a USB stick.

IMPORTANT - these two points save you trouble:

1. Unblock the ZIP BEFORE extracting.
   Right-click the ZIP file -> Properties -> tick "Unblock" at the bottom
   -> OK. Only then extract it.

   Windows marks downloaded files, and that mark carries over to every
   single file when you extract. Unblocking first usually keeps the
   SmartScreen warning away.

2. Extract first, then start.
   Launching the EXE straight out of the ZIP leaves it without everything
   else and it will not run.

The language follows your Windows setting: German on a German system, English
everywhere else. You can override it under the "Language" menu.

If "Windows protected your PC" still shows up: it does not mean anything was
found in the file. Windows shows that dialog for programs it has not seen
often yet. Continue with "More info" -> "Run anyway". Every release ships a
SHA-256 checksum so you can verify your download.

MusicDupes CHANGES AND DELETES NOTHING. It only shows. Deleting is up to you,
in Explorer.


THE THREE TABS
--------------

Duplicates       The groups found. The entry marked with * and highlighted
                 green is the one suggested for keeping. "Same title,
                 different recording" means another version (remix, live,
                 radio edit) - please check those yourself.

Pair comparison  Every file pair on its own, with two numbers:
                 "Coverage" measures against the shorter track, "Similarity"
                 against the longer one. An original of 3:51 inside its
                 extended mix of 6:32 has high coverage but only medium
                 similarity - it sits entirely inside, the extended version
                 simply holds much more.

File quality     All files with a bar from red to green: suitability for a
                 big system. Sortable by every column, filterable by format
                 and verdict.


THE MOST IMPORTANT POINT
------------------------

The "Bandwidth" column is MEASURED from the audio, not read from the tags:

  15-16 kHz    corresponds to roughly  96-128 kbps
  19-20 kHz    corresponds to roughly 256-320 kbps
  above 20 kHz                        lossless or a very high bit rate

If a FLAC or WAV says "Suspected transcode", it was almost certainly made
from an MP3. It occupies the space of a lossless file and still sounds like
the MP3 it came from. In that case the BIGGER file is the worse one -
something neither the extension nor the file size will tell you.


WHERE TO FIND WHAT
------------------

Hover any column heading and it explains itself. The same goes for the match
type on each row. The small (i) symbols explain the two sliders and the
method behind the detection.

More detail: menu "Help" -> "How detection works".


THE data FOLDER
---------------

Created next to the EXE on first launch. It holds the stored analyses and
your settings, which is why every later scan takes only a fraction of the
time.

It sits here on purpose rather than somewhere in your user profile, so that
copying the folder takes everything along. Deleting it is harmless - the next
scan will simply take as long as the first one did.

If the folder sits somewhere Windows does not allow writing (under "Program
Files", for instance), data goes to %LOCALAPPDATA%\MusicDupes instead.


LICENCES
--------

MusicDupes itself is released under the MIT licence (LICENSE).

The package also contains Qt and ffmpeg (https://ffmpeg.org), both under the
GNU Lesser General Public License v3. They ship unmodified as separate files
and may be replaced with other compatible builds. The licence texts are in
the licenses folder (LGPL-3.0 and the GPL-3.0 it builds on) and in
ffmpeg\LICENSE.txt; they have to be included whenever this package is passed
on. Details: THIRD-PARTY-LICENSES.md. The source code of ffmpeg is available
at https://ffmpeg.org/download.html.

MusicDupes itself only calls ffmpeg as a separate program.
