import tempfile
import unittest
from pathlib import Path
from pixel_vault import storage
from pixel_vault.media import inspect_file

class BulkTests(unittest.TestCase):
    def test_bulk_actions_and_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            db=root/"test.sqlite"
            storage.initialize(db)
            files=[root/"alpha.py",root/"beta.txt"]
            for item in files:
                item.write_text("hola",encoding="utf-8")
                storage.upsert(db,inspect_file(item))
            rows,_=storage.fetch_assets(db)
            ids=[r["id"] for r in rows]
            storage.bulk_favorite(db,ids)
            self.assertEqual(storage.fetch_assets(db,section="favorites")[1],2)
            storage.bulk_tags(db,ids,["proyecto","work"])
            self.assertEqual(storage.fetch_assets(db,query="proyecto")[1],2)
            self.assertEqual(storage.fetch_assets(db,extension=".py")[1],1)
            storage.create_collection(db,"Tareas")
            cid=storage.collections(db)[0]["id"]
            storage.bulk_to_collection(db,cid,ids)
            self.assertEqual(storage.fetch_assets(db,collection=cid)[1],2)
            storage.bulk_remove(db,ids)
            self.assertTrue(all(f.exists() for f in files))
            self.assertEqual(storage.stats(db)["count"],0)
