"""PIXEL VAULT — interfaz editorial de biblioteca creativa."""
import os
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QThread, QUrl, QSettings
from PySide6.QtGui import QDesktopServices, QPixmap, QGuiApplication, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFileDialog, QLineEdit, QComboBox, QSplitter,
    QMessageBox, QFormLayout, QTextEdit, QCheckBox, QInputDialog, QProgressBar,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMenu,
    QAbstractItemView, QFrame
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from . import storage, devdock
from .importer import ImportWorker
from .media import IMAGE, AUDIO, VIDEO
from .visuals import icon_for_asset

# Warm editorial design: far away from the blue/cyan developer-console UI.
STYLE = """
QWidget { background: #F7F3EC; color: #322436; font-family: 'Segoe UI'; font-size: 13px; }
QMainWindow { background: #F7F3EC; }
QWidget#topbar { background: #2D1B35; }
QWidget#topbar QLabel { background: transparent; color: #FAF1E7; }
QLabel#brand { font-weight: 800; font-size: 22px; color: #FFCE9B; letter-spacing: 1px; }
QLabel#eyebrow { color: #A46E72; font-size: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#sectionTitle { color: #39243C; font-weight: 800; font-size: 21px; }
QLabel#muted { color: #847588; }
QLabel#count { color: #745B70; font-size: 12px; }
QFrame#sidebar { background: #EDE4DC; border: none; border-radius: 12px; }
QFrame#detailPanel { background: #FFFCF7; border: 1px solid #E8D9CE; border-radius: 12px; }
QFrame#sidebar QLabel, QFrame#detailPanel QLabel { background: transparent; }
QFrame#sidebar QCheckBox, QFrame#detailPanel QCheckBox { background: transparent; }
QPushButton { padding: 9px 12px; background: #FFFDF8; border: 1px solid #DCCEC7;
 border-radius: 9px; font-weight: 600; }
QPushButton:hover { background: #FFE7D7; border-color: #D77A67; }
QPushButton#accent { background: #E87561; color: #231521; border-color: #E87561; font-weight: 800; }
QPushButton#accent:hover { background: #F69A77; }
QPushButton#viewActive { background: #38213D; color: #FFF1E3; border-color: #38213D; }
QLineEdit, QComboBox, QTextEdit { background: #FFFCF7; border: 1px solid #D8CAC5;
 border-radius: 9px; padding: 8px; selection-background-color: #E87561; }
QLineEdit:focus, QTextEdit:focus { border-color: #E87561; }
QListWidget { border: 1px solid #E5D5CA; border-radius: 10px; background: #FFFDF8;
 padding: 4px; outline: none; }
QFrame#sidebar QListWidget { background: #EDE4DC; border: none; }
QListWidget::item { border-radius: 9px; padding: 5px; }
QListWidget::item:selected { background: #F6C9B1; color: #2D1B35; }
QListWidget::item:hover { background: #F9E3D3; }
QTableWidget { background: #FFFDF8; alternate-background-color: #F8F1EB;
 gridline-color: #EFE4DC; border: 1px solid #E5D5CA; border-radius: 10px;
 selection-background-color: #F6C9B1; selection-color: #2D1B35; }
QHeaderView::section { background: #F1E7DD; color: #604A60; padding: 8px;
 border: 0px; border-bottom: 1px solid #DCCEC7; font-weight: 700; }
QMenu { background: #FFFCF7; border: 1px solid #DCCEC7; padding: 4px; }
QMenu::item { padding: 7px 16px; }
QMenu::item:selected { background: #F6C9B1; color: #2D1B35; }
QProgressBar { background: #E9DBD1; border: 0; border-radius: 6px; }
QProgressBar::chunk { background: #E87561; border-radius: 6px; }
QSplitter::handle { background: transparent; width: 6px; }
QToolTip { background: #322436; color: #FFF1E3; }
"""

