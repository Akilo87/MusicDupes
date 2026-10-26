"""Einstiegspunkt fuer die Portable-Fassung.

PyInstaller fuehrt sein Startskript als *Skript* aus, nicht als Modul eines
Pakets. Zeigt man es direkt auf ``musicdupes/__main__.py``, schlagen dort alle
relativen Importe fehl ("attempted relative import with no known parent
package"). Deshalb dieser Umweg: hier wird ``musicdupes`` ganz normal als
Paket importiert, und drinnen funktioniert wieder alles.
"""

import multiprocessing
import sys

from musicdupes.__main__ import main

if __name__ == "__main__":
    # Muss als Allererstes kommen: die Worker-Prozesse starten diese EXE
    # erneut, und freeze_support faengt sie ab, bevor sie eine zweite
    # Oberflaeche aufmachen.
    multiprocessing.freeze_support()
    sys.exit(main())
