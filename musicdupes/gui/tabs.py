"""Die beiden zusaetzlichen Reiter: Paarvergleich und Dateiqualitaet."""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel,
    QTreeWidget, QVBoxLayout, QWidget,
)

from .. import formatting, i18n
from ..i18n import t
from ..matcher import MATCH_SAME_TITLE, match_help, match_label
from ..quality import club_rating
from .widgets import BarDelegate, ROLE_RECORD, ROLE_SCORE, SortableItem, with_info

PAIR_COLUMN_KEYS = [
    ("col.group", 70), ("col.file_a", 300), ("col.file_b", 300),
    ("col.similarity", 130), ("col.coverage", 100),
    ("col.duration_a", 80), ("col.duration_b", 80), ("col.offset", 80),
    ("col.kind", 200), ("col.folder", 320),
]
(P_GROUP, P_A, P_B, P_SIMILAR, P_COVER, P_DUR_A, P_DUR_B, P_OFFSET,
 P_KIND, P_FOLDER) = range(10)

QUALITY_COLUMN_KEYS = [
    ("csv.file", 320), ("col.club", 140), ("col.rating", 100),
    ("col.format", 85), ("col.bitrate", 100), ("col.bandwidth", 95),
    ("col.samplerate", 95), ("col.channels", 75), ("col.duration", 75),
    ("col.size", 90), ("col.flags", 200), ("col.folder", 320),
]
(Q_NAME, Q_BAR, Q_LABEL, Q_FORMAT, Q_BITRATE, Q_BANDWIDTH, Q_RATE,
 Q_CHANNELS, Q_DURATION, Q_SIZE, Q_FLAGS, Q_FOLDER) = range(12)


def _base_tree(column_keys: list) -> QTreeWidget:
    tree = QTreeWidget()
    tree.setColumnCount(len(column_keys))
    tree.setHeaderLabels([t(key) for key, _ in column_keys])
    tree.setAlternatingRowColors(True)
    tree.setRootIsDecorated(False)
    tree.setUniformRowHeights(True)
    tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
    tree.setSortingEnabled(True)
    for column, (_, width) in enumerate(column_keys):
        tree.setColumnWidth(column, width)
    header = tree.header()
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setStretchLastSection(True)
    head = tree.headerItem()
    for column, (key, _) in enumerate(column_keys):
        text = t("help." + key)
        if text != "help." + key:
            head.setToolTip(column, text)
    return tree


