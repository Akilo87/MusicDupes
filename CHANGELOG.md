# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [1.1.0] — 2026-10-26

First public release.

### Fixed in the pre-release audit
* **Shifted and trimmed copies scored too low.** Both profiles sit on a
  fixed grid from the start of the file; a copy shifted by half a grid step
  dropped from 100 % to 79 % and fell below the 90 % default. The comparison
  now also checks half-step offsets. Test set: a copy with 6 s of extra
  lead-in went from 79 % to 99 %, the strongest false match stayed at 0.4 %.
  On a real 2,059-track library every existing group and every keep
  suggestion stayed the same; two radio edits are now correctly "same
  recording", and two missed pairs are found.
* **Grouping took minutes.** The candidate search sorted over a million
  intermediate hits per track. A pre-filter that provably cannot change the
  result (verified identical on all 2,059 tracks) plus parallel queries cut
  a rescan of that library from about 4 minutes to 28 s. *Regroup* reuses
  the candidates and takes about 5 s.
* **Very short files crashed the analysis** and showed up as unreadable
  (the peak finder returned two values instead of three).
* **Other versions counted as duplicates.** Remixes and live versions in a
  group were included in "duplicates" and "redundantly occupied", and the
  keeper tooltip called them expendable. They are now counted separately as
  "other versions".
* **English users saw German error messages**, because the worker processes
  never learned the language. Errors are now stored as keys like everything
  else.
* **Picking the same folder twice could re-analyse everything.** The folder
  dialog returns `V:/Music`, typed it is `V:\Music` — two different cache
  keys. Paths are now normalised, and existing caches are converted once
  instead of being re-read.
* **Closing the window during a scan** waited at most 3 s and then shut the
  program down with the background thread still running. It now cancels the
  run and closes once it has stopped. *Regroup* can now be cancelled.
* Name matching: "Stay With Me" no longer shrinks to "Stay", "Love -
  Delivered" no longer loses its second word, "- Remastered 2011" is
  stripped, and titles with different numbers ("Track 1" / "Track 2") no
  longer match.
* The text filter now also applies to the pair tab; double-click opens
  Explorer in every tab; the file quality summary no longer keeps a stale
  count after the filter is cleared.
* Explorer is started by its full path, so a planted `explorer.exe` in the
  download folder cannot be picked up. A corrupted settings file no longer
  prevents the start. Tag text in the detail heading is shown as plain text.

### Release and packaging fixes
* **The release workflow would not have run**: GitHub removed Node 20 on
  23 September 2026, and the actions were still on Node 20 versions. All
  actions updated to their Node 24 releases.
* **The smoke test checked nothing**: PowerShell does not wait for windowed
  programs, so the test looked for the result before the scan had started.
  It now waits, tests both executables and checks that a duplicate group
  comes out. Publishing runs in its own job, the only one with write access.
