"""Inicio de PIXEL VAULT con icono de escritorio propio."""
import sys
from pathlib import Path
from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from . import storage
from .ui import MainWindow

def resource_path(relative):
    # PyInstaller unpacks --add-data into sys._MEIPASS.
    root = Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[2]))
    return root / relative

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PIXEL VAULT")
    app.setOrganizationName("PixelVault")
    icon = resource_path("assets/pixelvault.png")
    if icon.is_file():
        app.setWindowIcon(QIcon(str(icon)))
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    db = Path(location) / "pixelvault.db"
    storage.initialize(db)
    window = MainWindow(db)
    window.show()
    raise SystemExit(app.exec())
