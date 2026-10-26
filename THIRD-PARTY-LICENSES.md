# Third-party components

MusicDupes itself is released under the **MIT License** (see `LICENSE`).

The source code pulls in the libraries listed below. The distributed
*portable package* additionally contains Python, Qt and ffmpeg as binaries.
This file documents what is included and under which terms.

---

## Runtime dependencies (source and portable package)

| Component | Version | Licence | Notes |
|---|---|---|---|
| [Python](https://www.python.org/) | 3.14 | PSF License 2.0 | Permissive, GPL-compatible |
| [NumPy](https://numpy.org/) | 2.x | BSD-3-Clause (plus 0BSD, MIT, Zlib, CC0 for bundled parts) | Permissive |
| [PySide6 / Qt](https://www.qt.io/qt-for-python) | 6.11 | **LGPL-3.0** (Qt is also available commercially) | See note below |
| [FFmpeg](https://ffmpeg.org/) | `win64-lgpl-shared` | **LGPL-3.0** (built with `--enable-version3`, without `--enable-gpl`) | See note below |

## Build tool

| Component | Licence | Notes |
|---|---|---|
| [PyInstaller](https://pyinstaller.org/) | GPL-2.0-or-later **with bootloader exception** | Only its small start-up program (the bootloader) ends up inside `MusicDupes.exe`. The exception explicitly permits distributing it as part of programs under any licence. PyInstaller imposes no licence on MusicDupes. |

---

## Note on Qt / PySide6 (LGPL-3.0)

The LGPL requires that users can replace the LGPL library with their own
version. MusicDupes is released in two forms, and both allow this:

* **Portable ZIP (folder):** Qt ships as **separate, unmodified DLL files**
  under `_internal\`, not statically linked into the executable. They can be
  replaced with API-compatible builds directly. This form exists precisely
  so that replacing them stays a matter of swapping files.
* **Single `MusicDupes.exe`:** contains the very same unmodified DLLs in an
  archive that is unpacked into a temporary folder at every start and loaded
  from there. To use a different Qt build, take the portable ZIP, or rebuild
  the executable from this repository's source with `build_portable.py`.
* Qt is not modified in any way.

The LGPL-3.0 builds on the GPL-3.0, and both texts have to accompany the
program. They are included as `licenses\LGPL-3.0.txt` and
`licenses\GPL-3.0.txt` - next to the executable in the ZIP, and inside the
single file, from where *Help → Licences* opens or saves them. Qt sources
are available from <https://download.qt.io/>.

## Note on FFmpeg (LGPL)

MusicDupes **only decodes** audio; it never encodes. The GPL-only parts of
FFmpeg (x264, x265, Xvid, frei0r and similar encoders and filters) are not
needed, so the package deliberately ships an **LGPL build** rather than the
more common GPL build.

* FFmpeg is called as a **separate process**, not linked as a library.
* It ships as unmodified binaries plus their DLLs under `ffmpeg\`, and can be
  replaced with any other compatible FFmpeg build (in the single file, they
  are unpacked into the temporary folder at every start).
* The licence text is included at `ffmpeg\LICENSE.txt` in the package, the
  GPL-3.0 it refers to at `licenses\GPL-3.0.txt`.

FFmpeg sources: <https://ffmpeg.org/download.html>.
The Windows builds come from <https://github.com/BtbN/FFmpeg-Builds>
(`win64-lgpl-shared`). The exact archive used, together with its SHA-256
checksum, is recorded in `ffmpeg\ORIGIN.txt` inside the package.

> If you build the package yourself with a GPL FFmpeg build, the resulting
> package as a whole falls under the GPL. The build script warns about this.

---

## What is *not* included

* **[mutagen](https://mutagen.readthedocs.io/)** (GPL-2.0-or-later) was used
  for tag reading in earlier versions. It was removed so that MusicDupes can
  be released under a permissive licence. Tags are read through `ffprobe`
  instead.

---

## Attribution

This software uses libraries from the FFmpeg project under the LGPLv3 and Qt
under the LGPLv3. Neither project endorses MusicDupes.
