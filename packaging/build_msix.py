"""Builds the MSIX package for the Microsoft Store.

Runs on top of the finished `dist/MusicDupes` folder from build_portable.py:
the same files, wrapped differently. Nothing is rebuilt.

Needs `makeappx.exe` from the Windows SDK. GitHub's windows-latest runners
have it; on a local machine it comes with the Windows 10/11 SDK.

    python packaging/build_msix.py --publisher "CN=..." --identity "Name"

For a Store submission, Identity Name, Publisher and PublisherDisplayName
must match the values Partner Center shows under *Product identity*.
Without arguments the script builds an unsigned test package - Windows will
refuse to install that, but it is enough to validate the layout.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist", "MusicDupes")
STAGE = os.path.join(ROOT, "build", "msix")
ICONS = os.path.join(ROOT, "docs", "icon")
MANIFEST = os.path.join(ROOT, "packaging", "AppxManifest.xml")
OUTPUT = os.path.join(ROOT, "MusicDupes.msix")

ASSETS = (
    "Square44x44Logo.png", "Square71x71Logo.png", "Square150x150Logo.png",
    "Square310x310Logo.png", "Wide310x150Logo.png", "StoreLogo.png",
)


def find_makeappx() -> str:
    found = shutil.which("makeappx")
    if found:
        return found
    roots = [
        r"C:\Program Files (x86)\Windows Kits\10\bin",
        r"C:\Program Files\Windows Kits\10\bin",
    ]
    candidates = []
    for base in roots:
        if not os.path.isdir(base):
            continue
        for folder, _dirs, names in os.walk(base):
            if "makeappx.exe" in names and os.sep + "x64" in folder:
                candidates.append(os.path.join(folder, "makeappx.exe"))
    if candidates:
        # Highest SDK version wins.
        return sorted(candidates)[-1]
    raise SystemExit(
        "makeappx.exe not found. Install the Windows 10/11 SDK, or let the\n"
        "GitHub Actions workflow build the package - its runners ship it."
    )


def patch_manifest(target: str, args: argparse.Namespace) -> None:
    """Writes the Partner Center identity into the manifest."""
    namespace = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
    ET.register_namespace("", namespace)
    for prefix, uri in (
        ("uap", "http://schemas.microsoft.com/appx/manifest/uap/windows10"),
        ("rescap", "http://schemas.microsoft.com/appx/manifest/foundation/"
                   "windows10/restrictedcapabilities"),
    ):
        ET.register_namespace(prefix, uri)

    tree = ET.parse(MANIFEST)
    root = tree.getroot()

    identity = root.find("{%s}Identity" % namespace)
    if args.identity:
        identity.set("Name", args.identity)
    if args.publisher:
        identity.set("Publisher", args.publisher)
    if args.version:
        identity.set("Version", args.version)

    if args.publisher_display:
        props = root.find("{%s}Properties" % namespace)
        node = props.find("{%s}PublisherDisplayName" % namespace)
        node.text = args.publisher_display

    tree.write(target, encoding="utf-8", xml_declaration=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", help="Identity Name from Partner Center")
    parser.add_argument("--publisher", help='Publisher, e.g. "CN=1234-ABCD-..."')
    parser.add_argument("--publisher-display", help="PublisherDisplayName")
    parser.add_argument("--version", help="Four-part version, e.g. 1.1.0.0")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()

    if not os.path.isdir(DIST):
        raise SystemExit(
            "dist/MusicDupes is missing - run build_portable.py first."
        )

    makeappx = find_makeappx()
    print("makeappx: {}\n".format(makeappx))

    print("1/3  Staging files ...")
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    # Ein Probelauf der Ordnerfassung hinterlaesst data\ mit dem Cache - und
    # damit allen Pfaden der eigenen Musiksammlung. Der gehoert nie ins Paket.
    shutil.copytree(
        DIST, STAGE,
        ignore=lambda folder, names: (
            ["data"] if os.path.normcase(folder) == os.path.normcase(DIST) else []
        ),
    )

    # The portable guides talk about unblocking ZIPs and a data folder next
    # to the executable. Neither applies to a Store install, so they would
    # only mislead.
    for name in ("LIESMICH.txt", "README.txt"):
        stale = os.path.join(STAGE, name)
        if os.path.isfile(stale):
            os.remove(stale)

    assets = os.path.join(STAGE, "Assets")
    os.makedirs(assets, exist_ok=True)
    for name in ASSETS:
        source = os.path.join(ICONS, name)
        if not os.path.isfile(source):
            raise SystemExit(
                "Missing tile: {}\nRun tools/make_icon.py first.".format(source)
            )
        shutil.copy2(source, os.path.join(assets, name))
    print("     {} tiles".format(len(ASSETS)))

    print("\n2/3  Writing manifest ...")
    patch_manifest(os.path.join(STAGE, "AppxManifest.xml"), args)
    if not args.publisher:
        print("     NOTE: no --publisher given - unsigned test package.")
        print("     Windows will refuse to install it; the Store signs the")
        print("     real one for you after certification.")

    print("\n3/3  Packing ...")
    if os.path.exists(args.output):
        os.remove(args.output)
    result = subprocess.run(
        [makeappx, "pack", "/d", STAGE, "/p", args.output, "/o"],
        cwd=ROOT,
    )
    if result.returncode != 0:
        return result.returncode

    size = os.path.getsize(args.output)
    print("\nDone: {}  ({:.1f} MB)".format(args.output, size / 1048576))
    print("Upload this file in Partner Center. Microsoft signs it after")
    print("certification - users then see no SmartScreen warning at all.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
