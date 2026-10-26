"""Ablaufsteuerung: suchen, analysieren, gruppieren.

Die Analyse laeuft in echten Prozessen, nicht in Threads: das Dekodieren ist
CPU-Arbeit und Pythons GIL wuerde bei Threads jeden Kern ausser einem
brachliegen lassen. Ein Ryzen mit 16 Threads spielt hier seine Staerke aus -
eine GPU dagegen nicht, weil die Arbeit aus vielen kleinen, seriellen
Dekodierschritten besteht und nicht aus einer grossen Matrixmultiplikation.
"""

from __future__ import annotations

import os
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import audio, matcher, scanner
from .i18n import t
from .analysis import analyze_file
from .cache import Cache


def default_workers() -> int:
    cpus = os.cpu_count() or 4
    # Ein Worker je CPU-Thread. Mehr bringt nichts, weil jeder Worker zudem
    # sein ffmpeg auslastet; die Obergrenze schuetzt den Arbeitsspeicher.
    return max(1, min(cpus, 32))


@dataclass
class ScanResult:
    records: list = field(default_factory=list)
    groups: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    cancelled: bool = False
    message: str = ""
    # Zwischenergebnis der Kandidatensuche, fuer "Neu gruppieren".
    stage1: dict = field(default_factory=dict)


class Cancelled(Exception):
    pass


class ScanEngine:
    """Fuehrt einen kompletten Durchlauf aus."""

    def __init__(self, cache_path: Optional[str] = None) -> None:
        self.cache_path = cache_path
        self.workers = default_workers()

    def scan(
        self,
        root: str,
        recursive: bool = True,
        audio_threshold: float = 0.90,
        meta_threshold: float = 0.82,
        use_metadata: bool = True,
        use_cache: bool = True,
        progress: Optional[Callable] = None,
        should_stop: Optional[Callable] = None,
    ) -> ScanResult:

        def report(stage: str, done: int, total: int) -> None:
            if progress is not None:
                progress(stage, done, total)

        def check() -> None:
            if should_stop is not None and should_stop():
                raise Cancelled()

        ok, message = audio.tools_available()
        if not ok:
            return ScanResult(message=message)
        # Ein Ordner, eine Schreibweise. Der Auswahldialog liefert "V:/Musik",
        # eingetippt heisst es "V:\Musik" - ohne Angleichung waeren das fuer
        # den Cache verschiedene Dateien, und alles wuerde neu analysiert.
        root = os.path.abspath(root)
        if not os.path.isdir(root):
            return ScanResult(message=t("engine.no_folder", path=root))

        result = ScanResult()
        started = time.perf_counter()

        try:
            # -- Dateien suchen -----------------------------------------
            report("stage.find_files", 0, 0)
            found = []
            for entry in scanner.find_audio_files(root, recursive, should_stop):
                found.append(entry)
                if len(found) % 200 == 0:
                    report("stage.find_files", len(found), 0)
            check()
            report("stage.find_files", len(found), len(found))

            if not found:
                result.message = t("engine.no_files")
                result.stats = {"tracks": 0}
                return result

            paths = [item[0] for item in found]

            # -- Was ist schon bekannt? ---------------------------------
            with Cache(self.cache_path) as cache:
                fresh = cache.fresh_paths(found) if use_cache else set()
                records = list(cache.load(fresh)) if fresh else []
                known = {rec["path"] for rec in records}
                todo = [p for p in paths if p not in known]

            report("stage.analyze", len(records), len(paths))

            # -- Analysieren --------------------------------------------
            if todo:
                fresh_records = self._analyze(
                    todo, len(records), len(paths), report, check
                )
                records.extend(fresh_records)
                with Cache(self.cache_path) as cache:
                    cache.store_many(fresh_records)

            check()

            # -- Gruppieren ---------------------------------------------
            def group_progress(stage: str, done: int, total: int) -> None:
                report(stage, done, total)
                check()

            groups, stats = matcher.build_groups(
                records,
                audio_threshold=audio_threshold,
                meta_threshold=meta_threshold,
                use_metadata=use_metadata,
                progress=group_progress,
                stage1_cache=result.stage1,
            )

            stats["seconds"] = time.perf_counter() - started
            stats["from_cache"] = len(records) - len(todo)
            stats["analyzed"] = len(todo)
            stats["workers"] = self.workers

            result.records = records
            result.groups = groups
            result.stats = stats
            return result

        except Cancelled:
            result.cancelled = True
            result.message = t("engine.cancelled")
            return result

    def _analyze(
        self,
        paths: list,
        offset: int,
        total: int,
        report: Callable,
        check: Callable,
    ) -> list:
        """Verteilt die Dateien auf Worker-Prozesse."""
        results: list = []
        executor = ProcessPoolExecutor(max_workers=self.workers)
        # Future -> Pfad: stirbt ein Worker, gehoert der Fehler trotzdem zur
        # richtigen Datei und nicht zu einem namenlosen Eintrag.
        pending: dict = {}
        try:
            queue = iter(paths)
            # Nicht alles auf einmal einreihen: so bleibt ein Abbruch schnell.
            for path in queue:
                pending[executor.submit(analyze_file, path)] = path
                if len(pending) >= self.workers * 4:
                    break

            while pending:
                done, _rest = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    path = pending.pop(future)
                    try:
                        results.append(future.result())
                    except Exception:  # noqa: BLE001
                        results.append({
                            "path": path, "error": "engine.worker_failed",
                        })
                    report(
                        "stage.analyze", offset + len(results), total
                    )

                try:
                    check()
                except Exception:
                    for future in pending:
                        future.cancel()
                    raise

                for _ in range(len(done)):
                    try:
                        path = next(queue)
                    except StopIteration:
                        break
                    pending[executor.submit(analyze_file, path)] = path
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        return results
