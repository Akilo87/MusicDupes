"""Hauptfenster von MusicDupes."""

from __future__ import annotations

import os
import shutil
import subprocess

from PySide6.QtCore import QSettings, Qt, QThread, Signal
from PySide6.QtGui import (
    QAction, QActionGroup, QBrush, QColor, QFont, QIcon, QKeySequence,
)
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFileDialog,
    QFrame, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QSizePolicy, QSlider,
    QSplitter, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from .. import exporting, formatting, i18n
from ..audio import tools_available
from ..cache import Cache, app_folder, default_path, settings_path
from ..resources import icon_file, is_onefile, licence_files
from ..engine import Cancelled, ScanEngine, default_workers
from ..i18n import t
from ..matcher import (
    MATCH_IDENTICAL_AUDIO, MATCH_IDENTICAL_FILE, MATCH_SAME_RECORDING,
    MATCH_SAME_TITLE, build_groups, match_help, match_label, redundant_bytes,
)
from .tabs import PairTab, QualityTab
from .widgets import BarDelegate, ROLE_RECORD, ROLE_SCORE, with_info

# Standardwerte der beiden Regler. Der akustische steht bewusst streng:
# Herunterdrehen kann man ihn jederzeit mit "Neu gruppieren", eine Liste
# voller Fehltreffer beim ersten Start verdirbt dagegen den Eindruck.
DEFAULT_AUDIO_THRESHOLD = 90
DEFAULT_META_THRESHOLD = 82

# Spaltenreihenfolge des Duplikate-Reiters: (Textschlüssel, Breite)
COLUMN_KEYS = [
    ("col.file_group", 340),
    ("col.hits", 90),
    ("col.kind", 200),
    ("col.quality", 110),
    ("col.format", 80),
    ("col.bitrate", 95),
    ("col.bandwidth", 95),
    ("col.duration", 70),
    ("col.size", 85),
    ("col.offset", 75),
    ("col.flags", 200),
    ("col.folder", 420),
]

COL_NAME, COL_SCORE, COL_KIND, COL_QUALITY, COL_FORMAT, COL_BITRATE = range(6)
COL_BANDWIDTH, COL_DURATION, COL_SIZE, COL_OFFSET, COL_FLAGS, COL_FOLDER = range(6, 12)

KIND_COLORS = {
    MATCH_IDENTICAL_FILE: "#c0392b",
    MATCH_IDENTICAL_AUDIO: "#d35400",
    MATCH_SAME_RECORDING: "#2c7fb8",
    MATCH_SAME_TITLE: "#7f8c8d",
}

NAME_MATCH_COLOR = "#b8860b"


