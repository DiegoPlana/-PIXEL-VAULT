"""Iconos de documentos generados con QPainter y miniaturas en caché."""
import hashlib
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QPen, QFont, QPainterPath
from .media import IMAGE, AUDIO, VIDEO, MODEL

COLORS = {
    "code": ("#4F46E5", "#F4F0FF"), "image": ("#DD6B57", "#FFF2E9"),
    "audio": ("#AE458A", "#F9EBF4"), "video": ("#336D75", "#E4F6EF"),
    "3d": ("#D59134", "#FFF3DE"), "pdf": ("#BE4E49", "#FFF2E8"),
    "doc": ("#527A60", "#ECF5E8"), "archive": ("#976D37", "#F8F0E2"),
    "misc": ("#6A647B", "#F0EDF3"),
}
CODE = {".py",".cpp",".h",".hpp",".c",".cs",".js",".jsx",".ts",".tsx",".java",".rs",
        ".go",".php",".css",".html",".json",".xml",".yaml",".yml",".sh",".bat",".sql"}
ARCHIVES = {".zip",".rar",".7z",".tar",".gz"}

def file_kind(extension):
    ext = extension.lower()
    if ext in IMAGE: return "image"
    if ext in AUDIO: return "audio"
    if ext in VIDEO: return "video"
    if ext in MODEL: return "3d"
    if ext in CODE: return "code"
    if ext == ".pdf": return "pdf"
    if ext in {".doc",".docx",".txt",".md",".odt"}: return "doc"
    if ext in ARCHIVES: return "archive"
    return "misc"

def placeholder(extension, size=QSize(168, 124)):
    """Vector-style thumbnail with extension badge, no dependence on OS icons."""
    kind = file_kind(extension)
    ink, paper = COLORS[kind]
    image = QPixmap(size)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    w, h = size.width(), size.height()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(paper))
    painter.drawRoundedRect(0, 0, w, h, 14, 14)
    painter.setBrush(QColor(ink))
    painter.drawRoundedRect(int(w*0.31), int(h*0.16), int(w*0.38), int(h*0.55), 12, 12)
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Segoe UI", max(11, int(h/6)))
    font.setBold(True)
    painter.setFont(font)
    label = {"audio":"♫", "video":"▶", "image":"◈", "3d":"3D",
             "code":"</>", "pdf":"PDF", "doc":"DOC", "archive":"ZIP"}.get(kind,"FILE")
    painter.drawText(int(w*0.2),int(h*0.16),int(w*0.6),int(h*0.54),
                     Qt.AlignmentFlag.AlignCenter,label)
    painter.setPen(QColor(ink))
    font.setPointSize(max(8,int(h/11)))
    painter.setFont(font)
    painter.drawText(0,int(h*0.76),w,int(h*0.19),Qt.AlignmentFlag.AlignCenter,
                     (extension.lstrip(".") or "FILE").upper()[:12])
    painter.end()
    return image

def thumbnail(record, cache_dir, size=QSize(168,124)):
    ext = record["extension"]
    filename = Path(record["path"])
    if ext == ".fbx" and filename.is_file():
        from .fbx_preview import cache_path
        image = cache_path(record, cache_dir)
        if image.is_file():
            preview = QPixmap(str(image))
            if not preview.isNull():
                return preview.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        return placeholder(ext,size)
    if ext not in IMAGE or not filename.is_file():
        return placeholder(ext,size)
    cache_dir = Path(cache_dir)
    identity = f'{record["path"]}|{record["size_bytes"]}|{record["mtime_ns"]}'
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{key}.png"
    pixmap = QPixmap(str(cache_file)) if cache_file.is_file() else QPixmap()
    if pixmap.isNull():
        # QImageReader decodes a scaled version where the format supports it.
        from PySide6.QtGui import QImageReader
        reader = QImageReader(str(filename))
        reader.setAutoTransform(True)
        original_size = reader.size()
        if original_size.isValid():
            reader.setScaledSize(original_size.scaled(size*2,
                Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():
            return placeholder(ext,size)
        pixmap = QPixmap.fromImage(image)
        try:
            cache_dir.mkdir(parents=True,exist_ok=True)
            pixmap.save(str(cache_file),"PNG")
        except OSError:
            pass
    return pixmap.scaled(size,Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)

def icon_for_asset(record, cache_dir, size=QSize(168,124)):
    return QIcon(thumbnail(record,cache_dir,size))
