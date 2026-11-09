"""Generación de vistas previas FBX fuera del hilo principal de Qt."""
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from .fbx_preview import render_fbx, cache_path

class ThumbnailWorker(QObject):
    ready = Signal(str)
    finished = Signal()
    def __init__(self, records, directory):
        super().__init__()
        self.records = list(records)
        self.directory = Path(directory)
        self.cancelled = False

    @Slot()
    def run(self):
        try:
            for record in self.records:
                if self.cancelled:
                    break
                try:
                    if not cache_path(record, self.directory).is_file():
                        render_fbx(record, self.directory)
                except Exception:
                    # FBX ilegibles o incompatibles conservan el icono fallback.
                    continue
                self.ready.emit(record["path"])
        finally:
            self.finished.emit()

    def cancel(self):
        self.cancelled = True
