"""SQLite: catálogo de archivos sin tocar sus originales."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
 id INTEGER PRIMARY KEY,
 path TEXT NOT NULL UNIQUE,
 name TEXT NOT NULL,
 extension TEXT NOT NULL,
 category TEXT NOT NULL DEFAULT 'Other',
 size_bytes INTEGER NOT NULL DEFAULT 0,
 mtime_ns INTEGER NOT NULL DEFAULT 0,
 sha256 TEXT,
 width INTEGER,
 height INTEGER,
 favorite INTEGER NOT NULL DEFAULT 0,
 description TEXT NOT NULL DEFAULT '',
 missing INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tags (
 id INTEGER PRIMARY KEY,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS asset_tags (
 asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
 tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
 PRIMARY KEY(asset_id, tag_id)
);
CREATE TABLE IF NOT EXISTS collections (
 id INTEGER PRIMARY KEY,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS collection_assets (
 collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
 asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
 PRIMARY KEY(collection_id, asset_id)
);
CREATE INDEX IF NOT EXISTS assets_hash_idx ON assets(sha256);
CREATE INDEX IF NOT EXISTS assets_cat_idx ON assets(category);
"""

@contextmanager
def connect(path):
    """Siempre confirmar/revertir y CERRAR SQLite (también en Windows)."""
    connection = sqlite3.connect(str(path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript(SCHEMA)

def upsert(path, data):
    with connect(path) as db:
        previous = db.execute("SELECT id FROM assets WHERE path=?", (data["path"],)).fetchone()
        if previous:
            db.execute("""UPDATE assets SET name=?, extension=?, size_bytes=?,
                mtime_ns=?, sha256=?, width=?, height=?, missing=0 WHERE path=?""",
                (data["name"], data["extension"], data["size_bytes"], data["mtime_ns"],
                 data["sha256"], data["width"], data["height"], data["path"]))
            return False
        db.execute("""INSERT INTO assets(path,name,extension,category,size_bytes,mtime_ns,sha256,width,height)
            VALUES (:path,:name,:extension,:category,:size_bytes,:mtime_ns,:sha256,:width,:height)""", data)
        return True

SORTS = {
    "Recientes": "a.id DESC",
    "Nombre A-Z": "a.name COLLATE NOCASE ASC",
    "Nombre Z-A": "a.name COLLATE NOCASE DESC",
    "Mayor tamaño": "a.size_bytes DESC",
}

def fetch_assets(path, query="", category="", section="all", collection=None, sort="Recientes", limit=160, offset=0, extension="", project_root=""):
    clauses, params = [], []
    if query.strip():
        clauses.append("""(a.name LIKE ? OR a.extension LIKE ? OR a.description LIKE ?
           OR EXISTS (SELECT 1 FROM asset_tags at JOIN tags t ON t.id=at.tag_id
           WHERE at.asset_id=a.id AND t.name LIKE ?))""")
        params += ["%" + query.strip() + "%"] * 4
    if extension and extension != "Todos":
        clauses.append("a.extension=?")
        params.append(extension)
    if project_root:
        import os
        root = os.path.normcase(os.path.normpath(project_root))
        root = root.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        clauses.append("a.path LIKE ? ESCAPE '!'")
        params.append(root.rstrip("/\\") + os.sep + "%")
    if category and category != "Todas":
        clauses.append("a.category=?")
        params.append(category)
    if section == "favorites":
        clauses.append("a.favorite=1")
    if section == "missing":
        clauses.append("a.missing=1")
    if section == "duplicates":
        clauses.append("a.sha256 IS NOT NULL AND EXISTS (SELECT 1 FROM assets b WHERE b.sha256=a.sha256 AND b.id<>a.id)")
    if collection is not None:
        clauses.append("EXISTS (SELECT 1 FROM collection_assets ca WHERE ca.asset_id=a.id AND ca.collection_id=?)")
        params.append(collection)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect(path) as db:
        total = db.execute("SELECT COUNT(*) FROM assets a" + where, params).fetchone()[0]
        rows = db.execute("SELECT a.* FROM assets a" + where + " ORDER BY " +
            SORTS.get(sort, SORTS["Recientes"]) + " LIMIT ? OFFSET ?",
            params + [limit,offset]).fetchall()
    return [dict(row) for row in rows], total

def categories(path):
    with connect(path) as db:
        return [row[0] for row in db.execute("SELECT DISTINCT category FROM assets ORDER BY category COLLATE NOCASE")]

def tags_for(path, asset_id):
    with connect(path) as db:
        return [r[0] for r in db.execute("""SELECT t.name FROM tags t JOIN asset_tags x
                ON x.tag_id=t.id WHERE x.asset_id=? ORDER BY t.name""", (asset_id,))]

def save_asset(path, asset_id, favorite, category, description, tags):
    with connect(path) as db:
        db.execute("UPDATE assets SET favorite=?,category=?,description=? WHERE id=?",
                   (int(favorite), category.strip() or "Other", description, asset_id))
        db.execute("DELETE FROM asset_tags WHERE asset_id=?", (asset_id,))
        for tag in sorted({t.strip()[:60] for t in tags if t.strip()}):
            db.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
            db.execute("""INSERT OR IGNORE INTO asset_tags(asset_id,tag_id)
                SELECT ?,id FROM tags WHERE name=? COLLATE NOCASE""", (asset_id,tag))

def remove_asset(path, asset_id):
    with connect(path) as db:
        db.execute("DELETE FROM assets WHERE id=?", (asset_id,))

def collections(path):
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT * FROM collections ORDER BY name")]

def create_collection(path, name):
    with connect(path) as db:
        db.execute("INSERT INTO collections(name) VALUES (?)", (name.strip(),))

def add_to_collection(path, collection_id, asset_id):
    with connect(path) as db:
        db.execute("INSERT OR IGNORE INTO collection_assets VALUES (?,?)", (collection_id,asset_id))

def stats(path):
    with connect(path) as db:
        totals = dict(db.execute("""SELECT COUNT(*) count, COALESCE(SUM(size_bytes),0) bytes,
            COALESCE(SUM(missing),0) missing FROM assets""").fetchone())
        totals["duplicates"] = db.execute("""SELECT COUNT(*) FROM
           (SELECT sha256 FROM assets WHERE sha256 IS NOT NULL GROUP BY sha256 HAVING COUNT(*) > 1)""").fetchone()[0]
        return totals

def set_missing(path, file_path, missing):
    with connect(path) as db:
        db.execute("UPDATE assets SET missing=? WHERE path=?", (int(missing), str(Path(file_path).resolve())))

def extensions(path):
    with connect(path) as db:
        return [row[0] for row in db.execute(
            "SELECT DISTINCT extension FROM assets WHERE extension != '' ORDER BY extension")]

def bulk_favorite(path, ids, favorite=True):
    clean = sorted({int(item) for item in ids if int(item) > 0})
    if not clean:
        return 0
    with connect(path) as db:
        db.executemany("UPDATE assets SET favorite=? WHERE id=?",
                       [(int(favorite), item) for item in clean])
    return len(clean)

def bulk_remove(path, ids):
    clean = sorted({int(item) for item in ids if int(item) > 0})
    if not clean:
        return 0
    with connect(path) as db:
        db.executemany("DELETE FROM assets WHERE id=?", [(item,) for item in clean])
    return len(clean)

def bulk_to_collection(path, collection_id, ids):
    clean = sorted({int(item) for item in ids if int(item) > 0})
    with connect(path) as db:
        db.executemany("INSERT OR IGNORE INTO collection_assets(collection_id,asset_id) VALUES (?,?)",
                       [(collection_id, item) for item in clean])
    return len(clean)

def bulk_tags(path, ids, tags):
    clean_ids = sorted({int(item) for item in ids if int(item) > 0})
    clean_tags = sorted({tag.strip()[:60] for tag in tags if tag.strip()})
    with connect(path) as db:
        for tag in clean_tags:
            db.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
            db.executemany("""INSERT OR IGNORE INTO asset_tags(asset_id, tag_id)
                SELECT ?, id FROM tags WHERE name=? COLLATE NOCASE""",
                [(item, tag) for item in clean_ids])
    return len(clean_ids)
