"""Detección de formatos, dimensiones y hash seguro en lectura."""
import hashlib
from pathlib import Path

IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".ico"}
AUDIO = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
VIDEO = {".mp4", ".webm", ".mkv", ".mov", ".avi"}
# Houdini prioritario; mantenemos .blend para poder catalogar recursos antiguos.
MODEL = {
    ".obj", ".fbx", ".glb", ".gltf", ".stl", ".blend",
    ".hip", ".hiplc", ".hipnc",
    ".hda", ".hdalc", ".hdanc", ".otl", ".otlc",
    ".geo", ".bgeo", ".bgeo.sc", ".geo.sc", ".sim", ".vdb",
    ".usd", ".usda", ".usdc", ".usdz", ".usdnc", ".abc"
}

def file_extension(path):
    """Path.suffix devuelve '.sc' para caches como foo.bgeo.sc."""
    lower = Path(path).name.lower()
    for extension in (".bgeo.sc", ".geo.sc"):
        if lower.endswith(extension):
            return extension
    return Path(path).suffix.lower()

DOCUMENT = {".pdf", ".doc", ".docx", ".txt", ".md", ".svg", ".psd", ".ai"}

def classify(path):
    path = Path(path)
    ext = file_extension(path)
    parent = str(path.parent).lower()
    if ext in IMAGE:
        if "icon" in parent or ext == ".ico":
            return "Icons"
        if "wallpaper" in parent or "fondo" in parent:
            return "Wallpapers"
        return "Images"
    if ext in AUDIO:
        return "Audio"
    if ext in VIDEO:
        return "Videos"
    if ext in MODEL:
        return "3D Models"
    if ext in DOCUMENT:
        return "Documents"
    return "Other"

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def image_dimensions(path):
    if Path(path).suffix.lower() not in IMAGE:
        return None, None
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size
    except (OSError, ValueError):
        return None, None

def inspect_file(path):
    path = Path(path).resolve()
    stat = path.stat()
    width, height = image_dimensions(path)
    return dict(path=str(path),name=path.name,extension=file_extension(path),
        category=classify(path),size_bytes=stat.st_size,mtime_ns=stat.st_mtime_ns,
        sha256=sha256_file(path),width=width,height=height)
