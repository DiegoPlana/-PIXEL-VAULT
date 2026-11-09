"""Interfaz oscura de biblioteca creativa. No elimina archivos originales."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, QThread, QUrl, QSize
from PySide6.QtGui import QDesktopServices, QPixmap, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFileDialog, QLineEdit, QComboBox, QSplitter, QMessageBox,
    QFormLayout, QTextEdit, QCheckBox, QInputDialog, QProgressBar, QScrollArea,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from . import storage
from .importer import ImportWorker
from .media import IMAGE, AUDIO, VIDEO

CSS = """
QWidget { background:#0b1020; color:#e8f2ff; font: 13px 'Segoe UI'; }
QMainWindow { background:#090e1c; }
QPushButton { background:#182740; border:1px solid #344965; border-radius:7px;
 padding:9px 12px; }
QPushButton:hover { background:#224263; border-color:#00c8ea; }
QLineEdit,QComboBox,QTextEdit,QListWidget { background:#121d31; border:1px solid #33465f;
 border-radius:6px; padding:6px; selection-background-color:#186b88; }
QLabel#heading { font-size:23px; font-weight:bold; color:#5fe5ff; }
QLabel#muted { color:#9bb2cb; }
QProgressBar { background:#162238; border:0; border-radius:5px; }
QProgressBar::chunk { background:#18bedc; border-radius:5px; }
"""

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected = None
        self.offset = 0
        self.section = "all"
        self.collection_id = None
        self.thread = None
        self.worker = None
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.setWindowTitle("PIXEL VAULT · Creative Library")
        self.resize(1280, 780)
        self.setStyleSheet(CSS)
        self.build()
        self.reload()

    def build(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        top = QHBoxLayout()
        title = QLabel("◈ PIXEL VAULT")
        title.setObjectName("heading")
        top.addWidget(title)
        top.addStretch(1)
        for name, action in [
            ("+ Archivos", self.import_files),
            ("+ Carpeta", self.import_folder),
            ("↻ Comprobar archivos", self.refresh_files),
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(action)
            top.addWidget(btn)
        layout.addLayout(top)

        search_bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar recursos, etiquetas, extensiones...")
        self.search.textChanged.connect(self.search_changed)
        search_bar.addWidget(self.search, 3)
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self.search_changed)
        search_bar.addWidget(self.category_filter, 1)
        self.sort = QComboBox()
        self.sort.addItems(["Recientes", "Nombre A-Z", "Nombre Z-A", "Mayor tamaño"])
        self.sort.currentTextChanged.connect(self.search_changed)
        search_bar.addWidget(self.sort, 1)
        layout.addLayout(search_bar)

        splitter = QSplitter()
        layout.addWidget(splitter, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("NAVEGACIÓN"))
        self.navigation = QListWidget()
        for label, key in [("Todos los recursos","all"),("Favoritos","favorites"),
                           ("Duplicados exactos","duplicates"),("No disponibles","missing")]:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, ("section",key))
            self.navigation.addItem(item)
        self.navigation.currentItemChanged.connect(self.change_navigation)
        left_layout.addWidget(self.navigation)
        left_layout.addWidget(QLabel("COLECCIONES"))
        self.collections_list = QListWidget()
        self.collections_list.currentItemChanged.connect(self.change_collection)
        left_layout.addWidget(self.collections_list)
        new_collection = QPushButton("+ Crear colección")
        new_collection.clicked.connect(self.create_collection)
        left_layout.addWidget(new_collection)
        splitter.addWidget(left)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        self.overview = QLabel()
        self.overview.setObjectName("muted")
        center_layout.addWidget(self.overview)
        self.assets = QListWidget()
        self.assets.setViewMode(QListWidget.ViewMode.IconMode)
        self.assets.setIconSize(QSize(104,104))
        self.assets.setGridSize(QSize(156,150))
        self.assets.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.assets.setMovement(QListWidget.Movement.Static)
        self.assets.currentItemChanged.connect(self.select_asset)
        self.assets.itemDoubleClicked.connect(lambda item: self.open_original())
        center_layout.addWidget(self.assets)
        pagination = QHBoxLayout()
        self.page_label = QLabel("")
        prev_btn = QPushButton("Anterior")
        next_btn = QPushButton("Siguiente")
        prev_btn.clicked.connect(lambda: self.change_page(-1))
        next_btn.clicked.connect(lambda: self.change_page(1))
        pagination.addWidget(prev_btn)
        pagination.addWidget(self.page_label)
        pagination.addWidget(next_btn)
        center_layout.addLayout(pagination)
        splitter.addWidget(center)

        right = QWidget()
        details = QVBoxLayout(right)
        details.addWidget(QLabel("DETALLES DEL RECURSO"))
        self.preview = QLabel("Selecciona un archivo")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(220)
        self.preview.setWordWrap(True)
        details.addWidget(self.preview)
        self.video = QVideoWidget()
        self.video.setMinimumHeight(190)
        self.video.hide()
        self.player.setVideoOutput(self.video)
        details.addWidget(self.video)
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setObjectName("muted")
        details.addWidget(self.path_label)
        form = QFormLayout()
        self.category_edit = QLineEdit()
        self.tags_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(70)
        self.favorite = QCheckBox("Favorito")
        form.addRow("Categoría",self.category_edit)
        form.addRow("Etiquetas (comas)",self.tags_edit)
        form.addRow("Descripción",self.description_edit)
        form.addRow("",self.favorite)
        details.addLayout(form)
        for label, handler in [
            ("Guardar cambios", self.save_selected),
            ("Abrir original", self.open_original),
            ("Mostrar en carpeta", self.open_folder),
            ("Añadir a colección", self.assign_collection),
            ("Quitar de biblioteca", self.remove_selected),
        ]:
            button = QPushButton(label)
            button.clicked.connect(handler)
            details.addWidget(button)
        self.play_button = QPushButton("▶ Reproducir / Pausar")
        self.play_button.clicked.connect(self.toggle_play)
        details.addWidget(self.play_button)
        details.addStretch()
        splitter.addWidget(right)
        splitter.setSizes([200,780,300])

        bottom = QHBoxLayout()
        self.status = QLabel("Listo")
        bottom.addWidget(self.status,1)
        self.progress = QProgressBar()
        self.progress.setRange(0,0)
        self.progress.hide()
        bottom.addWidget(self.progress)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.cancel_import)
        self.cancel_button.hide()
        bottom.addWidget(self.cancel_button)
        layout.addLayout(bottom)

    def search_changed(self, *_):
        self.offset = 0
        self.reload_assets()

    def reload(self):
        current = self.category_filter.currentText()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItems(["Todas"] + storage.categories(self.db))
        index = self.category_filter.findText(current)
        if index >= 0:
            self.category_filter.setCurrentIndex(index)
        self.category_filter.blockSignals(False)
        self.collections_list.blockSignals(True)
        self.collections_list.clear()
        for col in storage.collections(self.db):
            item = QListWidgetItem(col["name"])
            item.setData(Qt.ItemDataRole.UserRole,col["id"])
            self.collections_list.addItem(item)
        self.collections_list.blockSignals(False)
        totals = storage.stats(self.db)
        self.status.setText(
            f'{totals["count"]} recursos · {totals["bytes"]/(1024**2):.1f} MB referenciados · '
            f'{totals["duplicates"]} grupos duplicados · {totals["missing"]} no disponibles'
        )
        self.reload_assets()

    def reload_assets(self):
        category = self.category_filter.currentText()
        rows, total = storage.fetch_assets(
            self.db,query=self.search.text(),category=category,
            section=self.section,collection=self.collection_id,
            sort=self.sort.currentText(),limit=160,offset=self.offset)
        self.assets.blockSignals(True)
        self.assets.clear()
        self.selected = None
        for row in rows:
            item = QListWidgetItem(row["name"])
            item.setToolTip(row["path"])
            item.setData(Qt.ItemDataRole.UserRole,row)
            if row["extension"] in IMAGE and Path(row["path"]).is_file():
                pixmap = QPixmap(row["path"])
                if not pixmap.isNull():
                    item.setIcon(QIcon(pixmap.scaled(
                        QSize(104,104),Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)))
            self.assets.addItem(item)
        self.assets.blockSignals(False)
        self.page_label.setText(f'{self.offset+1 if total else 0}–{min(self.offset+160,total)} de {total}')
        self.overview.setText(f'{total} resultados · Biblioteca local')
        self.preview.setText("Selecciona un archivo")
        self.path_label.clear()

    def change_page(self, direction):
        _, total = storage.fetch_assets(self.db,query=self.search.text(),
            category=self.category_filter.currentText(),section=self.section,
            collection=self.collection_id,limit=1)
        new_offset = max(0,self.offset+direction*160)
        if new_offset < total or new_offset == 0:
            self.offset = new_offset
            self.reload_assets()

    def change_navigation(self, current, previous):
        if current is None:
            return
        self.section = current.data(Qt.ItemDataRole.UserRole)[1]
        self.collection_id = None
        self.collections_list.blockSignals(True)
        self.collections_list.clearSelection()
        self.collections_list.blockSignals(False)
        self.search_changed()

    def change_collection(self, current, previous):
        if current is None:
            return
        self.collection_id = current.data(Qt.ItemDataRole.UserRole)
        self.section = "all"
        self.navigation.blockSignals(True)
        self.navigation.clearSelection()
        self.navigation.blockSignals(False)
        self.search_changed()

    def select_asset(self, current, previous):
        self.player.stop()
        self.video.hide()
        if current is None:
            self.selected = None
            return
        row = current.data(Qt.ItemDataRole.UserRole)
        self.selected = row
        path = Path(row["path"])
        self.path_label.setText(
            f'{row["name"]}\n{row["path"]}\n{row["size_bytes"]:,} bytes'
            + (f' · {row["width"]}×{row["height"]}' if row["width"] else "")
            + ("\nARCHIVO NO DISPONIBLE" if not path.is_file() else ""))
        self.category_edit.setText(row["category"])
        self.tags_edit.setText(", ".join(storage.tags_for(self.db,row["id"])))
        self.description_edit.setPlainText(row["description"])
        self.favorite.setChecked(bool(row["favorite"]))
        self.preview.setPixmap(QPixmap())
        if path.is_file() and row["extension"] in IMAGE:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.preview.setPixmap(pixmap.scaled(QSize(275,240),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))
                return
        self.preview.setText(row["extension"].upper().lstrip(".") or "FILE")
        if path.is_file() and row["extension"] in AUDIO | VIDEO:
            self.player.setSource(QUrl.fromLocalFile(str(path)))
            if row["extension"] in VIDEO:
                self.video.show()

    def save_selected(self):
        if self.selected is None:
            return
        storage.save_asset(self.db,self.selected["id"],self.favorite.isChecked(),
            self.category_edit.text(),self.description_edit.toPlainText(),
            self.tags_edit.text().split(","))
        self.reload()

    def open_original(self):
        if self.selected:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.selected["path"]))

    def open_folder(self):
        if self.selected:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.selected["path"]).parent)))

    def remove_selected(self):
        if self.selected is None:
            return
        answer = QMessageBox.question(self,"Confirmar",
            "¿Quitar este registro de la biblioteca? El archivo original NO se borrará.")
        if answer == QMessageBox.StandardButton.Yes:
            storage.remove_asset(self.db,self.selected["id"])
            self.reload()

    def create_collection(self):
        name, ok = QInputDialog.getText(self,"Nueva colección","Nombre:")
        if ok and name.strip():
            try:
                storage.create_collection(self.db,name)
                self.reload()
            except Exception as error:
                QMessageBox.warning(self,"Colección",str(error))

    def assign_collection(self):
        if self.selected is None:
            return
        cols = storage.collections(self.db)
        if not cols:
            QMessageBox.information(self,"Colecciones","Crea una colección primero.")
            return
        names = [c["name"] for c in cols]
        name, ok = QInputDialog.getItem(self,"Colección","Añadir a:",names,0,False)
        if ok:
            idx = names.index(name)
            storage.add_to_collection(self.db,cols[idx]["id"],self.selected["id"])
            self.reload()

    def toggle_play(self):
        if self.selected is None or self.selected["extension"] not in AUDIO | VIDEO:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def import_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self,"Importar recursos")
        if paths:
            self.begin_import(paths)

    def import_folder(self):
        path = QFileDialog.getExistingDirectory(self,"Importar carpeta")
        if path:
            self.begin_import([path])

    def refresh_files(self):
        self.begin_import([],refresh=True)

    def begin_import(self, paths, refresh=False):
        if self.thread is not None:
            return
        self.thread = QThread(self)
        self.worker = ImportWorker(self.db,paths,refresh)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(lambda n,name: self.status.setText(f"Procesados {n}: {name}"))
        self.worker.finished.connect(self.finish_import)
        self.worker.failed.connect(self.fail_import)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.clear_thread)
        self.progress.show()
        self.cancel_button.show()
        self.thread.start()

    def finish_import(self, result):
        self.progress.hide()
        self.cancel_button.hide()
        self.reload()
        QMessageBox.information(self,"Importación",str(result))

    def fail_import(self, reason):
        self.progress.hide()
        self.cancel_button.hide()
        QMessageBox.warning(self,"Error al importar",reason)

    def clear_thread(self):
        self.thread = None
        self.worker = None

    def cancel_import(self):
        if self.worker:
            self.worker.cancel()
            self.status.setText("Cancelando después del archivo actual...")

    def closeEvent(self,event):
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self,"Importación activa",
                "Cancela la importación y espera a que termine antes de salir.")
            event.ignore()
            return
        self.player.stop()
        event.accept()
