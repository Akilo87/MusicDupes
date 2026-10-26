"""Erzeugt Programmsymbol und Store-Kacheln aus einer Zeichnung.

Reproduzierbar im Repo statt als Binaerdatei von irgendwoher: das Symbol
laesst sich so nachvollziehen und aendern.

Motiv: eine Wellenform, dahinter versetzt dieselbe Wellenform blass - zwei
Kopien desselben Tons. Bewusst sehr einfach, weil das Symbol auch bei 16
Pixeln noch erkennbar sein muss.

Aufruf:  .venv\\Scripts\\python.exe tools\\make_icon.py
"""

from __future__ import annotations

import os
import struct
import sys

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush, QColor, QGuiApplication, QImage, QLinearGradient, QPainter,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(ROOT, "docs", "icon")
ICO_PATH = os.path.join(ROOT, "musicdupes.ico")

# Balkenhoehen der Wellenform, als Anteil der Bildhoehe.
BARS = (0.34, 0.62, 0.92, 0.52, 0.74, 0.40)

BACK_TOP = QColor("#3b82f6")
BACK_BOTTOM = QColor("#1e3a8a")
GHOST = QColor(255, 255, 255, 90)
SOLID = QColor(255, 255, 255, 240)

# Groessen fuer die .ico-Datei und die Store-Kacheln.
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
STORE_ASSETS = {
    "Square44x44Logo.png": (44, 44),
    "Square71x71Logo.png": (71, 71),
    "Square150x150Logo.png": (150, 150),
    "Square310x310Logo.png": (310, 310),
    "Wide310x150Logo.png": (310, 150),
    "StoreLogo.png": (50, 50),
}


def _draw_bars(painter: QPainter, rect: QRectF, colour: QColor) -> None:
    count = len(BARS)
    gap = rect.width() / (count * 3.2)
    bar_width = (rect.width() - gap * (count - 1)) / count
    radius = bar_width * 0.42
    painter.setBrush(QBrush(colour))
    painter.setPen(Qt.NoPen)
    for index, factor in enumerate(BARS):
        height = rect.height() * factor
        x = rect.left() + index * (bar_width + gap)
        y = rect.center().y() - height / 2
        painter.drawRoundedRect(
            QRectF(x, y, bar_width, height), radius, radius
        )


def render(width: int, height: int) -> QImage:
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # Hintergrund: abgerundetes Quadrat mit Verlauf.
    side = min(width, height)
    inset = side * 0.045
    box = QRectF(
        (width - side) / 2 + inset, (height - side) / 2 + inset,
        side - 2 * inset, side - 2 * inset,
    )
    gradient = QLinearGradient(QPointF(box.topLeft()), QPointF(box.bottomRight()))
    gradient.setColorAt(0.0, BACK_TOP)
    gradient.setColorAt(1.0, BACK_BOTTOM)
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.NoPen)
    corner = box.width() * 0.22
    painter.drawRoundedRect(box, corner, corner)

    # Zwei Wellenformen, die hintere versetzt und blass: das Duplikat.
    inner = QRectF(
        box.left() + box.width() * 0.20,
        box.top() + box.height() * 0.24,
        box.width() * 0.56,
        box.height() * 0.52,
    )
    offset = box.width() * 0.085
    _draw_bars(
        painter,
        inner.adjusted(offset, -offset * 0.45, offset, -offset * 0.45),
        GHOST,
    )
    _draw_bars(painter, inner, SOLID)
    painter.end()
    return image


def write_ico(path: str) -> None:
    """Schreibt eine .ico-Datei mit PNG-Eintraegen.

    Windows versteht PNG-komprimierte Eintraege seit Vista; so bleibt die
    Datei klein und 256x256 ueberhaupt erst moeglich.
    """
    entries = []
    for size in ICO_SIZES:
        image = render(size, size)
        from PySide6.QtCore import QBuffer, QByteArray

        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QBuffer.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        entries.append((size, bytes(data)))

    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = len(header) + 16 * len(entries)
    directory = b""
    payload = b""
    for size, blob in entries:
        dimension = 0 if size >= 256 else size
        directory += struct.pack(
            "<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(blob), offset
        )
        payload += blob
        offset += len(blob)

    with open(path, "wb") as handle:
        handle.write(header + directory + payload)


def main() -> int:
    # Ohne QGuiApplication gibt es keinen Grafikstapel fuer QPainter.
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)

    os.makedirs(ICON_DIR, exist_ok=True)
    write_ico(ICO_PATH)
    print("  {}  ({} Bytes)".format(ICO_PATH, os.path.getsize(ICO_PATH)))

    for name, (width, height) in STORE_ASSETS.items():
        target = os.path.join(ICON_DIR, name)
        render(width, height).save(target, "PNG")
        print("  {}  {}x{}".format(target, width, height))

    # Grosse Fassung fuer README und Store-Eintrag.
    big = os.path.join(ICON_DIR, "icon-512.png")
    render(512, 512).save(big, "PNG")
    print("  {}  512x512".format(big))
    del app
    return 0


if __name__ == "__main__":
    sys.exit(main())
