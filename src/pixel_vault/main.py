"""Punto de entrada de la aplicación Qt."""
import sys
from pathlib import Path
from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication
from . import storage
from .ui import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PixelVault")
    app.setOrganizationName("PixelVault")
    root = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    database = root / "pixelvault.db"
    storage.initialize(database)
    window = MainWindow(database)
    window.show()
    raise SystemExit(app.exec())
