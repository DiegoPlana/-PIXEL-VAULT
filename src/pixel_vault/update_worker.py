"""Consulta y descarga actualizaciones sin bloquear la interfaz Qt."""
from PySide6.QtCore import QObject, Signal, Slot
from .updater import check_update, download_update

class UpdateWorker(QObject):
    result = Signal(object)
    error = Signal(str)
    done = Signal()
    progress = Signal(int)
    def __init__(self, mode="check", info=None):
        super().__init__()
        self.mode=mode
        self.info=info
    @Slot()
    def run(self):
        try:
            if self.mode=="check":
                self.result.emit(check_update())
            else:
                path=download_update(self.info,progress=lambda current,total:
                    self.progress.emit(int(current*100/total)))
                self.result.emit(str(path))
        except Exception as error:
            self.error.emit(str(error))
        finally:
            self.done.emit()
