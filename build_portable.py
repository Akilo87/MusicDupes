"""Builds both deliveries: the folder in dist/MusicDupes (zipped) and the
single MusicDupes.exe in dist-single.

Five steps:

1. PyInstaller bundles Python, Qt and the program code into the folder.
2. FFmpeg is copied in *afterwards* - deliberately not handed to PyInstaller.
3. Guides and licence texts are placed next to the executable.
4. The single-file version is built from the same files.
5. The folder is zipped; SHA-256 checksums are written next to both.

Why step 2 is separate: if the FFmpeg DLLs are passed to PyInstaller as
``datas``, it classifies them as binaries, follows their dependencies and
drops a second copy into the main folder. That inflates the package by about
160 MB without a single one of those copies ever being used.

Run with:   .venv\\Scripts\\python.exe build_portable.py
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist", "MusicDupes")
ZIP_PATH = os.path.join(ROOT, "MusicDupes-Portable.zip")
# Zweite Auslieferungsform: eine einzelne EXE zum Herunterladen und Starten.
SINGLE_DIST = os.path.join(ROOT, "dist-single")
SINGLE_EXE = os.path.join(SINGLE_DIST, "MusicDupes.exe")

# The project-local copy comes first: it is the build that gets shipped and
# the one whose licence the package documents.
FFMPEG_CANDIDATES = [
    os.path.join(ROOT, "ffmpeg"),
    r"C:\Program Files\ffmpeg\bin",
    r"C:\Program Files (x86)\ffmpeg\bin",
    r"C:\ffmpeg\bin",
]
# ffplay only plays audio back - MusicDupes never needs it, and leaving it
# out saves about 34 MB.
SKIP_PREFIXES = ("ffplay",)

# User-facing guides in both languages. README.md targets developers and
# would only confuse people inside the package.
BESIDE_EXE = ("LIESMICH.txt", "README.txt", "LICENSE", "THIRD-PARTY-LICENSES.md")
# The LGPL-3.0 has to be accompanied by its own text and by the GPL-3.0.
LICENCE_DIR = "licenses"
LICENCE_TEXTS = ("LGPL-3.0.txt", "GPL-3.0.txt")

# Created by the program itself next to the EXE: cache and settings of a
# test run, including every path of the local music collection. Never part
# of a package that gets passed on.
PRIVATE_DIRS = ("data",)


def find_ffmpeg_dir() -> str:
    for folder in FFMPEG_CANDIDATES:
        if os.path.isfile(os.path.join(folder, "ffmpeg.exe")):
            return folder
    found = shutil.which("ffmpeg")
    if found:
        return os.path.dirname(found)
    raise SystemExit(
        "FFmpeg not found. Download a win64-lgpl-shared build from\n"
        "  https://github.com/BtbN/FFmpeg-Builds/releases\n"
        "and unpack its bin/ contents into:  " + os.path.join(ROOT, "ffmpeg")
    )


def check_ffmpeg_licence(folder: str) -> str:
    """Reads the build flags. A GPL build changes the licence of the package.

    MusicDupes itself is MIT, but a package containing GPL binaries falls
    under the GPL as a whole. Since we only ever decode, an LGPL build is
    enough - so this is worth catching before a release goes out.
    """
    exe = os.path.join(folder, "ffmpeg.exe")
    try:
        proc = subprocess.run(
            [exe, "-version"], capture_output=True, timeout=60, text=True,
            errors="replace",
        )
    except Exception as exc:  # noqa: BLE001
        print("     WARNING: could not read the FFmpeg version ({})".format(exc))
        return "unknown"

    banner = (proc.stdout or "") + (proc.stderr or "")
    if "--enable-nonfree" in banner:
        return "nonfree"
    if "--enable-gpl" in banner:
        return "gpl"
    return "lgpl3" if "--enable-version3" in banner else "lgpl2.1"


def human(num_bytes: float) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return "{:.1f} {}".format(value, unit)
        value /= 1024
    return "{:.1f} GB".format(value)


def folder_size(path: str) -> int:
    total = 0
    for folder, _dirs, names in os.walk(path):
        for name in names:
            try:
                total += os.path.getsize(os.path.join(folder, name))
            except OSError:
                pass
    return total


def write_checksum(path: str) -> str:
    """Legt <datei>.sha256 daneben, damit Downloads pruefbar sind."""
    digest = sha256_of(path)
    with open(path + ".sha256", "w", encoding="utf-8") as handle:
        handle.write("{}  {}\n".format(digest, os.path.basename(path)))
    return digest


def build_single(pyinstaller: str) -> None:
    """Baut die Einzeldatei-Fassung aus demselben Quellstand.

    FFmpeg kommt aus dem schon fertig bestueckten ``dist/MusicDupes/ffmpeg``:
    dort ist bereits aussortiert, und die Lizenz liegt sicher dabei - egal,
    wo auf dem Rechner das FFmpeg urspruenglich gefunden wurde.
    """
    env = dict(os.environ, MUSICDUPES_FFMPEG_DIR=os.path.join(DIST, "ffmpeg"))
    result = subprocess.run(
        [pyinstaller, "MusicDupes-single.spec", "--noconfirm", "--clean",
         "--distpath", SINGLE_DIST, "--workpath",
         os.path.join(ROOT, "build", "single")],
        cwd=ROOT, env=env,
    )
    if result.returncode != 0:
        raise SystemExit("Single-file build failed.")


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pack_zip() -> str:
    """Packt dist/MusicDupes und schreibt die Pruefsumme daneben."""
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    base = os.path.dirname(DIST)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for folder, dirs, names in os.walk(DIST):
            if folder == DIST:
                # Der Cache eines Probelaufs enthaelt alle Pfade der eigenen
                # Musiksammlung - der darf nie mit weitergegeben werden.
                dirs[:] = [d for d in dirs if d.lower() not in PRIVATE_DIRS]
            for name in names:
                full = os.path.join(folder, name)
                zf.write(full, os.path.relpath(full, base))

    digest = sha256_of(ZIP_PATH)
    with open(ZIP_PATH + ".sha256", "w", encoding="utf-8") as handle:
        handle.write("{}  {}\n".format(digest, os.path.basename(ZIP_PATH)))
    return digest


def main() -> int:
    # Getrennte Schritte, damit die Signatur dazwischen passt: erst bauen,
    # dann die EXE signieren lassen, dann mit der signierten EXE packen.
    parser = argparse.ArgumentParser(description="Builds the portable package.")
    parser.add_argument("--no-zip", action="store_true",
                        help="Build only, do not pack the ZIP yet")
    parser.add_argument("--zip-only", action="store_true",
                        help="Only pack dist/MusicDupes (after signing)")
    parser.add_argument("--no-single", action="store_true",
                        help="Skip the single-file build")
    options = parser.parse_args()

    if options.zip_only:
        if not os.path.isdir(DIST):
            raise SystemExit("dist/MusicDupes is missing.")
        if os.path.isfile(SINGLE_EXE):
            write_checksum(SINGLE_EXE)
            print("Single file: {}  ({})".format(
                SINGLE_EXE, human(os.path.getsize(SINGLE_EXE))
            ))
        digest = pack_zip()
        print("ZIP:     {}  ({})".format(
            ZIP_PATH, human(os.path.getsize(ZIP_PATH))
        ))
        print("SHA-256: " + digest)
        return 0

    pyinstaller = os.path.join(ROOT, ".venv", "Scripts", "pyinstaller.exe")
    if not os.path.isfile(pyinstaller):
        pyinstaller = shutil.which("pyinstaller") or ""
    if not pyinstaller:
        raise SystemExit(
            "PyInstaller is missing. Install it with:\n"
            "  .venv\\Scripts\\python.exe -m pip install pyinstaller"
        )

    ffmpeg_dir = find_ffmpeg_dir()
    licence = check_ffmpeg_licence(ffmpeg_dir)
    print("FFmpeg: {}  (licence: {})\n".format(ffmpeg_dir, licence))

    if licence in ("gpl", "nonfree"):
        print("=" * 70)
        print("  WARNING: this is a {} FFmpeg build.".format(licence.upper()))
        print("  MusicDupes is MIT-licensed, but a package containing these")
        print("  binaries falls under the GPL as a whole - and a 'nonfree'")
        print("  build may not be redistributed at all.")
        print("  MusicDupes only decodes audio, so a win64-lgpl-shared build")
        print("  from https://github.com/BtbN/FFmpeg-Builds is sufficient.")
        print("=" * 70)
        print()

    print("1/5  Running PyInstaller ...")
    result = subprocess.run(
        [pyinstaller, "MusicDupes.spec", "--noconfirm", "--clean"], cwd=ROOT
    )
    if result.returncode != 0:
        return result.returncode
    if not os.path.isdir(DIST):
        raise SystemExit("Expected folder is missing: " + DIST)

    print("\n2/5  Adding FFmpeg ...")
    target = os.path.join(DIST, "ffmpeg")
    os.makedirs(target, exist_ok=True)
    copied = 0
    for name in sorted(os.listdir(ffmpeg_dir)):
        lower = name.lower()
        if lower.startswith(SKIP_PREFIXES):
            continue
        if lower.endswith((".exe", ".dll", ".txt")):
            shutil.copy2(
                os.path.join(ffmpeg_dir, name), os.path.join(target, name)
            )
            copied += 1
    print("     {} files -> {}".format(copied, target))

    # The licence has to travel with the binaries - whoever passes the
    # package on passes FFmpeg on too.
    if not os.path.isfile(os.path.join(target, "LICENSE.txt")):
        for parent in (ffmpeg_dir, os.path.dirname(ffmpeg_dir)):
            source = os.path.join(parent, "LICENSE.txt")
            if os.path.isfile(source):
                shutil.copy2(source, os.path.join(target, "LICENSE.txt"))
                break
        else:
            print("     WARNING: no LICENSE.txt found for FFmpeg!")

    print("\n3/5  Companion files ...")
    for name in BESIDE_EXE:
        source = os.path.join(ROOT, name)
        if os.path.isfile(source):
            shutil.copy2(source, os.path.join(DIST, name))
            print("     " + name)
    os.makedirs(os.path.join(DIST, LICENCE_DIR), exist_ok=True)
    for name in LICENCE_TEXTS:
        source = os.path.join(ROOT, LICENCE_DIR, name)
        if not os.path.isfile(source):
            raise SystemExit("Licence text missing: " + source)
        shutil.copy2(source, os.path.join(DIST, LICENCE_DIR, name))
        print("     {}\\{}".format(LICENCE_DIR, name))

    # Dieselben Dateien ein zweites Mal verpackt: als eine einzelne EXE.
    # Gemessen gegen die Ordnerfassung kostet das rund eine Sekunde beim
    # Start, erspart Anwendern aber das Entpacken vollstaendig.
    if not options.no_single:
        print("\n4/5  Building the single-file version ...")
        build_single(pyinstaller)
        print("     {}  ({})".format(
            SINGLE_EXE, human(os.path.getsize(SINGLE_EXE))
        ))

    print("\nFolder:      {}  ({})".format(DIST, human(folder_size(DIST))))
    if options.no_zip:
        print("\nZIP skipped (--no-zip). Sign the executables, then run")
        print("  python build_portable.py --zip-only")
        return 0

    print("\n5/5  Packing ZIP ...")
    digest = pack_zip()
    print("\nDone.")
    print("  ZIP:         {}  ({})".format(
        ZIP_PATH, human(os.path.getsize(ZIP_PATH))
    ))
    print("  SHA-256:     " + digest)
    if os.path.isfile(SINGLE_EXE):
        single_digest = write_checksum(SINGLE_EXE)
        print("  Single file: {}  ({})".format(
            SINGLE_EXE, human(os.path.getsize(SINGLE_EXE))
        ))
        print("  SHA-256:     " + single_digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