class MainWindow(QMainWindow):
    PAGE_SIZE = 120

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.selected = None
        self.rows = []
        self.section = "all"
        self.collection_id = None
        self.project_root = ""
        self.offset = 0
        self.thread = None
        self.worker = None
        self.settings = QSettings("PixelVault", "PixelVault")
        self.cache = Path(db).parent / "thumbnails"
        self.devdock_db = devdock.find_database(self.settings.value("devdock_db", ""))
        self.devdock_projects = []
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.player.setAudioOutput(self.output)
        self.setWindowTitle("PIXEL VAULT — Creative Asset Library")
        self.setAcceptDrops(True)
        self.setMinimumSize(1000, 680)
        self.resize(1480, 900)
        self.setStyleSheet(STYLE)
        self.build_ui()
        self.reload_projects()
        self.load_library()
        self.set_view(self.settings.value("view", "grid"))

    def action_button(self, label, handler, style=None):
        btn = QPushButton(label)
        if style:
            btn.setObjectName(style)
        btn.clicked.connect(handler)
        return btn

    def build_ui(self):
        outer = QWidget()
        self.setCentralWidget(outer)
        root = QVBoxLayout(outer)
        root.setContentsMargins(12, 0, 12, 8)
        root.setSpacing(12)
        header = QWidget()
        header.setObjectName("topbar")
        header.setStyleSheet("QWidget#topbar{border-radius: 0px 0px 16px 16px;}")
        row = QHBoxLayout(header)
        row.setContentsMargins(22, 14, 22, 14)
        heading = QLabel("◒  PIXEL VAULT")
        heading.setObjectName("brand")
        row.addWidget(heading)
        tagline = QLabel("YOUR CREATIVE UNIVERSE   /   LOCAL ARCHIVE")
        tagline.setStyleSheet("color:#D9B6B3; font-size:10px; letter-spacing:2px;")
        row.addSpacing(18)
        row.addWidget(tagline)
        row.addStretch()
        row.addWidget(self.action_button("＋ Archivos", self.import_files))
        row.addWidget(self.action_button("＋ Carpeta", self.import_folder, "accent"))
        row.addWidget(self.action_button("↻ Actualizar", self.refresh_files))
        root.addWidget(header)

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar en tu universo: archivo, etiqueta, descripción…")
        self.search.textChanged.connect(self.filter_changed)
        toolbar.addWidget(self.search, 4)
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self.filter_changed)
        toolbar.addWidget(self.category_filter, 1)
        self.extension_filter = QComboBox()
        self.extension_filter.currentTextChanged.connect(self.filter_changed)
        toolbar.addWidget(self.extension_filter, 1)
        self.sort = QComboBox()
        self.sort.addItems(["Recientes","Nombre A-Z","Nombre Z-A","Mayor tamaño"])
        self.sort.currentTextChanged.connect(self.filter_changed)
        toolbar.addWidget(self.sort, 1)
        self.grid_btn = self.action_button("▦ Galería", lambda: self.set_view("grid"))
        self.list_btn = self.action_button("☷ Lista", lambda: self.set_view("list"))
        toolbar.addWidget(self.grid_btn)
        toolbar.addWidget(self.list_btn)
        root.addLayout(toolbar)

        main = QSplitter()
        root.addWidget(main, 1)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12,16,12,12)
        nav_caption = QLabel("EXPLORAR")
        nav_caption.setObjectName("eyebrow")
        side.addWidget(nav_caption)
        self.navigation = QListWidget()
        for title, key in [
            ("◈  Biblioteca completa", "all"),
            ("♥  Favoritos", "favorites"),
            ("⊞  Duplicados exactos", "duplicates"),
            ("⚑  No disponibles", "missing"),
        ]:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.navigation.addItem(item)
        self.navigation.currentItemChanged.connect(self.navigation_changed)
        side.addWidget(self.navigation, 2)
        label = QLabel("COLECCIONES")
        label.setObjectName("eyebrow")
        side.addWidget(label)
        self.collections_list = QListWidget()
        self.collections_list.currentItemChanged.connect(self.collection_changed)
        side.addWidget(self.collections_list, 2)
        side.addWidget(self.action_button("+ Nueva colección", self.create_collection))
        label = QLabel("PROYECTOS DEVDOCK")
        label.setObjectName("eyebrow")
        side.addWidget(label)
        self.projects_list = QListWidget()
        self.projects_list.currentItemChanged.connect(self.project_changed)
        side.addWidget(self.projects_list, 2)
        side.addWidget(self.action_button("↗ Conectar DEVDOCK", self.configure_devdock))
        side.addWidget(self.action_button("Importar proyecto", self.import_project))
        main.addWidget(sidebar)

        middle = QWidget()
        mid = QVBoxLayout(middle)
        mid.setContentsMargins(4,0,4,0)
        top = QHBoxLayout()
        self.title = QLabel("Tu biblioteca")
        self.title.setObjectName("sectionTitle")
        top.addWidget(self.title)
        top.addStretch()
        self.count_label = QLabel()
        self.count_label.setObjectName("count")
        top.addWidget(self.count_label)
        mid.addLayout(top)
        self.view_stack = QStackedWidget()
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.ViewMode.IconMode)
        self.gallery.setIconSize(QSize(168,124))
        self.gallery.setGridSize(QSize(200,190))
        self.gallery.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.gallery.setMovement(QListWidget.Movement.Static)
        self.gallery.setWordWrap(True)
        self.gallery.setSpacing(7)
        self.gallery.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.gallery.itemSelectionChanged.connect(self.on_gallery_selection)
        self.gallery.itemDoubleClicked.connect(lambda _: self.open_original())
        self.gallery.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.gallery.customContextMenuRequested.connect(self.gallery_menu)
        self.view_stack.addWidget(self.gallery)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["RECURSO","TIPO","CATEGORÍA","TAMAÑO","MODIFICADO","UBICACIÓN"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setIconSize(QSize(30,30))
        self.table.verticalHeader().setDefaultSectionSize(43)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5,QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self.on_table_selection)
        self.table.cellDoubleClicked.connect(lambda r,c: self.open_original())
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.table_menu)
        self.view_stack.addWidget(self.table)
        mid.addWidget(self.view_stack,1)
        foot = QHBoxLayout()
        foot.addWidget(self.action_button("← Anterior", lambda: self.change_page(-1)))
        foot.addStretch()
        self.page_label = QLabel()
        self.page_label.setObjectName("muted")
        foot.addWidget(self.page_label)
        foot.addStretch()
        foot.addWidget(self.action_button("Siguiente →", lambda: self.change_page(1)))
        mid.addLayout(foot)
        main.addWidget(middle)

        detail_frame = QFrame()
        detail_frame.setObjectName("detailPanel")
        details = QVBoxLayout(detail_frame)
        details.setContentsMargins(15,16,15,16)
        label = QLabel("EN FOCO  /  INSPECTOR")
        label.setObjectName("eyebrow")
        details.addWidget(label)
        self.preview = QLabel("Selecciona un recurso para explorarlo")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setWordWrap(True)
        self.preview.setMinimumHeight(215)
        self.preview.setStyleSheet("background:#F3E9DF; border-radius:12px; padding:12px;")
        details.addWidget(self.preview)
        self.video = QVideoWidget()
        self.video.setMinimumHeight(170)
        self.video.hide()
        details.addWidget(self.video)
        self.player.setVideoOutput(self.video)
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setObjectName("muted")
        details.addWidget(self.path_label)
        form = QFormLayout()
        self.category_edit = QLineEdit()
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("arte, personaje, proyecto…")
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(75)
        self.favorite = QCheckBox("♥ Favorito")
        form.addRow("Categoría", self.category_edit)
        form.addRow("Etiquetas", self.tags_edit)
        form.addRow("Nota", self.description_edit)
        form.addRow("", self.favorite)
        details.addLayout(form)
        details.addWidget(self.action_button("Guardar cambios", self.save_selected,"accent"))
        buttons = QHBoxLayout()
        buttons.addWidget(self.action_button("Abrir",self.open_original))
        buttons.addWidget(self.action_button("Carpeta",self.open_folder))
        buttons.addWidget(self.action_button("Copiar ruta",self.copy_path))
        details.addLayout(buttons)
        details.addWidget(self.action_button("＋ Añadir a colección",self.assign_collection))
        details.addWidget(self.action_button("▶ Reproducir / Pausar", self.toggle_play))
        details.addWidget(self.action_button("Quitar de biblioteca (no borra archivo)",self.remove_selected))
        details.addStretch()
        main.addWidget(detail_frame)
        main.setSizes([218,930,306])

        bottom = QHBoxLayout()
        self.status = QLabel()
        self.status.setObjectName("muted")
        bottom.addWidget(self.status, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0,0)
        self.progress.hide()
        bottom.addWidget(self.progress)
        self.cancel_btn = self.action_button("Cancelar importación", self.cancel_import)
        self.cancel_btn.hide()
        bottom.addWidget(self.cancel_btn)
        root.addLayout(bottom)

    def set_view(self, mode):
        mode = "list" if mode == "list" else "grid"
        self.view_stack.setCurrentIndex(1 if mode == "list" else 0)
        self.grid_btn.setObjectName("viewActive" if mode == "grid" else "")
        self.list_btn.setObjectName("viewActive" if mode == "list" else "")
        for widget in (self.grid_btn,self.list_btn):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.settings.setValue("view",mode)
        self.show_rows()

    def filter_changed(self, *_):
        self.offset = 0
        self.load_assets()

    def load_library(self):
        current_category = self.category_filter.currentText()
        current_ext = self.extension_filter.currentText()
        for widget, values, current in [
            (self.category_filter,["Todas"] + storage.categories(self.db),current_category),
            (self.extension_filter,["Todos"] + storage.extensions(self.db),current_ext)
        ]:
            widget.blockSignals(True)
            widget.clear()
            widget.addItems(values)
            if widget.findText(current) >= 0:
                widget.setCurrentText(current)
            widget.blockSignals(False)
        self.collections_list.blockSignals(True)
        self.collections_list.clear()
        for collection in storage.collections(self.db):
            item = QListWidgetItem("◌  " + collection["name"])
            item.setData(Qt.ItemDataRole.UserRole,collection["id"])
            self.collections_list.addItem(item)
        self.collections_list.blockSignals(False)
        summary = storage.stats(self.db)
        self.status.setText(
            f'{summary["count"]} recursos · {summary["bytes"]/1024**2:.1f} MB indexados · '
            f'{summary["duplicates"]} grupos repetidos · {summary["missing"]} sin localizar')
        self.load_assets()

    def load_assets(self):
        self.rows,self.total = storage.fetch_assets(
            self.db, query=self.search.text(), category=self.category_filter.currentText(),
            section=self.section,collection=self.collection_id, sort=self.sort.currentText(),
            offset=self.offset,limit=self.PAGE_SIZE,
            extension=self.extension_filter.currentText(),project_root=self.project_root)
        self.show_rows()
        start = self.offset+1 if self.total else 0
        self.page_label.setText(f'{start}–{min(self.offset+self.PAGE_SIZE,self.total)} / {self.total}')
        self.count_label.setText(f'{self.total} RECURSOS')

    def show_rows(self):
        self.selected = None
        self.player.stop()
        self.video.hide()
        self.preview.setPixmap(QPixmap())
        self.preview.setText("Selecciona un recurso para explorarlo")
        self.path_label.clear()
        self.gallery.blockSignals(True)
        self.table.blockSignals(True)
        self.gallery.clear()
        self.table.setRowCount(len(self.rows))
        for index,asset in enumerate(self.rows):
            img = icon_for_asset(asset,self.cache, QSize(168,124))
            item = QListWidgetItem(img,asset["name"])
            item.setToolTip(asset["path"])
            item.setData(Qt.ItemDataRole.UserRole,asset)
            self.gallery.addItem(item)
            values = [asset["name"],asset["extension"].upper() or "FILE",
                      asset["category"],self.human_size(asset["size_bytes"]),
                      self.mtime(asset["mtime_ns"]),asset["path"]]
            for column,value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setData(Qt.ItemDataRole.UserRole,asset)
                if column == 0:
                    cell.setIcon(icon_for_asset(asset,self.cache,QSize(36,36)))
                self.table.setItem(index,column,cell)
        self.gallery.blockSignals(False)
        self.table.blockSignals(False)

    @staticmethod
    def human_size(value):
        for unit in ("B","KB","MB","GB","TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024

    @staticmethod
    def mtime(ns):
        from datetime import datetime
        try:
            return datetime.fromtimestamp(ns / 1_000_000_000).strftime("%d/%m/%Y")
        except (ValueError,OverflowError,OSError):
            return "—"

    def current_ids(self):
        if self.view_stack.currentIndex() == 0:
            return [item.data(Qt.ItemDataRole.UserRole)["id"] for item in self.gallery.selectedItems()]
        return [self.rows[i] ["id"] for i in sorted({index.row() for index in self.table.selectedIndexes()})]

    def selection_changed(self, rows):
        self.player.stop()
        self.video.hide()
        if not rows:
            self.selected = None
            return
        self.show_details(rows[0])

    def on_gallery_selection(self):
        self.selection_changed([item.data(Qt.ItemDataRole.UserRole) for item in self.gallery.selectedItems()])

    def on_table_selection(self):
        indices = sorted({index.row() for index in self.table.selectedIndexes()})
        self.selection_changed([self.rows[i] for i in indices])

    def show_details(self, asset):
        self.selected = asset
        file_path = Path(asset["path"])
        self.category_edit.setText(asset["category"])
        self.tags_edit.setText(", ".join(storage.tags_for(self.db,asset["id"])))
        self.description_edit.setPlainText(asset["description"])
        self.favorite.setChecked(bool(asset["favorite"]))
        self.path_label.setText(
            f'{asset["name"]}\n{self.human_size(asset["size_bytes"])} · '
            f'{asset["extension"].upper() or "ARCHIVO"}\n'
            f'{asset["width"]}×{asset["height"]} px\n' if asset["width"] else
            f'{asset["name"]}\n{self.human_size(asset["size_bytes"])} · '
            f'{asset["extension"].upper() or "ARCHIVO"}\n'
        )
        self.path_label.setText(self.path_label.text() + asset["path"] +
            ("\n⚠ El archivo ya no está en esta ubicación" if not file_path.is_file() else ""))
        self.preview.setText("")
        self.preview.setPixmap(icon_for_asset(asset,self.cache,QSize(280,210)).pixmap(QSize(280,210)))
        if file_path.is_file() and asset["extension"] in AUDIO | VIDEO:
            self.player.setSource(QUrl.fromLocalFile(str(file_path)))
            if asset["extension"] in VIDEO:
                self.video.show()

    def navigation_changed(self,current,previous):
        if current is None:return
        self.section = current.data(Qt.ItemDataRole.UserRole)
        self.collection_id = None
        self.project_root = ""
        self.collections_list.blockSignals(True)
        self.collections_list.clearSelection()
        self.collections_list.blockSignals(False)
        self.projects_list.blockSignals(True)
        self.projects_list.clearSelection()
        self.projects_list.blockSignals(False)
        self.title.setText({"all":"Tu biblioteca","favorites":"Tus favoritos",
            "duplicates":"Duplicados exactos","missing":"Recursos no disponibles"}[self.section])
        self.filter_changed()

    def collection_changed(self,current,previous):
        if current is None:return
        self.collection_id = current.data(Qt.ItemDataRole.UserRole)
        self.section = "all"
        self.project_root = ""
        self.navigation.blockSignals(True)
        self.navigation.clearSelection()
        self.navigation.blockSignals(False)
        self.projects_list.blockSignals(True)
        self.projects_list.clearSelection()
        self.projects_list.blockSignals(False)
        self.title.setText(current.text().replace("◌  ",""))
        self.filter_changed()

    def project_changed(self,current,previous):
        if current is None:return
        project = current.data(Qt.ItemDataRole.UserRole)
        self.project_root = project["root_path"]
        self.section = "all"
        self.collection_id = None
        for widget in (self.navigation,self.collections_list):
            widget.blockSignals(True)
            widget.clearSelection()
            widget.blockSignals(False)
        self.title.setText("Proyecto / " + project["name"])
        self.filter_changed()

    def change_page(self,direction):
        offset = max(0,self.offset+direction*self.PAGE_SIZE)
        if offset < self.total or offset == 0:
            self.offset = offset
            self.load_assets()

    def save_selected(self):
        if not self.selected:return
        storage.save_asset(self.db,self.selected["id"],self.favorite.isChecked(),
            self.category_edit.text(),self.description_edit.toPlainText(),
            self.tags_edit.text().split(","))
        self.load_library()

    def open_original(self):
        if self.selected and Path(self.selected["path"]).is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.selected["path"]))

    def open_folder(self):
        if self.selected:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.selected["path"]).parent)))

    def copy_path(self):
        if self.selected:
            QGuiApplication.clipboard().setText(self.selected["path"])

    def remove_selected(self):
        ids = self.current_ids()
        if not ids and self.selected:
            ids = [self.selected["id"]]
        if not ids:return
        reply=QMessageBox.question(self,"Confirmar",
            f'¿Quitar {len(ids)} registro(s)? Los archivos originales NO se borrarán.')
        if reply == QMessageBox.StandardButton.Yes:
            storage.bulk_remove(self.db,ids)
            self.load_library()

    def create_collection(self):
        name,ok = QInputDialog.getText(self,"Crear colección","Nombre")
        if ok and name.strip():
            try:
                storage.create_collection(self.db,name)
                self.load_library()
            except Exception as error:
                QMessageBox.warning(self,"Colección",str(error))

    def assign_collection(self):
        ids = self.current_ids()
        if not ids and self.selected: ids=[self.selected["id"]]
        cols = storage.collections(self.db)
        if not ids:return
        if not cols:
            QMessageBox.information(self,"Colecciones","Crea una colección primero.")
            return
        names = [col["name"] for col in cols]
        name,ok = QInputDialog.getItem(self,"Asignar a colección","Destino",names,0,False)
        if ok:
            storage.bulk_to_collection(self.db,cols[names.index(name)]["id"],ids)
            self.status.setText(f'{len(ids)} recurso(s) añadidos a {name}')

    def add_tags_bulk(self):
        ids=self.current_ids()
        if not ids:return
        tags,ok=QInputDialog.getText(self,"Etiquetar recursos","Etiquetas separadas por comas:")
        if ok and tags.strip():
            storage.bulk_tags(self.db,ids,tags.split(","))
            self.load_assets()

    def favorite_bulk(self):
        ids=self.current_ids()
        if ids:
            storage.bulk_favorite(self.db,ids)
            self.load_library()

    def toggle_play(self):
        if not self.selected or self.selected["extension"] not in AUDIO | VIDEO:return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def make_context_menu(self,global_pos):
        menu=QMenu(self)
        menu.addAction("Abrir archivo",self.open_original)
        menu.addAction("Mostrar carpeta",self.open_folder)
        menu.addAction("Copiar ruta",self.copy_path)
        menu.addSeparator()
        menu.addAction("♥ Marcar favoritos (selección)",self.favorite_bulk)
        menu.addAction("＋ Etiquetar selección",self.add_tags_bulk)
        menu.addAction("＋ Añadir a colección",self.assign_collection)
        menu.addSeparator()
        menu.addAction("Quitar selección de la biblioteca",self.remove_selected)
        menu.exec(global_pos)

    def gallery_menu(self,pos):
        item=self.gallery.itemAt(pos)
        if not item:return
        if not item.isSelected():
            self.gallery.clearSelection()
            item.setSelected(True)
        self.make_context_menu(self.gallery.viewport().mapToGlobal(pos))

    def table_menu(self,pos):
        item=self.table.itemAt(pos)
        if not item:return
        if not item.isSelected():
            self.table.clearSelection()
            self.table.selectRow(item.row())
        self.make_context_menu(self.table.viewport().mapToGlobal(pos))

    def reload_projects(self):
        self.projects_list.blockSignals(True)
        self.projects_list.clear()
        try:
            self.devdock_projects = devdock.list_projects(self.devdock_db)
            for project in self.devdock_projects:
                item=QListWidgetItem("⌁  " + project["name"])
                item.setToolTip(project["root_path"])
                item.setData(Qt.ItemDataRole.UserRole,project)
                self.projects_list.addItem(item)
        except Exception as error:
            self.devdock_projects=[]
            self.status.setText("DEVDOCK: " + str(error))
        self.projects_list.blockSignals(False)

    def configure_devdock(self):
        path,_ = QFileDialog.getOpenFileName(self,
            "Selecciona devdock.sqlite (solo lectura)",str(Path.home()),
            "Bases SQLite (*.sqlite *.db);;Todos los archivos (*)")
        if path:
            try:
                projects=devdock.list_projects(path)
            except Exception as error:
                QMessageBox.warning(self,"DEVDOCK","No se pudo leer la base: " + str(error))
                return
            self.settings.setValue("devdock_db",path)
            self.devdock_db=Path(path)
            self.reload_projects()
            QMessageBox.information(self,"DEVDOCK",
                f'Conectado en modo solo lectura. {len(projects)} proyectos disponibles.')

    def import_project(self):
        item=self.projects_list.currentItem()
        if item is None:
            QMessageBox.information(self,"DEVDOCK","Selecciona primero un proyecto.")
            return
        path=item.data(Qt.ItemDataRole.UserRole)["root_path"]
        if not Path(path).is_dir():
            QMessageBox.warning(self,"Proyecto","No se encuentra la carpeta.")
            return
        if QMessageBox.question(self,"Importar proyecto",
            f'¿Indexar archivos de {path}? Esto puede tardar si contiene muchos archivos. '
            "No se modificarán los originales.") == QMessageBox.StandardButton.Yes:
            self.start_import([path])

    def import_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,"Añadir recursos")
        if paths:self.start_import(paths)

    def import_folder(self):
        path=QFileDialog.getExistingDirectory(self,"Añadir carpeta")
        if path:self.start_import([path])

    def refresh_files(self):
        self.start_import([],refresh=True)

    def start_import(self,paths,refresh=False):
        if self.thread is not None:return
        self.thread=QThread(self)
        self.worker=ImportWorker(self.db,paths,refresh)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(lambda n,name:self.status.setText(f'{n} archivos procesados · {name}'))
        self.worker.finished.connect(self.import_complete)
        self.worker.failed.connect(self.import_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.clear_worker)
        self.progress.show()
        self.cancel_btn.show()
        self.thread.start()

    def import_complete(self,result):
        self.progress.hide()
        self.cancel_btn.hide()
        self.load_library()
        QMessageBox.information(self,"Importación finalizada",
            f'Añadidos: {result["added"]}\nActualizados: {result["updated"]}\n'
            f'No disponibles: {result["missing"]}\nErrores: {result["errors"]}')

    def import_failed(self,error):
        self.progress.hide()
        self.cancel_btn.hide()
        QMessageBox.warning(self,"Error al importar",error)

    def clear_worker(self):
        self.thread=None
        self.worker=None

    def cancel_import(self):
        if self.worker:
            self.worker.cancel()
            self.status.setText("Cancelando tras el archivo actual…")

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self,event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.start_import(paths)
            event.acceptProposedAction()

    def closeEvent(self,event):
        if self.thread is not None and self.thread.isRunning():
            QMessageBox.information(self,"Importación activa",
                "Cancela la importación y espera a que termine antes de cerrar.")
            event.ignore()
            return
        self.player.stop()
        event.accept()