class Worker(QThread):
    """Scan bzw. Neugruppierung im Hintergrund."""

    progressed = Signal(str, int, int)
    finished_ok = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, mode: str, payload: dict) -> None:
        super().__init__()
        self.mode = mode
        self.payload = payload
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    def _should_stop(self) -> bool:
        return self._stop

    def run(self) -> None:
        try:
            if self.mode == "scan":
                engine = ScanEngine(self.payload.get("cache_path"))
                result = engine.scan(
                    self.payload["root"],
                    recursive=self.payload["recursive"],
                    audio_threshold=self.payload["audio_threshold"],
                    meta_threshold=self.payload["meta_threshold"],
                    use_metadata=self.payload["use_metadata"],
                    use_cache=self.payload["use_cache"],
                    progress=self.progressed.emit,
                    should_stop=self._should_stop,
                )
                self.finished_ok.emit(result)
            else:
                def progress(stage: str, done: int, total: int) -> None:
                    self.progressed.emit(stage, done, total)
                    if self._stop:
                        raise Cancelled()

                groups, stats = build_groups(
                    self.payload["records"],
                    audio_threshold=self.payload["audio_threshold"],
                    meta_threshold=self.payload["meta_threshold"],
                    use_metadata=self.payload["use_metadata"],
                    progress=progress,
                    stage1_cache=self.payload["stage1"],
                )
                self.finished_ok.emit((groups, stats))
        except Cancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001
            import traceback
            self.failed.emit("{}\n\n{}".format(exc, traceback.format_exc(limit=6)))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # INI neben der EXE statt Registry - sonst wäre die Portable-Fassung
        # nicht wirklich portabel.
        self.settings = QSettings(settings_path(), QSettings.IniFormat)
        # Die Sprache steht vor dem Aufbau fest: Beschriftungen werden einmal
        # gesetzt und nicht zur Laufzeit ausgetauscht.
        self.language_setting = str(self.settings.value("language", "auto"))
        i18n.set_language(self.language_setting)

        self.setWindowTitle("MusicDupes")
        # Auch direkt am Fenster: greift selbst dann, wenn das Fenster ohne
        # den ueblichen Starter erzeugt wird.
        path = icon_file()
        if path:
            icon = QIcon(path)
            if not icon.isNull():
                self.setWindowIcon(icon)
        self.resize(1560, 900)

        self.records: list = []
        self.groups: list = []
        self.stats: dict = {}
        # Kandidatensuche des letzten Scans - "Neu gruppieren" braucht sie
        # nicht noch einmal, sie haengt von keinem Schwellwert ab.
        self.stage1: dict = {}
        self.worker: Worker | None = None
        self._close_pending = False
        self.columns = [(t(key), width) for key, width in COLUMN_KEYS]

        self._build_ui()
        self._restore_settings()
        self._check_tools()

    # -- Aufbau ------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 8)
        layout.setSpacing(10)

        layout.addWidget(self._build_folder_row())
        layout.addWidget(self._build_options())

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat(t("state.ready"))
        self.progress.setMaximum(1)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Die Detailanzeige liegt unter den Reitern und gehört allen dreien -
        # egal wo etwas ausgewählt wird, die Daten stehen an derselben Stelle.
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self._build_tabs())
        splitter.addWidget(self._build_details())
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([640, 195])
        layout.addWidget(splitter, 1)

        self.setCentralWidget(central)
        self.status = self.statusBar()
        self.status.showMessage(t("status.start", workers=default_workers()))
        self._build_menu()

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu(t("menu.file"))

        act_scan = QAction(t("menu.scan"), self)
        act_scan.setShortcut(QKeySequence("F5"))
        act_scan.triggered.connect(self.start_scan)
        menu.addAction(act_scan)

        act_export = QAction(t("menu.export_dupes"), self)
        act_export.setShortcut(QKeySequence.Save)
        act_export.triggered.connect(self.export_csv)
        menu.addAction(act_export)

        act_quality = QAction(t("menu.export_quality"), self)
        act_quality.triggered.connect(self.export_quality_csv)
        menu.addAction(act_quality)

        menu.addSeparator()
        act_clear = QAction(t("menu.clear_cache"), self)
        act_clear.triggered.connect(self.clear_cache)
        menu.addAction(act_clear)

        menu.addSeparator()
        act_quit = QAction(t("menu.quit"), self)
        act_quit.setShortcut(QKeySequence.Quit)
        act_quit.triggered.connect(self.close)
        menu.addAction(act_quit)

        self._build_language_menu()

        help_menu = self.menuBar().addMenu(t("menu.help"))
        act_help = QAction(t("menu.how"), self)
        act_help.triggered.connect(self.show_help)
        help_menu.addAction(act_help)

        act_licences = QAction(t("menu.licences"), self)
        act_licences.triggered.connect(self.show_licences)
        help_menu.addAction(act_licences)

    def _build_language_menu(self) -> None:
        """Sprachwahl.

        Normalfall ist die Systemsprache; die Einträge sind für den Fall da,
        dass jemand es anders möchte.
        """
        menu = self.menuBar().addMenu(t("menu.language"))
        group = QActionGroup(self)
        group.setExclusive(True)

        entries = [("auto", t("menu.lang_auto"))]
        entries += [(code, i18n.LANGUAGE_NAMES[code]) for code in i18n.LANGUAGES]

        for code, label in entries:
            action = QAction(label, self, checkable=True)
            action.setChecked(code == self.language_setting)
            action.triggered.connect(
                lambda _checked=False, value=code: self.choose_language(value)
            )
            group.addAction(action)
            menu.addAction(action)

    def _build_folder_row(self) -> QWidget:
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)

        row.addWidget(QLabel(t("lbl.folder")))
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText(t("ph.folder"))
        row.addWidget(self.folder_edit, 1)

        browse = QPushButton(t("btn.browse"))
        browse.clicked.connect(self.choose_folder)
        row.addWidget(browse)

        self.scan_button = QPushButton(t("btn.scan"))
        self.scan_button.setDefault(True)
        self.scan_button.setMinimumWidth(130)
        self.scan_button.clicked.connect(self.start_scan)
        row.addWidget(self.scan_button)

        self.cancel_button = QPushButton(t("btn.cancel"))
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_scan)
        row.addWidget(self.cancel_button)

        return box

    def _slider(self, value: int, minimum: int) -> QSlider:
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(100)
        slider.setValue(value)
        slider.setMinimumWidth(190)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(10)
        return slider

    def _build_options(self) -> QWidget:
        box = QGroupBox(t("grp.detection"))
        outer = QHBoxLayout(box)
        outer.setSpacing(24)

        audio_col = QVBoxLayout()
        self.audio_label = QLabel()
        self.audio_slider = self._slider(DEFAULT_AUDIO_THRESHOLD, 20)
        self.audio_slider.valueChanged.connect(self._on_threshold_changed)
        audio_col.addWidget(with_info(self.audio_label, t("help.audio_threshold")))
        audio_col.addWidget(self.audio_slider)
        hint = QLabel(t("lbl.audio_hint"))
        # Mittelgrau statt einer Palettenrolle: das liest sich sowohl im
        # hellen als auch im dunklen Windows-Design.
        hint.setStyleSheet("color: rgba(140,140,140,235); font-size: 11px;")
        audio_col.addWidget(hint)
        outer.addLayout(audio_col)

        meta_col = QVBoxLayout()
        self.meta_label = QLabel()
        self.meta_slider = self._slider(DEFAULT_META_THRESHOLD, 60)
        self.meta_slider.valueChanged.connect(self._on_threshold_changed)
        meta_col.addWidget(with_info(self.meta_label, t("help.meta_threshold")))
        meta_col.addWidget(self.meta_slider)
        self.meta_check = QCheckBox(t("chk.metadata"))
        self.meta_check.setChecked(True)
        self.meta_check.toggled.connect(self._on_threshold_changed)
        meta_col.addWidget(self.meta_check)
        outer.addLayout(meta_col)

        flags_col = QVBoxLayout()
        self.recursive_check = QCheckBox(t("chk.recursive"))
        self.recursive_check.setChecked(True)
        flags_col.addWidget(self.recursive_check)
        self.cache_check = QCheckBox(t("chk.cache"))
        self.cache_check.setChecked(True)
        flags_col.addWidget(self.cache_check)
        self.regroup_button = QPushButton(t("btn.regroup"))
        self.regroup_button.setToolTip(t("tip.regroup"))
        self.regroup_button.setEnabled(False)
        self.regroup_button.clicked.connect(self.regroup)
        flags_col.addWidget(self.regroup_button)
        outer.addLayout(flags_col)

        filter_col = QVBoxLayout()
        filter_col.addWidget(QLabel(t("lbl.filter")))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(t("ph.filter"))
        self.filter_edit.textChanged.connect(self._apply_filter)
        filter_col.addWidget(self.filter_edit)
        self.kind_filter = QComboBox()
        self.kind_filter.addItem(t("cmb.all_kinds"), "")
        for kind in (MATCH_IDENTICAL_FILE, MATCH_IDENTICAL_AUDIO,
                     MATCH_SAME_RECORDING, MATCH_SAME_TITLE):
            self.kind_filter.addItem(match_label(kind), kind)
        self.kind_filter.currentIndexChanged.connect(self._apply_filter)
        filter_col.addWidget(self.kind_filter)
        outer.addLayout(filter_col)

        outer.addStretch(1)

        # Zwei Nachschlagepunkte für alles, was nicht an einem einzelnen
        # Bedienelement hängt.
        info_col = QVBoxLayout()
        info_col.addWidget(with_info(
            QLabel(t("lbl.how_compared")), t("help.detection")
        ))
        info_col.addWidget(with_info(
            QLabel(t("lbl.which_keep")), t("help.recommendation")
        ))
        info_col.addStretch(1)
        outer.addLayout(info_col)

        self._on_threshold_changed()
        return box

    def _build_tabs(self) -> QWidget:
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tree(), t("tab.duplicates"))

        self.pair_tab = PairTab()
        self.pair_tab.selectionChanged.connect(self._on_selection)
        self.pair_tab.revealRequested.connect(self.reveal_selected)
        self.tabs.addTab(self.pair_tab, t("tab.pairs"))

        self.quality_tab = QualityTab()
        self.quality_tab.selectionChanged.connect(self._on_selection)
        self.quality_tab.revealRequested.connect(self.reveal_selected)
        self.tabs.addTab(self.quality_tab, t("tab.quality"))

        self.tabs.setTabToolTip(0, t("tip.tab_duplicates"))
        self.tabs.setTabToolTip(1, t("help.tab_pairs"))
        self.tabs.setTabToolTip(2, t("help.tab_quality"))
        self.tabs.currentChanged.connect(lambda _: self._on_selection())
        return self.tabs

    def _build_tree(self) -> QWidget:
        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(self.columns))
        self.tree.setHeaderLabels([name for name, _ in self.columns])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setItemDelegateForColumn(COL_QUALITY, BarDelegate(self.tree))
        self.tree.itemSelectionChanged.connect(self._on_selection)
        self.tree.itemDoubleClicked.connect(lambda *_: self.reveal_selected())

        # Jede Spaltenüberschrift erklärt sich selbst - das ist die Stelle,
        # an der man beim Lesen der Liste stutzt.
        head = self.tree.headerItem()
        for column, (key, _) in enumerate(COLUMN_KEYS):
            text = t("help." + key)
            if text != "help." + key:
                head.setToolTip(column, text)

        header = self.tree.header()
        for column, (_, width) in enumerate(self.columns):
            self.tree.setColumnWidth(column, width)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setToolTip(t("tip.headers"))
        return self.tree

    def _build_details(self) -> QWidget:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 4, 0, 0)

        row = QHBoxLayout()
        self.detail_title = QLabel(t("sel.none"))
        # Hier steht Text aus den Tags. Als reiner Text, sonst wuerde Qt
        # einen Titel wie "<b>Remix</b>" als Formatierung auslegen.
        self.detail_title.setTextFormat(Qt.PlainText)
        font = QFont()
        font.setBold(True)
        self.detail_title.setFont(font)
        row.addWidget(self.detail_title, 1)

        self.play_button = QPushButton(t("btn.play"))
        self.play_button.clicked.connect(self.play_selected)
        self.play_button.setEnabled(False)
        row.addWidget(self.play_button)

        self.reveal_button = QPushButton(t("btn.reveal"))
        self.reveal_button.clicked.connect(self.reveal_selected)
        self.reveal_button.setEnabled(False)
        row.addWidget(self.reveal_button)

        self.export_button = QPushButton(t("btn.export"))
        self.export_button.clicked.connect(self.export_csv)
        self.export_button.setEnabled(False)
        row.addWidget(self.export_button)
        layout.addLayout(row)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.detail_text)
        return frame

    # -- Einstellungen ------------------------------------------------------

    def _restore_settings(self) -> None:
        folder = self.settings.value("folder", "")
        if folder:
            self.folder_edit.setText(os.path.normpath(str(folder)))
        self.audio_slider.setValue(
            _setting_int(self.settings, "audio", DEFAULT_AUDIO_THRESHOLD)
        )
        self.meta_slider.setValue(
            _setting_int(self.settings, "meta", DEFAULT_META_THRESHOLD)
        )
        self.meta_check.setChecked(self.settings.value("use_meta", True, type=bool))
        self.recursive_check.setChecked(
            self.settings.value("recursive", True, type=bool)
        )
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt-Namensschema
        if self.worker is not None and self.worker.isRunning():
            # Erst den Hintergrundlauf sauber beenden lassen, dann schliessen.
            # Ein Thread, der beim Beenden noch laeuft, reisst das Programm
            # sonst mit einer Absturzmeldung herunter. Das Fenster schliesst
            # sich von selbst, sobald der Lauf abgebrochen ist.
            self._close_pending = True
            self.cancel_scan()
            event.ignore()
            return
        self.settings.setValue("folder", self.folder_edit.text())
        self.settings.setValue("audio", self.audio_slider.value())
        self.settings.setValue("meta", self.meta_slider.value())
        self.settings.setValue("use_meta", self.meta_check.isChecked())
        self.settings.setValue("recursive", self.recursive_check.isChecked())
        self.settings.setValue("language", self.language_setting)
        self.settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)

    def _check_tools(self) -> None:
        ok, message = tools_available()
        if not ok:
            QMessageBox.warning(self, t("msg.ffmpeg_missing"), message)
            self.scan_button.setEnabled(False)

    def choose_language(self, code: str) -> None:
        if code == self.language_setting:
            return
        self.language_setting = code
        self.settings.setValue("language", code)
        self.settings.sync()
        QMessageBox.information(self, t("msg.lang_title"), t("msg.lang_restart"))

    # -- Aktionen -----------------------------------------------------------

    def _on_threshold_changed(self) -> None:
        self.audio_label.setText(
            t("lbl.audio_threshold", value=self.audio_slider.value())
        )
        self.meta_label.setText(
            t("lbl.meta_threshold", value=self.meta_slider.value())
        )
        self.meta_slider.setEnabled(self.meta_check.isChecked())
        if self.records:
            self.regroup_button.setEnabled(True)

    def choose_folder(self) -> None:
        start = self.folder_edit.text() or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, t("dlg.choose_folder"), start)
        if folder:
            # Der Dialog liefert "V:/Musik"; angezeigt wird die Windows-Form.
            self.folder_edit.setText(os.path.normpath(folder))

    def _busy(self, busy: bool) -> None:
        self.scan_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)
        self.regroup_button.setEnabled(not busy and bool(self.records))
        self.folder_edit.setEnabled(not busy)

    def start_scan(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        root = self.folder_edit.text().strip()
        if not root or not os.path.isdir(root):
            QMessageBox.information(
                self, t("msg.no_folder_title"), t("msg.no_folder")
            )
            return

        self.tree.clear()
        self.detail_text.clear()
        self.detail_title.setText(t("sel.none"))
        self._busy(True)

        self.worker = Worker("scan", {
            "root": root,
            "recursive": self.recursive_check.isChecked(),
            "audio_threshold": self.audio_slider.value() / 100.0,
            "meta_threshold": self.meta_slider.value() / 100.0,
            "use_metadata": self.meta_check.isChecked(),
            "use_cache": self.cache_check.isChecked(),
            "cache_path": None,
        })
        self.worker.progressed.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_scan_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def regroup(self) -> None:
        if not self.records or (self.worker and self.worker.isRunning()):
            return
        self._busy(True)
        self.worker = Worker("regroup", {
            "records": self.records,
            "audio_threshold": self.audio_slider.value() / 100.0,
            "meta_threshold": self.meta_slider.value() / 100.0,
            "use_metadata": self.meta_check.isChecked(),
            "stage1": self.stage1,
        })
        self.worker.progressed.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_regroup_done)
        self.worker.cancelled.connect(self._on_regroup_cancelled)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self) -> None:
        if self._close_pending:
            self.close()

    def _on_regroup_cancelled(self) -> None:
        self._busy(False)
        self.progress.setMaximum(1)
        self.progress.setValue(0)
        self.progress.setFormat(t("state.cancelled"))

    def cancel_scan(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.request_stop()
            self.progress.setFormat(t("state.cancelling"))

    def _on_progress(self, stage: str, done: int, total: int) -> None:
        # Die Engine meldet Schlüssel, keine fertigen Sätze.
        label = t(stage)
        if total > 0:
            self.progress.setMaximum(total)
            self.progress.setValue(min(done, total))
            self.progress.setFormat(
                t("progress.of", stage=label, done=done, total=total)
            )
        else:
            self.progress.setMaximum(0)
            self.progress.setFormat(t("progress.plain", stage=label, done=done))

    def _on_failed(self, message: str) -> None:
        self._busy(False)
        self.progress.setMaximum(1)
        self.progress.setValue(0)
        self.progress.setFormat(t("state.failed"))
        QMessageBox.critical(self, t("msg.error"), message)

    def _on_scan_done(self, result) -> None:
        self._busy(False)
        self.progress.setMaximum(1)
        self.progress.setValue(1)

        if result.message and not result.records:
            self.progress.setFormat(
                t("state.cancelled") if result.cancelled else t("state.no_data")
            )
            self.status.showMessage(result.message)
            if not result.cancelled:
                QMessageBox.information(self, "MusicDupes", result.message)
            return

        self.records = result.records
        self.groups = result.groups
        self.stats = result.stats
        self.stage1 = result.stage1
        self._populate()
        self.progress.setFormat(t("state.done"))

    def _on_regroup_done(self, payload) -> None:
        self._busy(False)
        self.progress.setMaximum(1)
        self.progress.setValue(1)
        self.groups, stats = payload
        self.stats.update(stats)
        self._populate()
        self.progress.setFormat(t("state.done"))

    # -- Darstellung --------------------------------------------------------

    def _populate(self) -> None:
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()

        for number, group in enumerate(self.groups, 1):
            best_record = self.records[group.best]
            parent = QTreeWidgetItem(self.tree)
            parent.setText(
                COL_NAME,
                "{}.  {}".format(number, formatting.display_name(best_record)),
            )
            parent.setText(COL_KIND, group.label)
            parent.setText(COL_SCORE, str(len(group.members)))

            colour = QColor(KIND_COLORS.get(group.kind, "#555555"))
            parent.setForeground(COL_KIND, QBrush(colour))
            explanation = match_help(group.kind)
            if group.kind == MATCH_SAME_TITLE:
                explanation += t("tip.group_same_title")
            parent.setToolTip(COL_KIND, explanation)
            parent.setToolTip(COL_NAME, explanation)

            font = parent.font(COL_NAME)
            font.setBold(True)
            parent.setFont(COL_NAME, font)
            parent.setFont(COL_KIND, font)

            for member in group.members:
                self._add_member(parent, group, member)
            parent.setExpanded(True)

        self._add_error_section()
        self.pair_tab.populate(self.records, self.groups)
        self.quality_tab.populate(self.records)

        self.tree.setUpdatesEnabled(True)
        self.export_button.setEnabled(bool(self.groups))
        # Erst hier, nicht in _busy(): dort stehen die Ergebnisse noch nicht.
        self.regroup_button.setEnabled(bool(self.records))
        self._apply_filter()

        stats = self.stats
        message = t(
            "status.summary",
            tracks=stats.get("tracks", 0),
            cached=stats.get("from_cache", 0),
            fresh=stats.get("analyzed", 0),
            groups=len(self.groups),
            dupes=stats.get("duplicates", 0),
            versions=stats.get("versions", 0),
            wasted=formatting.filesize(redundant_bytes(self.records, self.groups)),
            seconds=stats.get("seconds", 0.0),
            workers=stats.get("workers", default_workers()),
        )
        errors = stats.get("errors", 0)
        if errors:
            message += t("status.errors", count=errors)
        self.status.showMessage(message)

    def _add_error_section(self) -> None:
        """Nicht lesbare Dateien anzeigen statt stillschweigend zu übergehen.

        Sonst hält man eine Sammlung für geprüft, in der Dateien einfach
        durchgefallen sind.
        """
        broken = [
            i for i, record in enumerate(self.records) if record.get("error")
        ]
        if not broken:
            return

        parent = QTreeWidgetItem(self.tree)
        parent.setText(COL_NAME, t("errors.header", count=len(broken)))
        parent.setText(COL_KIND, t("errors.skipped"))
        colour = QBrush(QColor("#c0392b"))
        parent.setForeground(COL_NAME, colour)
        parent.setForeground(COL_KIND, colour)
        font = parent.font(COL_NAME)
        font.setBold(True)
        parent.setFont(COL_NAME, font)

        for index in broken:
            record = self.records[index]
            item = QTreeWidgetItem(parent)
            item.setText(COL_NAME, "   " + os.path.basename(record.get("path") or ""))
            item.setText(COL_FLAGS, t(record.get("error") or ""))
            item.setText(COL_SIZE, formatting.filesize(record.get("size")))
            item.setText(COL_FOLDER, os.path.dirname(record.get("path") or ""))
            item.setForeground(COL_FLAGS, colour)
            item.setData(COL_NAME, ROLE_RECORD, index)
        parent.setExpanded(False)

    def _add_member(self, parent: QTreeWidgetItem, group, member: int) -> None:
        record = self.records[member]
        item = QTreeWidgetItem(parent)
        is_best = member == group.best

        name = os.path.basename(record.get("path") or "")
        item.setText(COL_NAME, ("* " if is_best else "   ") + name)

        acoustic = group.scores.get(member, 0.0)
        name_score = group.name_scores.get(member)
        if name_score is None:
            item.setText(COL_SCORE, "{:.0f} %".format(acoustic * 100))
        else:
            # Deutlich machen, dass hier die Beschriftung gepasst hat und
            # nicht der Klang - sonst liest sich "100 %" wie "identisch".
            item.setText(COL_SCORE, t("hits.by_name", value=name_score * 100))
            item.setForeground(COL_SCORE, QBrush(QColor(NAME_MATCH_COLOR)))
            item.setToolTip(COL_SCORE, t("tip.by_name", value=acoustic * 100))

        kind = group.kinds.get(member, "")
        item.setText(COL_KIND, match_label(kind) if kind else "")
        if kind:
            item.setToolTip(COL_KIND, match_help(kind))
        if kind == MATCH_SAME_TITLE:
            item.setForeground(COL_KIND, QBrush(QColor(NAME_MATCH_COLOR)))

        offset_seconds = group.offsets.get(member, 0.0)
        if abs(offset_seconds) >= 0.05:
            item.setToolTip(COL_OFFSET, t("tip.offset", value=offset_seconds))

        score = float(record.get("quality_score") or 0.0)
        item.setText(COL_QUALITY, "{:.0f}".format(score))
        item.setData(COL_QUALITY, ROLE_SCORE, score)

        item.setText(COL_FORMAT, (record.get("codec") or "").upper())
        if not record.get("lossless"):
            item.setToolTip(COL_FORMAT, t("tip.lossy"))
        item.setText(COL_BITRATE, formatting.bitrate(record))
        if record.get("bitrate_is_container"):
            item.setToolTip(COL_BITRATE, t("tip.container_bitrate"))
        item.setText(COL_BANDWIDTH, formatting.bandwidth(record.get("cutoff_hz")))
        item.setToolTip(COL_BANDWIDTH, t("tip.bandwidth"))
        item.setText(COL_DURATION, formatting.duration(record.get("duration")))
        item.setText(COL_SIZE, formatting.filesize(record.get("size")))
        item.setText(COL_OFFSET, formatting.offset(offset_seconds))

        flags = record.get("quality_flags") or []
        item.setText(COL_FLAGS, ", ".join(i18n.flag_texts(record)))
        notes = []
        if i18n.FLAG_TRANSCODE in flags:
            item.setForeground(COL_FLAGS, QBrush(QColor("#c0392b")))
            notes.append(t("tip.flag_transcode"))
        if i18n.FLAG_CLIPPING in flags:
            notes.append(t("tip.flag_clipping"))
        if i18n.FLAG_HIRES_EMPTY in flags:
            notes.append(t("tip.flag_hires"))
        if notes:
            item.setToolTip(COL_FLAGS, "\n\n".join(notes))

        item.setText(COL_FOLDER, os.path.dirname(record.get("path") or ""))

        for column in (COL_SCORE, COL_QUALITY, COL_BITRATE, COL_BANDWIDTH,
                       COL_DURATION, COL_SIZE, COL_OFFSET):
            item.setTextAlignment(column, Qt.AlignRight | Qt.AlignVCenter)

        item.setData(COL_NAME, ROLE_RECORD, member)

        if is_best:
            brush = QBrush(QColor(46, 160, 67, 40))
            for column in range(len(self.columns)):
                item.setBackground(column, brush)
            font = item.font(COL_NAME)
            font.setBold(True)
            item.setFont(COL_NAME, font)
            item.setToolTip(COL_NAME, t("kept.tooltip"))

    def _apply_filter(self) -> None:
        text = self.filter_edit.text().strip().lower()
        kind = self.kind_filter.currentData()
        # Das Textfeld gilt für alle Reiter.
        if hasattr(self, "quality_tab"):
            self.quality_tab.set_text_filter(text)
            self.pair_tab.set_text_filter(text)

        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            group = self.groups[i] if i < len(self.groups) else None
            kind_ok = not kind or (group is not None and group.kind == kind)

            visible_children = 0
            for j in range(parent.childCount()):
                child = parent.child(j)
                if not text:
                    match = True
                else:
                    member = child.data(COL_NAME, ROLE_RECORD)
                    match = text in formatting.search_text(self.records[member])
                child.setHidden(not (match and kind_ok))
                if match and kind_ok:
                    visible_children += 1
            parent.setHidden(visible_children == 0)

    def _current_record(self):
        """Der ausgewählte Track des gerade sichtbaren Reiters."""
        index = self.tabs.currentIndex()
        if index == 1:
            return self.pair_tab.selected_record()
        if index == 2:
            return self.quality_tab.selected_record()
        for item in self.tree.selectedItems():
            value = item.data(COL_NAME, ROLE_RECORD)
            if value is not None:
                return value
        return None

    def _on_selection(self) -> None:
        member = self._current_record()
        has_file = member is not None and 0 <= member < len(self.records)
        self.play_button.setEnabled(has_file)
        self.reveal_button.setEnabled(has_file)
        if not has_file:
            self.detail_title.setText(t("sel.none"))
            self.detail_text.clear()
            return

        record = self.records[member]
        self.detail_title.setText(formatting.display_name(record))
        self.detail_text.setHtml(self._describe(record))

    def _describe(self, record: dict) -> str:
        if record.get("error"):
            return (
                "<p style='color:#c0392b'><b>{}</b></p><p>{}</p>"
                "<p style='color:#888'>{}</p>"
            ).format(
                _escape(t("errors.detail_title")),
                _escape(t(str(record.get("error")))),
                _escape(str(record.get("path") or "")),
            )

        flags = i18n.flag_texts(record)
        channels = int(record.get("channels") or 0)
        channel_text = {1: t("val.mono"), 2: t("val.stereo")}.get(
            channels, str(channels)
        )
        rows = [
            (t("det.path"), record.get("path") or ""),
            (t("det.artist"), record.get("artist") or "-"),
            (t("det.title"), record.get("title") or "-"),
            (t("det.album"), record.get("album") or "-"),
            (t("det.duration"), formatting.duration(record.get("duration"))),
            (t("det.codec"), "{} ({})".format(
                record.get("codec") or "-", record.get("codec_long") or "")),
            (t("det.lossless"),
             t("val.yes") if record.get("lossless") else t("val.no")),
            (t("det.bitrate"), formatting.bitrate(record)),
            (t("det.samplerate"), "{} Hz".format(record.get("sample_rate") or 0)),
            (t("det.channels"), channel_text),
            (t("det.bitdepth"), str(record.get("bits_per_sample") or "-")),
            (t("det.bandwidth"), formatting.bandwidth(record.get("cutoff_hz"))),
            (t("det.peak"), "{:.1f} dBFS".format(record.get("peak_dbfs") or 0.0)),
            (t("det.rms"), "{:.1f} dBFS".format(record.get("rms_dbfs") or 0.0)),
            (t("det.clipping"), "{:.3f} %".format(
                (record.get("clip_ratio") or 0.0) * 100)),
            (t("det.score"),
             t("val.score_of", value=record.get("quality_score") or 0.0)),
            (t("det.flags"), ", ".join(flags) if flags else t("val.none")),
            (t("det.size"), formatting.filesize(record.get("size"))),
        ]
        cells = "".join(
            "<tr><td style='padding:2px 14px 2px 0;color:#888'>{}</td>"
            "<td style='padding:2px 0'>{}</td></tr>".format(key, _escape(str(value)))
            for key, value in rows
        )
        return "<table style='font-size:12px'>{}</table>".format(cells)

    # -- Dateiaktionen (nur lesend) ----------------------------------------

    def _selected_path(self) -> str:
        member = self._current_record()
        if member is None or not (0 <= member < len(self.records)):
            return ""
        return self.records[member].get("path") or ""

    def play_selected(self) -> None:
        path = self._selected_path()
        if not path or not os.path.exists(path):
            return
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, t("btn.play"), str(exc))

    def reveal_selected(self) -> None:
        path = self._selected_path()
        if not path or not os.path.exists(path):
            return
        # Voller Pfad statt nur "explorer": Windows saehe sonst zuerst im
        # Programmordner und im Arbeitsordner nach - etwa im Download-Ordner,
        # wo eine untergeschobene explorer.exe liegen koennte.
        explorer = os.path.join(
            os.environ.get("SystemRoot") or r"C:\Windows", "explorer.exe"
        )
        try:
            subprocess.Popen([explorer, "/select,", os.path.normpath(path)])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, t("btn.reveal"), str(exc))

    def export_csv(self) -> None:
        if not self.groups:
            QMessageBox.information(self, t("msg.export"), t("msg.no_results"))
            return
        start = os.path.join(
            self.folder_edit.text() or os.path.expanduser("~"), "MusicDupes.csv"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, t("dlg.save_csv"), start, t("dlg.csv_filter")
        )
        if not path:
            return
        try:
            rows = exporting.write_csv(path, self.records, self.groups)
        except OSError as exc:
            QMessageBox.critical(self, t("msg.export"), str(exc))
            return
        self.status.showMessage(t("status.csv_written", rows=rows, path=path))

    def export_quality_csv(self) -> None:
        if not self.records:
            QMessageBox.information(self, t("msg.export"), t("msg.nothing_scanned"))
            return
        start = os.path.join(
            self.folder_edit.text() or os.path.expanduser("~"),
            "MusicDupes-Quality.csv",
        )
        path, _ = QFileDialog.getSaveFileName(
            self, t("dlg.save_quality"), start, t("dlg.csv_filter")
        )
        if not path:
            return
        try:
            rows = exporting.write_quality_csv(path, self.records)
        except OSError as exc:
            QMessageBox.critical(self, t("msg.export"), str(exc))
            return
        self.status.showMessage(t("status.csv_written", rows=rows, path=path))

    def clear_cache(self) -> None:
        answer = QMessageBox.question(
            self, t("msg.clear_cache_title"),
            t("msg.clear_cache", path=default_path()),
        )
        if answer != QMessageBox.Yes:
            return
        with Cache() as cache:
            cache.clear()
        self.status.showMessage(t("status.cache_cleared"))

    def show_help(self) -> None:
        QMessageBox.information(self, t("menu.how"), t("help.dialog"))

    def show_licences(self) -> None:
        """Lizenzhinweise, mit Knopf zum Herausschreiben der Volltexte.

        Nötig wegen der Einzeldatei-Fassung: dort stecken die Lizenztexte im
        Archiv und sind sonst nicht erreichbar. Die LGPL verlangt aber, dass
        sie der Auslieferung beiliegen.
        """
        box = QMessageBox(self)
        box.setWindowTitle(t("lic.title"))
        box.setIcon(QMessageBox.Information)
        box.setText(t("lic.intro"))
        save = box.addButton(t("lic.save"), QMessageBox.ActionRole)
        box.addButton(QMessageBox.Close)
        box.exec()
        if box.clickedButton() is save:
            self._export_licences()

    def _export_licences(self) -> None:
        sources = licence_files()
        if not sources:
            QMessageBox.warning(self, t("lic.title"), t("lic.none"))
            return

        # Ordnerfassung und Quellcode: die Texte liegen schon als Dateien da,
        # Kopieren hiesse nur Doppel anlegen. Herausgeschrieben werden muss
        # nur aus der Einzeldatei, deren Inhalt beim Beenden verschwindet.
        if not is_onefile():
            folder = os.path.dirname(os.path.abspath(sources[0]))
            QMessageBox.information(
                self, t("lic.title"),
                t("lic.located", count=len(sources), path=folder),
            )
            self._open_folder(folder)
            return

        target = os.path.join(app_folder(), "licenses")
        try:
            os.makedirs(target, exist_ok=True)
            for source in sources:
                name = os.path.basename(source)
                # "LICENSE.txt" allein verriete nicht, wozu er gehoert.
                if os.path.basename(os.path.dirname(source)) == "ffmpeg":
                    name = "FFmpeg-" + name
                shutil.copy2(source, os.path.join(target, name))
        except OSError as exc:
            QMessageBox.warning(self, t("lic.title"), str(exc))
            return
        QMessageBox.information(
            self, t("lic.title"), t("lic.saved", count=len(sources), path=target)
        )
        self._open_folder(target)

    def _open_folder(self, folder: str) -> None:
        try:
            os.startfile(folder)  # type: ignore[attr-defined]
        except OSError:
            pass


def _setting_int(settings: QSettings, key: str, default: int) -> int:
    """Zahl aus der INI - eine von Hand verbogene Datei darf den Start nicht
    verhindern."""
    try:
        return int(settings.value(key, default))
    except (TypeError, ValueError):
        return default


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
