"""Actualizador Windows: GitHub Releases, SHA-256 obligatorio y consentimiento."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from . import __version__

API = "https://api.github.com/repos/DiegoPlana/-PIXEL-VAULT/releases/latest"
INSTALLER_PATTERN = re.compile(r"^PIXEL-VAULT-Setup-([0-9]+\.[0-9]+\.[0-9]+)\.exe$")
MAX_INSTALLER = 220 * 1024 * 1024
MAX_METADATA = 1024 * 1024

class UpdateError(Exception):
    pass

def version_tuple(value):
    value=value.lstrip("v")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+",value):
        raise UpdateError("Versión de actualización no válida")
    return tuple(int(piece) for piece in value.split("."))

def is_installed():
    # La opción portable/fuente no se actualiza mediante instalador Inno Setup.
    if sys.platform!="win32" or not getattr(sys,"frozen",False):
        return False
    return Path(sys.executable).parent.joinpath("unins000.exe").is_file()

def _read_json(url):
    request=urllib.request.Request(url,headers={
        "Accept":"application/vnd.github+json",
        "User-Agent":"PixelVault-Updater/"+__version__,
    })
    with urllib.request.urlopen(request,timeout=12) as stream:
        raw=stream.read(MAX_METADATA+1)
    if len(raw)>MAX_METADATA:
        raise UpdateError("Respuesta de GitHub demasiado grande")
    return json.loads(raw.decode("utf-8"))

def validate_release(release, current=__version__):
    if not isinstance(release,dict) or release.get("draft") or release.get("prerelease"):
        return None
    tag=str(release.get("tag_name",""))
    version=tag.lstrip("v")
    if version_tuple(version)<=version_tuple(current):
        return None
    expected_name=f"PIXEL-VAULT-Setup-{version}.exe"
    for asset in release.get("assets",[]):
        if asset.get("name")!=expected_name:
            continue
        link=str(asset.get("browser_download_url",""))
        parsed=urlparse(link)
        if parsed.scheme!="https" or parsed.netloc.lower()!="github.com":
            raise UpdateError("El enlace de la actualización no es de GitHub")
        if not parsed.path.startswith("/DiegoPlana/-PIXEL-VAULT/releases/download/"):
            raise UpdateError("El enlace de la actualización no pertenece al proyecto")
        digest=str(asset.get("digest") or "")
        if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}",digest):
            raise UpdateError("La versión publicada no tiene un SHA-256 verificable")
        size=int(asset.get("size",0))
        if size<=0 or size>MAX_INSTALLER:
            raise UpdateError("El tamaño de la actualización es inválido")
        return {"version":version,"url":link,"sha256":digest[7:].lower(),"size":size,
                "notes":str(release.get("body",""))[:2000]}
    raise UpdateError("La versión nueva no incluye un instalador de Windows compatible")

def check_update():
    try:
        return validate_release(_read_json(API))
    except (OSError,ValueError,json.JSONDecodeError) as error:
        raise UpdateError("No se ha podido comprobar GitHub Releases: "+str(error)) from error

def download_update(info, progress=None):
    """Descarga con límites a un directorio temporal; verifica integridad antes de usar."""
    destination=Path(tempfile.mkdtemp(prefix="pixelvault-update-"))/(
        f'PIXEL-VAULT-Setup-{info["version"]}.exe')
    request=urllib.request.Request(info["url"],headers={
        "User-Agent":"PixelVault-Updater/"+__version__,
        "Accept":"application/octet-stream",
    })
    digest=hashlib.sha256()
    transferred=0
    try:
        with urllib.request.urlopen(request,timeout=25) as source, open(destination,"wb") as target:
            final=urlparse(source.geturl())
            if final.scheme!="https" or final.hostname not in (
                    "github.com","release-assets.githubusercontent.com",
                    "objects.githubusercontent.com"):
                raise UpdateError("Redirección de descarga inesperada")
            for chunk in iter(lambda:source.read(1024*1024),b""):
                transferred+=len(chunk)
                if transferred>MAX_INSTALLER or transferred>info["size"]:
                    raise UpdateError("La descarga supera el tamaño publicado")
                digest.update(chunk)
                target.write(chunk)
                if progress:
                    progress(transferred,info["size"])
        if transferred!=info["size"] or digest.hexdigest()!=info["sha256"]:
            raise UpdateError("SHA-256/tamaño incorrecto: instalador descartado")
        return destination
    except Exception:
        destination.unlink(missing_ok=True)
        raise

def launch_installer(installer):
    if not is_installed():
        raise UpdateError("Las actualizaciones desde la app requieren la versión instalada")
    # Inno Setup reutiliza el AppId y la carpeta existente. Nunca borra la biblioteca.
    flags=0
    if sys.platform=="win32":
        flags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    subprocess.Popen([
        str(installer),"/SILENT","/SUPPRESSMSGBOXES","/NORESTART",
        "/CLOSEAPPLICATIONS","/RESTARTAPPLICATIONS"
    ],close_fds=True,creationflags=flags)
