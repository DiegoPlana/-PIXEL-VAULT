"""Comprueba detección de proyectos Houdini y caches con doble extensión."""
import unittest
from pixel_vault.media import classify, file_extension

class HoudiniFormatTests(unittest.TestCase):
    def test_houdini_projects(self):
        for path in ("scene.hip","scene.hiplc","scene.hipnc","tool.hda","tool.hdalc",
                     "tool.hdanc","tool.otl","geometry.vdb","usd.usdc","mesh.abc"):
            with self.subTest(path=path):
                self.assertEqual(classify(path),"3D Models")
    def test_compressed_geometry(self):
        self.assertEqual(file_extension("frame.1001.bgeo.sc"),".bgeo.sc")
        self.assertEqual(classify("frame.1001.bgeo.sc"),"3D Models")
        self.assertEqual(file_extension("geo.geo.sc"),".geo.sc")
        self.assertEqual(classify("geo.geo.sc"),"3D Models")
    def test_blender_is_still_readable(self):
        self.assertEqual(classify("old_asset.blend"),"3D Models")

if __name__ == "__main__":
    unittest.main()
