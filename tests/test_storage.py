import tempfile
import unittest
from pathlib import Path
from pixel_vault import storage
from pixel_vault.media import classify, inspect_file

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "catalog.sqlite"
        storage.initialize(self.db)
        self.asset = self.root / "example.txt"
        self.asset.write_text("hola",encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_and_search(self):
        data = inspect_file(self.asset)
        self.assertTrue(storage.upsert(self.db,data))
        self.assertFalse(storage.upsert(self.db,data))
        rows,total = storage.fetch_assets(self.db,query="example")
        self.assertEqual(total,1)
        self.assertEqual(rows[0]["category"],"Documents")

    def test_favorites_tags_and_collections(self):
        storage.upsert(self.db,inspect_file(self.asset))
        rows,_ = storage.fetch_assets(self.db)
        aid = rows[0]["id"]
        storage.save_asset(self.db,aid,True,"References","Prueba",["test","art"])
        self.assertEqual(storage.tags_for(self.db,aid),["art","test"])
        self.assertEqual(storage.fetch_assets(self.db,section="favorites")[1],1)
        storage.create_collection(self.db,"Mi proyecto")
        cid = storage.collections(self.db)[0]["id"]
        storage.add_to_collection(self.db,cid,aid)
        self.assertEqual(storage.fetch_assets(self.db,collection=cid)[1],1)
        storage.remove_asset(self.db,aid)
        self.assertTrue(self.asset.exists())

    def test_duplicates(self):
        second = self.root / "second.txt"
        second.write_text("hola",encoding="utf-8")
        storage.upsert(self.db,inspect_file(self.asset))
        storage.upsert(self.db,inspect_file(second))
        self.assertEqual(storage.stats(self.db)["duplicates"],1)
        self.assertEqual(storage.fetch_assets(self.db,section="duplicates")[1],2)

    def test_missing(self):
        storage.upsert(self.db,inspect_file(self.asset))
        storage.set_missing(self.db,self.asset,True)
        self.assertEqual(storage.fetch_assets(self.db,section="missing")[1],1)

if __name__ == "__main__":
    unittest.main()
