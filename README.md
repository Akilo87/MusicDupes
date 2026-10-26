# MusicDupes

**Finds duplicate music files by the way they sound — not by their tags.**

Recognises the same recording across formats and bit rates, measures what is
actually in each file, and tells you which copy is the better one.

MusicDupes **changes and deletes nothing**. It is a viewer. Deleting stays
your decision, in Explorer.

[Deutsche Version dieser Seite](README.de.md) · Windows · MIT licence

![The file quality tab](docs/img/quality-tab.png)

---

## Why another duplicate finder

Most tools compare file names, tags, or byte-for-byte hashes. That misses the
same track saved as FLAC and as MP3, and it cannot tell you which of two
copies is worth keeping.

MusicDupes does two things differently.

**It compares the audio.** Every file is decoded once and reduced to an
acoustic fingerprint, so a 320 kbps MP3 and its FLAC original are recognised
as the same recording even with completely different tags.

**It measures quality instead of reading it.** The *Bandwidth* column is
derived from the audio signal, not from the tags. That exposes something no
tag can tell you: a FLAC that was created from an MP3. It occupies the space
of a lossless file and still sounds like the MP3 it came from — and in that
case the **bigger** file is the worse one.

|  | |
|---|---|
| 15–16 kHz | roughly 96–128 kbps |
| 19–20 kHz | roughly 256–320 kbps |
| above 20 kHz | lossless or a very high bit rate |

---

## Getting started

### Single file — download and run (recommended)

1. Download **`MusicDupes.exe`** from [Releases](../../releases/latest).
2. Double-click it.

That is the whole procedure. One file, about 125 MB, no installation, no
extraction, no Python, no FFmpeg — everything is inside. It runs from a USB
stick too.

Each start takes about a second longer than the folder version below,
because the program unpacks itself into a temporary folder; that folder is
removed again when you close it. Its own data — the analysis cache and your
settings — goes into a `data` folder next to the file.

### Portable folder — slightly faster, libraries replaceable

Download `MusicDupes-Portable.zip`, **unblock it first** (right-click →
Properties → *Unblock*), extract it, and run `MusicDupes.exe` from the
folder. Starts in about 0.3 seconds instead of 1.5.

This is also the build to take if you want to swap out the bundled Qt or
FFmpeg libraries, which the LGPL entitles you to — in the folder version
they are ordinary files you can replace.

### Microsoft Store — planned

A Store version is prepared (`packaging/`) and will be linked here once the
listing is live. Store packages are signed by Microsoft, so Windows shows no
warning for them at all.

### Language

The language follows your Windows setting: German on a German system,
English everywhere else. Override it under *Language*.

### Is it safe? Why Windows may warn you

Windows may show **"Windows protected your PC"** the first time. That does
not mean anything was found in the file — Windows shows the dialog for
programs it has not seen often yet. Click *More info → Run anyway*.

Every release is built by GitHub Actions from the tagged source in this
repository, and ships SHA-256 checksums so you can verify your download.

MusicDupes has **no network access at all** and never modifies or deletes a
file — see the [privacy policy](docs/privacy.md).

### Code signing policy