* **The build could pack private data**: `--zip-only` (the signing step) and
  the MSIX build copied a `data\` folder left by a test run — cache and
  settings with every path of the local music collection. Excluded now.
* **Licence texts:** the LGPL-3.0 requires the GPL-3.0 text alongside; both
  are now shipped in `licenses\`. The in-package guides called FFmpeg "GPL";
  it is LGPL.
* Both executables now carry product name and version (required by SignPath).
* Releases are built with Python 3.14 and pinned package versions
  (`requirements-build.txt`), the same as local builds.
* README, guides and release notes no longer claim the releases are signed
  before SignPath has approved the project.

### Added
* **Single-file build.** `MusicDupes.exe` is one 125 MB file: download,
  double-click, done — no extraction step at all. Measured against the
  folder version: 1.5 s to the window instead of 0.3 s, temporary files
  cleaned up on exit, worker processes and the bundled FFmpeg both work.
  The folder version stays available; it starts faster and keeps the LGPL
  libraries replaceable as individual files.
* **Code signing via SignPath Foundation prepared**, which signs open source
  projects free of charge. The signature would be applied inside the public
  build workflow from the tagged source; the private key stays in SignPath's
  hardware module. Their certificate is shared across many projects and
  therefore already carries SmartScreen reputation, which a freshly bought
  certificate would not. Active once the project is approved — see
  `docs/code-signing-policy.md`.
* **Microsoft Store packaging** (`packaging/`). Store-published packages are
  signed by Microsoft after certification, which is the only distribution
  route Microsoft lists as having no SmartScreen prompt. Registration for
  individual developers is free. The portable ZIP stays available alongside.
* **Application icon.** The executable previously carried the default
  PyInstaller icon, which does nothing for trust. Generated reproducibly
  from `tools/make_icon.py`, including the Store tile sizes.
* **English as a second language**, selected automatically from the Windows
  display language (German for DE/AT/CH, English everywhere else) and
  overridable under *Language*. CLI: `--lang de|en|auto`.
* **Pair comparison tab** — every file pair with both readings of the same
  measurement side by side: *coverage* (against the shorter track) and
  *similarity* (against the longer one).
* **File quality tab** — all files with a red-to-green club suitability bar,
  sortable by every column, filterable by format and verdict.
* Explanations throughout: every column heading, every match type and every
  finding explains itself on hover; ⓘ symbols cover the sliders and the
  method.
* Unreadable files are now listed instead of silently skipped.
* Portable package with bundled Python, Qt and FFmpeg — no installation.
* SHA-256 checksum generated for every build.

### Changed
* **Default acoustic threshold raised from 55 % to 90 %.** Strict by default;
  lowering it afterwards costs one click on *Regroup*.
* **Licensed under MIT.** `mutagen` (GPL-2.0) was removed and the package now
  ships an **LGPL** FFmpeg build instead of a GPL one. Verified on a
  2,059-file library: the comparison name derived from `ffprobe` tags is
  identical to the one `mutagen` produced for every single file, so grouping
  is unchanged.
* Quality findings and error messages are stored as language-neutral keys
  rather than German text, so the same files are judged identically in both
  languages. This raises the cache schema version — the first scan after
  updating re-reads the collection once.
* Cache and settings live next to the executable (`data\`), not in the user
  profile or the registry, so copying the folder takes everything along. If
  that location is not writable — a Store install, or the folder placed
  under `Program Files` — everything moves to `%LOCALAPPDATA%\MusicDupes`
  instead.

### Fixed
* **The taskbar showed a placeholder icon instead of the application icon.**
  The `icon=` setting in the PyInstaller spec only gives the *file* its icon
  in Explorer. The taskbar, the title bar and Alt-Tab use the *window* icon,
  which Qt never received — so it fell back to its own placeholder. The icon
  file is now shipped with both builds and applied via `setWindowIcon()`, and
  the process declares an explicit AppUserModelID so Windows groups the
  window under the application rather than under whatever launched it.
* **The keep recommendation could prefer a lossy file over a FLAC.** A high
  bit rate counted as much as lossless, and the clipping penalty hit only the
  FLAC — which loudly mastered club tracks collect almost every time. The
  decision is now staged: measured bandwidth, then genuinely lossless, then
  the score, then length, bit rate and size.
* **The keep suggestion was labelled "Identical file"**, which read as if a
  byte-identical copy existed. It is now "Reference".
* **Name-based matches showed a plain percentage** in the same column as
  acoustic matches, so a remix could read as "100 %". Those are now shown
  separately as `Name 96 %` in amber, with the acoustic value in the tooltip.
* **A single wrong name match could merge two unrelated songs.** Name edges
  no longer chain: they only connect finished acoustic groups, and every
  further group has to match the *seed* group, not just a neighbour.
* **Trimmed duplicates were missed.** A cut half a frame off the analysis
  grid dropped the same recording from 99 % to 20 %. The dense verification
  stage removes that dependency entirely — the same case now scores 97.9 %.
* `.eac3`, `.mp4` and `.webm` added to the recognised extensions.
