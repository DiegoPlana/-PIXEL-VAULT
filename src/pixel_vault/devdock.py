"""Integración local de solo lectura con DEVDОCK (Electron + node:sqlite)."""
import os
import sqlite3
from pathlib import Path

def candidate_databases():
    home = Path.home()
    appdata = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    paths = [
        appdata / "devdock" / "devdock.sqlite",
        appdata / "DEVDОCK" / "devdock.sqlite",
        xdg / "devdock" / "devdock.sqlite",
        xdg / "DEVDОCK" / "devdock.sqlite",
        home / "Library" / "Application Support" / "devdock" / "devdock.sqlite",
    ]
    return list(dict.fromkeys(paths))

def find_database(custom_path=None):
    if custom_path:
        candidate = Path(custom_path).expanduser()
        return candidate if candidate.is_file() else None
    return next((path for path in candidate_databases() if path.is_file()), None)

def list_projects(database_path):
    """DevDock schema: projects(id,name,root_path,category). Never write to this DB."""
    if not database_path:
        return []
    path = Path(database_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    uri = path.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=3) as db:
        db.row_factory = sqlite3.Row
        data = db.execute(
            "SELECT id,name,root_path,category FROM projects ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [dict(row) for row in data if row["root_path"]]

def project_for_path(path, projects):
    """Match deepest encompassing project folder; never match sibling prefixes."""
    path = os.path.normcase(os.path.abspath(str(path)))
    matches = []
    for project in projects:
        root = os.path.normcase(os.path.abspath(project["root_path"]))
        try:
            if os.path.commonpath([path, root]) == root:
                matches.append((len(root), project))
        except ValueError:
            continue
    return max(matches, default=(0, None), key=lambda pair: pair[0])[1]
