# Code signing policy

> Required by SignPath Foundation. The page has to be publicly reachable
> and linked from the project home page before an application is approved.

**Status:** prepared in the release workflow, application with SignPath
Foundation pending. Until it is approved, releases are published unsigned.
Once approved, signed releases carry the note:

*Free code signing provided by [SignPath.io](https://about.signpath.io/),
certificate by [SignPath Foundation](https://signpath.org/).*

## Signing

Release binaries of MusicDupes are signed by
**[SignPath Foundation](https://signpath.org/)**, which provides free code
signing certificates to open source projects.

Signing happens inside the public GitHub Actions workflow
[`release.yml`](../.github/workflows/release.yml), from the tagged source in
this repository. No binary is ever built or signed on a private machine and
uploaded afterwards. The private key never leaves SignPath's hardware
security module; the project has no copy of it.

* **Certificate:** issued to SignPath Foundation
* **Signed artifacts:** both executables of a release - the single
  `MusicDupes.exe` and the `MusicDupes.exe` inside `MusicDupes-Portable.zip`
* **File metadata:** product name `MusicDupes`, product version equal to the
  release version (set at build time from `musicdupes/__init__.py`)
* **Build system:** GitHub Actions, `windows-latest` runners
* **Trigger:** version tags (`v*`) only

Third-party binaries shipped in the package (Python, Qt, NumPy, FFmpeg) are
included unmodified and are not re-signed by this project.

The Microsoft Store package is signed separately by Microsoft after Store
certification.

## Team roles

| Role | Members |
|---|---|
| Committers and reviewers | The repository owner |
| Approvers | The repository owner |

Only the repository owner can push a version tag, and only a version tag
starts a signing request. Every signing request additionally requires manual
approval in SignPath. Changes from other contributors are merged only after
review by the owner.

Contributors can open pull requests freely; pull request builds are never
signed.

## Privacy

This program will not transfer any information to other networked systems
unless specifically requested by the user or the person installing or
operating it. MusicDupes has no network access at all - see the
[privacy policy](privacy.md).

## Reporting a problem

If you find a signed binary that does not match the corresponding tagged
source, please open an issue in this repository immediately and state the
version and the SHA-256 checksum of the file you have.

---

# Richtlinie zur Code-Signatur

**Stand:** im Release-Ablauf vorbereitet, Antrag bei SignPath Foundation
gestellt bzw. geplant. Bis zur Freigabe erscheinen Veröffentlichungen
unsigniert.

Veröffentlichte Programmdateien von MusicDupes werden von
**[SignPath Foundation](https://signpath.org/)** signiert, die
Open-Source-Projekten kostenlose Signaturzertifikate bereitstellt. Signiert
werden beide Programmdateien eines Release: die einzelne `MusicDupes.exe`
und die `MusicDupes.exe` in `MusicDupes-Portable.zip`.

Signiert wird innerhalb des öffentlich einsehbaren GitHub-Actions-Ablaufs
[`release.yml`](../.github/workflows/release.yml), aus dem markierten
Quellstand dieses Repositories. Keine Datei wird auf einem privaten Rechner
gebaut, signiert und nachträglich hochgeladen. Der private Schlüssel
verlässt das Hardware-Sicherheitsmodul von SignPath nie; das Projekt besitzt
keine Kopie davon.

Nur der Eigentümer des Repositories kann eine Versionsmarkierung setzen, und
nur eine solche löst eine Signaturanfrage aus. Jede Anfrage muss in SignPath
zusätzlich manuell freigegeben werden. Beiträge per Pull Request werden
niemals signiert.

MusicDupes erhebt, überträgt und speichert keine Daten und hat keinerlei
Netzwerkzugriff — siehe [Datenschutzerklärung](privacy.md).