Code signing through [SignPath Foundation](https://signpath.org/), which
signs open source projects free of charge, has been prepared in the release
workflow. Once the project is approved, releases are signed there — the
private key never leaves SignPath's hardware module — and carry the note
*Free code signing provided by [SignPath.io](https://about.signpath.io/),
certificate by [SignPath Foundation](https://signpath.org/)*. Details:
[code signing policy](docs/code-signing-policy.md).

---

## The three tabs

### Duplicates

Groups of files that belong together. The entry marked `*` and highlighted
green is the suggestion for keeping.

Match types, from certain to uncertain:

| Type | What was actually checked |
|---|---|
| Identical file | Byte for byte the same file |
| Identical audio, different tags | Decoded audio identical, only the tags differ |
| Same recording | Same audio, re-encoded: other format, bit rate, rip or edit |
| Same title, different recording | Only artist and title match — usually a remix, live or radio edit |

The last type is the uncertain one. It is shown as `Name 96 %` in amber
rather than as a plain percentage, because acoustically those files often
have nothing in common. Such files are not counted as duplicates either, nor
towards the space shown as "redundantly occupied".

### Pair comparison

![The pair comparison tab](docs/img/pair-tab.png)

The same measurement, read two ways:

* **Coverage** divides by the **shorter** track: *how much of it sits inside
  the longer one?*
* **Similarity** divides by the **longer** track: *how much do the files
  resemble each other overall?*

An original of 3:51 against its extended mix of 6:32 has high coverage but
only medium similarity. The original sits almost entirely inside the extended
version; the extended version simply holds a lot more.

Coverage is what finds duplicates. Similarity is what judges them.

### File quality

Every file read in, whether duplicated or not, with a red-to-green bar for
suitability on a large PA system. Sortable by any column, filterable by
format and verdict.

| Verdict | from | corresponds to |
|---|---|---|
| Very good | 88 | lossless or full bandwidth |
| Good | 70 | 256 kbps upwards |
| Usable | 50 | around 192 kbps |
| At a pinch | 30 | around 128 kbps, audibly dull |
| Unsuitable | – | embarrassing on a big system |

---

## How detection works

Each file is decoded **once**. Fingerprint and quality data come out of the
same spectrogram — decoding twice would halve the speed.

The comparison then runs in two stages.

**1. Candidate search.** Prominent points are picked from the spectrum and
linked in pairs into hashes (a constellation fingerprint). An inverted index
uses those to find the few suspects among thousands of files without
comparing every file with every other.

**2. Verification.** Only the candidates are compared densely: a narrow band
profile (16 bands, ~21 frames/s), aligned in time by cross-correlation and
then checked frame by frame — at whole and at half-frame offsets, so that a
file cut or shifted by a fraction of a frame still lines up. Only this
number reaches the interface.

The second stage is not optional — it is the reason the percentage is worth
anything. The stage-1 hit count depends heavily on where a file happens to
fall on the analysis grid: a cut that is half a frame off drops the same
recording from 99 % to 20 %. The dense comparison does not have that problem.

Measured on a test set — one recording as WAV, FLAC, MP3 96/128/256/320, OGG,
AAC, a FLAC made from an MP3, a trimmed copy, a copy trimmed off the
analysis grid and a copy with 6 s of extra lead-in, plus a second recording
and two unrelated tracks:

* every copy against the suggested keeper: **97.6 % or more**
* weakest pair (two differently trimmed copies against each other): **85.4 %**
* strongest false match: **0.4 %**

> **Honest caveat:** that false-positive figure comes from a small test set.
> A real collection contains things it does not — tracks from one album
> sharing a drum loop, the same sample in two songs, classical repertoire in
> several recordings. Expect the margin to be narrower on real material. The
> default threshold is set to a strict 90 % for that reason.

### Which file to keep

Decided in this order — deliberately not by a single score:

1. **Measured bandwidth** (in 2 kHz steps) — the one figure that cannot lie
2. **Genuinely lossless** — a suspected transcode does not count as lossless
3. Quality score
4. Length, then bit rate, then size

Bandwidth comes first because otherwise a FLAC made from an MP3 would beat
its own original on format and file size alone. The score is not first
because clipping penalties — which loudly mastered club tracks collect almost
every time — would otherwise push a lossy file ahead of a FLAC.

---

## Why CPU and not the GPU

The work is almost entirely audio decoding (FFmpeg) and many small FFTs:
serial, branchy, memory-bound. That is the opposite of what a GPU is fast at;
the data would still be travelling across PCIe by the time the CPU had
finished.

A 16-thread CPU saturates reliably, after which the disk is the limit. For
scale: roughly **2,000 tracks in a few minutes** on the first run. Later runs
take about half a minute (2,059 tracks: 28 s), because every analysis is
cached in `data\cache.db`; *Regroup* after moving a slider takes about five
seconds.

---

## Supported formats

Whatever the bundled FFmpeg can decode: MP3, FLAC, WAV, M4A/AAC, ALAC,
OGG/Vorbis, Opus, WMA, AIFF, APE, WavPack, Musepack, DSF, TTA, AC3/EAC3 and
more.

---

## Building from source

Requires Python 3.10+ on Windows (releases are built with Python 3.14 and the
exact package versions in `requirements-build.txt`).

```
setup.bat
```

Then place a `win64-lgpl-shared` FFmpeg build from
[BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) into
`ffmpeg\` (the contents of its `bin\` folder), and run:

```
build-portable.bat
```

That produces both deliveries — `dist-single\MusicDupes.exe` and
`dist\MusicDupes\` packed as `MusicDupes-Portable.zip` — each with a SHA-256
checksum. The build script warns if the FFmpeg build it finds is GPL — see
the licensing section.

Run without building: `MusicDupes.bat`, or on the command line:

```
MusicDupes-Konsole.bat --cli "D:\Music" --csv result.csv --lang en
```

The same switches work with the released `MusicDupes.exe`. Being a windowed
program it prints nothing, though — use `--csv` to get the result.

---

## Licensing

MusicDupes is **MIT licensed** — see [LICENSE](LICENSE).

Both deliveries additionally contain Python (PSF), NumPy (BSD),
Qt/PySide6 (**LGPL-3.0**) and FFmpeg (**LGPL-3.0**), unmodified. In the
portable ZIP the LGPL components are separate, replaceable files, which is
what the LGPL asks for; the licence texts (including the GPL-3.0 the LGPL
builds on) are in `licenses\`. Details and attributions:
[THIRD-PARTY-LICENSES.md](THIRD-PARTY-LICENSES.md).

The FFmpeg build is deliberately **LGPL, not GPL**: MusicDupes only decodes,
so the GPL-only encoders (x264, x265, Xvid) are not needed. Building the
package with a GPL FFmpeg would place the whole package under the GPL.

PyInstaller is GPL-2.0 **with a bootloader exception** that explicitly allows
distributing the built program under any licence, so it imposes nothing here.

---

## Known limitations

* **Windows only.** The engine is portable Python, but the packaging,
  `explorer /select` and the FFmpeg bundling are Windows-specific.
* **The false-positive rate has not been measured on a large real corpus** —
  see the caveat above.
* Tracks shorter than about one second are not identified; there is too
  little to compare.
* Files longer than 20 minutes are analysed up to that point. More than
  enough for identification, and it bounds memory per worker.
* The comparison assumes **one constant time offset** between two files. A
  prepended intro is handled; extra bars inserted in the middle are not, and
  everything after them stops matching.

## Contributing

Issues and pull requests are welcome. There are no tests worth the name yet —
that is the most useful place to start.