class PairTab(QWidget):
    """Jedes Dateipaar einzeln - mit beiden Lesarten des Vergleichs."""

    selectionChanged = Signal()
    revealRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)

        head = QHBoxLayout()
        head.addWidget(with_info(
            QLabel(t("lbl.pair_head")), t("help.tab_pairs")
        ))
        head.addStretch(1)
        self.summary = QLabel("")
        self.summary.setStyleSheet("color: rgba(140,140,140,235);")
        head.addWidget(self.summary)
        layout.addLayout(head)

        self.tree = _base_tree(PAIR_COLUMN_KEYS)
        self.tree.setItemDelegateForColumn(P_SIMILAR, BarDelegate(self.tree))
        self.tree.itemSelectionChanged.connect(self.selectionChanged.emit)
        self.tree.itemDoubleClicked.connect(lambda *_: self.revealRequested.emit())
        layout.addWidget(self.tree)
        self.records: list = []
        self._text = ""
        self._count_text = ""

    def populate(self, records: list, groups: list) -> None:
        self.records = records
        self.tree.setSortingEnabled(False)
        self.tree.clear()

        count = 0
        for number, group in enumerate(groups, 1):
            for pair in group.pairs:
                first, second = records[pair.a], records[pair.b]
                item = SortableItem(self.tree)
                item.set_sortable(P_GROUP, str(number), number)
                item.set_sortable(
                    P_A, os.path.basename(first.get("path") or ""),
                    os.path.basename(first.get("path") or "").lower(),
                )
                item.set_sortable(
                    P_B, os.path.basename(second.get("path") or ""),
                    os.path.basename(second.get("path") or "").lower(),
                )
                item.set_sortable(
                    P_SIMILAR, "{:.0f} %".format(pair.similarity * 100),
                    pair.similarity,
                )
                item.setData(P_SIMILAR, ROLE_SCORE, pair.similarity * 100)
                item.set_sortable(
                    P_COVER, "{:.0f} %".format(pair.coverage * 100),
                    pair.coverage,
                )
                item.set_sortable(
                    P_DUR_A, formatting.duration(first.get("duration")),
                    float(first.get("duration") or 0.0),
                )
                item.set_sortable(
                    P_DUR_B, formatting.duration(second.get("duration")),
                    float(second.get("duration") or 0.0),
                )
                item.set_sortable(
                    P_OFFSET, formatting.offset(pair.offset), abs(pair.offset)
                )
                item.set_sortable(
                    P_KIND, match_label(pair.kind), pair.kind
                )
                item.setToolTip(P_KIND, match_help(pair.kind))
                if pair.kind == MATCH_SAME_TITLE:
                    item.setForeground(P_KIND, QBrush(QColor("#b8860b")))
                item.set_sortable(
                    P_FOLDER, os.path.dirname(first.get("path") or ""),
                    (os.path.dirname(first.get("path") or "")).lower(),
                )

                # Der Unterschied zwischen beiden Zahlen ist die eigentliche
                # Aussage - deshalb steht er als Hinweis an der Zeile.
                if pair.coverage - pair.similarity > 0.12:
                    item.setToolTip(P_SIMILAR, t(
                        "tip.pair_gap",
                        coverage=pair.coverage * 100,
                        similarity=pair.similarity * 100,
                    ))

                for column in (P_GROUP, P_SIMILAR, P_COVER, P_DUR_A, P_DUR_B,
                               P_OFFSET):
                    item.setTextAlignment(column, Qt.AlignRight | Qt.AlignVCenter)

                item.setData(P_A, ROLE_RECORD, pair.a)
                item.setData(P_B, ROLE_RECORD, pair.b)
                count += 1

        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(P_SIMILAR, Qt.AscendingOrder)
        self._count_text = t("pairs.count", count=count)
        self._apply_filter()

    def set_text_filter(self, text: str) -> None:
        self._text = (text or "").strip().lower()
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Ein Paar bleibt sichtbar, wenn eine der beiden Dateien passt."""
        visible = 0
        total = self.tree.topLevelItemCount()
        for row in range(total):
            item = self.tree.topLevelItem(row)
            show = True
            if self._text:
                show = any(
                    self._text in formatting.search_text(self.records[index])
                    for index in (item.data(P_A, ROLE_RECORD),
                                  item.data(P_B, ROLE_RECORD))
                )
            item.setHidden(not show)
            visible += int(show)
        if self._text:
            self.summary.setText(t("pairs.visible", visible=visible, total=total))
        else:
            self.summary.setText(self._count_text)

    def selected_record(self):
        for item in self.tree.selectedItems():
            value = item.data(P_A, ROLE_RECORD)
            if value is not None:
                return value
        return None


class QualityTab(QWidget):
    """Alle gefundenen Dateien, sortierbar nach Eignung und Format."""

    selectionChanged = Signal()
    revealRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)

        head = QHBoxLayout()
        head.addWidget(with_info(
            QLabel(t("lbl.quality_head")), t("help.tab_quality")
        ))
        head.addSpacing(18)
        head.addWidget(QLabel(t("lbl.format")))
        self.format_filter = QComboBox()
        self.format_filter.addItem(t("cmb.all_formats"), "")
        self.format_filter.currentIndexChanged.connect(self._apply_filter)
        head.addWidget(self.format_filter)
        head.addSpacing(12)
        head.addWidget(QLabel(t("lbl.rating")))
        self.rating_filter = QComboBox()
        self.rating_filter.addItem(t("cmb.all_ratings"), "")
        for key in ("club.very_good", "club.good", "club.usable",
                    "club.marginal", "club.unsuitable"):
            self.rating_filter.addItem(t(key), t(key))
        self.rating_filter.currentIndexChanged.connect(self._apply_filter)
        head.addWidget(self.rating_filter)
        head.addStretch(1)
        self.summary = QLabel("")
        self.summary.setStyleSheet("color: rgba(140,140,140,235);")
        head.addWidget(self.summary)
        layout.addLayout(head)

        self.tree = _base_tree(QUALITY_COLUMN_KEYS)
        self.tree.setItemDelegateForColumn(Q_BAR, BarDelegate(self.tree))
        self.tree.itemSelectionChanged.connect(self.selectionChanged.emit)
        self.tree.itemDoubleClicked.connect(lambda *_: self.revealRequested.emit())
        layout.addWidget(self.tree)

        self.records: list = []
        self._text = ""
        # Zusammenfassung ohne Filter - kommt zurueck, wenn er geleert wird.
        self._count_text = ""

    def populate(self, records: list) -> None:
        self.records = records
        self.tree.setSortingEnabled(False)
        self.tree.clear()

        formats = set()
        counts = {}
        for index, record in enumerate(records):
            if record.get("error"):
                continue
            score, label = club_rating(record)
            counts[label] = counts.get(label, 0) + 1
            codec = (record.get("codec") or "").upper()
            formats.add(codec)

            item = SortableItem(self.tree)
            name = os.path.basename(record.get("path") or "")
            item.set_sortable(Q_NAME, name, name.lower())
            item.set_sortable(Q_BAR, "{:.0f}".format(score), score)
            item.setData(Q_BAR, ROLE_SCORE, score)
            item.set_sortable(Q_LABEL, label, score)
            item.set_sortable(Q_FORMAT, codec, codec)
            item.set_sortable(
                Q_BITRATE, formatting.bitrate(record),
                int(record.get("bitrate") or 0),
            )
            item.set_sortable(
                Q_BANDWIDTH, formatting.bandwidth(record.get("cutoff_hz")),
                float(record.get("cutoff_hz") or 0.0),
            )
            item.set_sortable(
                Q_RATE, "{} Hz".format(record.get("sample_rate") or 0),
                int(record.get("sample_rate") or 0),
            )
            item.set_sortable(
                Q_CHANNELS,
                {1: t("val.mono"), 2: t("val.stereo")}.get(
                    int(record.get("channels") or 0),
                    str(record.get("channels") or 0),
                ),
                int(record.get("channels") or 0),
            )
            item.set_sortable(
                Q_DURATION, formatting.duration(record.get("duration")),
                float(record.get("duration") or 0.0),
            )
            item.set_sortable(
                Q_SIZE, formatting.filesize(record.get("size")),
                int(record.get("size") or 0),
            )
            flags = record.get("quality_flags") or []
            shown = ", ".join(i18n.flag_texts(record))
            item.set_sortable(Q_FLAGS, shown, shown)
            if i18n.FLAG_TRANSCODE in flags:
                item.setForeground(Q_FLAGS, QBrush(QColor("#c0392b")))
            item.set_sortable(
                Q_FOLDER, os.path.dirname(record.get("path") or ""),
                (os.path.dirname(record.get("path") or "")).lower(),
            )

            for column in (Q_BAR, Q_BITRATE, Q_BANDWIDTH, Q_RATE, Q_DURATION,
                           Q_SIZE):
                item.setTextAlignment(column, Qt.AlignRight | Qt.AlignVCenter)

            item.setData(Q_NAME, ROLE_RECORD, index)

        current = self.format_filter.currentData()
        self.format_filter.blockSignals(True)
        self.format_filter.clear()
        self.format_filter.addItem(t("cmb.all_formats"), "")
        for codec in sorted(formats):
            self.format_filter.addItem(codec, codec)
        position = self.format_filter.findData(current)
        self.format_filter.setCurrentIndex(max(0, position))
        self.format_filter.blockSignals(False)

        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(Q_BAR, Qt.AscendingOrder)

        order = [t(key) for key in ("club.unsuitable", "club.marginal",
                                    "club.usable", "club.good", "club.very_good")]
        parts = [
            "{}x {}".format(counts[label], label)
            for label in order if counts.get(label)
        ]
        self._count_text = "   ".join(parts)
        self._apply_filter()

    def set_text_filter(self, text: str) -> None:
        self._text = (text or "").strip().lower()
        self._apply_filter()

    def _apply_filter(self) -> None:
        codec = self.format_filter.currentData()
        rating = self.rating_filter.currentData()
        visible = 0
        for row in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(row)
            show = True
            if codec and item.text(Q_FORMAT) != codec:
                show = False
            if show and rating and item.text(Q_LABEL) != rating:
                show = False
            if show and self._text:
                record = self.records[item.data(Q_NAME, ROLE_RECORD)]
                show = self._text in formatting.search_text(record)
            item.setHidden(not show)
            if show:
                visible += 1
        if codec or rating or self._text:
            self.summary.setText(t(
                "quality.visible",
                visible=visible, total=self.tree.topLevelItemCount(),
            ))
        else:
            # Sonst bliebe nach dem Leeren des Filters die alte Zahl stehen.
            self.summary.setText(self._count_text)

    def selected_record(self):
        for item in self.tree.selectedItems():
            value = item.data(Q_NAME, ROLE_RECORD)
            if value is not None:
                return value
        return None
