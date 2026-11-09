"""Importador en QThread: progreso, cancelación y errores aislados."""
import os
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from .media import inspect_file
from . import storage

class ImportWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, db_path, paths=(), refresh=False):
        super().__init__()
        self.db_path = db_path
        self.paths = [Path(p) for p in paths]
        self.refresh = refresh
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def scan(self):
        if self.refresh:
            with storage.connect(self.db_path) as db:
                paths = [Path(row[0]) for row in db.execute("SELECT path FROM assets")]
            yield from paths
            return
        seen = set()
        for entry in self.paths:
            if self.cancelled:
                return
            if entry.is_file():
                candidates = [entry]
            elif entry.is_dir():
                candidates = (
                    Path(root) / filename
                    for root, dirs, filenames in os.walk(entry, followlinks=False)
                    for filename in filenames
                )
            else:
                continue
            for candidate in candidates:
                if self.cancelled:
                    return
                try:
                    if not candidate.is_file():
                        continue
                    path = candidate.resolve()
                    if str(path) not in seen:
                        seen.add(str(path))
                        yield path
                except OSError:
                    continue

    @Slot()
    def run(self):
        results = {"added":0, "updated":0, "missing":0, "errors":0}
        try:
            for number, path in enumerate(self.scan(), 1):
                if self.cancelled:
                    break
                try:
                    if self.refresh and not path.is_file():
                        storage.set_missing(self.db_path, path, True)
                        results["missing"] += 1
                    else:
                        info = inspect_file(path)
                        added = storage.upsert(self.db_path, info)
                        results["added" if added else "updated"] += 1
                except (OSError, ValueError, PermissionError):
                    results["errors"] += 1
                if number % 10 == 0:
                    self.progress.emit(number, str(path.name))
            results["cancelled"] = self.cancelled
            self.finished.emit(results)
        except Exception as error:
            self.failed.emit(str(error))
