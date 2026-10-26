"""Gemeinsame Bausteine der Oberflaeche."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QStyledItemDelegate, QTreeWidgetItem, QWidget,
)

ROLE_RECORD = Qt.UserRole + 1
ROLE_SCORE = Qt.UserRole + 2
ROLE_SORT = Qt.UserRole + 4


def score_color(score: float) -> QColor:
    """Rot (schlecht) ueber Gelb nach Gruen (gut)."""
    value = max(0.0, min(100.0, float(score))) / 100.0
    if value < 0.5:
        ratio = value / 0.5
        return QColor(int(200 + 25 * ratio), int(60 + 130 * ratio), 50)
    ratio = (value - 0.5) / 0.5
    return QColor(int(225 - 145 * ratio), int(190 - 20 * ratio), int(50 + 30 * ratio))


class BarDelegate(QStyledItemDelegate):
    """Zeichnet einen Wert 0..100 als farbigen Balken hinter dem Text.

    Ein Balken laesst sich quer ueber hunderte Zeilen erfassen, eine Zahl
    nicht.
    """

    def __init__(self, parent=None, fraction: float = 0.62) -> None:
        super().__init__(parent)
        self.fraction = fraction

    def paint(self, painter: QPainter, option, index) -> None:
        score = index.data(ROLE_SCORE)
        super().paint(painter, option, index)
        if score is None:
            return

        rect = option.rect.adjusted(6, 0, -6, 0)
        bar_height = 6
        bar = rect.adjusted(0, (rect.height() - bar_height) // 2, 0, 0)
        bar.setHeight(bar_height)
        bar.setWidth(max(10, int(rect.width() * self.fraction)))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 38))
        painter.drawRoundedRect(bar, 3, 3)
        filled = bar.adjusted(0, 0, 0, 0)
        filled.setWidth(
            max(2, int(bar.width() * max(0.0, min(100.0, float(score))) / 100.0))
        )
        painter.setBrush(score_color(float(score)))
        painter.drawRoundedRect(filled, 3, 3)
        painter.restore()


class SortableItem(QTreeWidgetItem):
    """Zeile, die nach hinterlegten Zahlen sortiert statt nach Text.

    Ohne das stuende in einer nach Bitrate sortierten Liste 96 vor 1411.
    """

    def __lt__(self, other) -> bool:
        tree = self.treeWidget()
        column = tree.sortColumn() if tree is not None else 0
        mine = self.data(column, ROLE_SORT)
        theirs = other.data(column, ROLE_SORT)
        if mine is not None and theirs is not None:
            try:
                return mine < theirs
            except TypeError:
                pass
        return super().__lt__(other)

    def set_sortable(self, column: int, text: str, value) -> None:
        self.setText(column, text)
        self.setData(column, ROLE_SORT, value)


def info_icon(text: str) -> QLabel:
    """Kleines Info-Symbol, das beim Ueberfahren erklaert."""
    label = QLabel("ⓘ")
    label.setToolTip(text)
    label.setCursor(Qt.WhatsThisCursor)
    label.setStyleSheet(
        "QLabel { color: rgba(120,170,220,255); font-size: 15px; "
        "padding: 0px 2px; }"
        "QLabel:hover { color: rgba(160,205,255,255); }"
    )
    return label


def with_info(widget: QWidget, text: str) -> QWidget:
    """Stellt ein Info-Symbol neben ein Bedienelement."""
    holder = QWidget()
    row = QHBoxLayout(holder)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(4)
    row.addWidget(widget)
    row.addWidget(info_icon(text))
    row.addStretch(1)
    return holder
