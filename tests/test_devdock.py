import sqlite3
import tempfile
import unittest
from pathlib import Path
from pixel_vault.devdock import list_projects, project_for_path

class DevdockTests(unittest.TestCase):
    def test_readonly_project_link(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory) / "devdock.sqlite"
            with sqlite3.connect(db) as connection:
                connection.execute("""CREATE TABLE projects (
                    id TEXT,name TEXT,root_path TEXT,category TEXT)""")
                connection.execute("""INSERT INTO projects VALUES
                    ('1','Umbra','C:/Projects/Umbra','Game')""")
            projects=list_projects(db)
            self.assertEqual(projects[0]["name"],"Umbra")
            self.assertEqual(project_for_path("C:/Projects/Umbra/Content/test.png",projects)["name"],"Umbra")
            self.assertIsNone(project_for_path("C:/Projects/Umbra2/test.png",projects))
            with sqlite3.connect(db) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0],1)
