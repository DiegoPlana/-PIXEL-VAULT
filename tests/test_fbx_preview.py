import tempfile
import unittest
from pixel_vault.fbx_preview import render_mesh,cache_path

class FBXThumbnailTests(unittest.TestCase):
    def test_mesh_renders_pixels(self):
        vertices=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]
        faces=[(vertices[0],vertices[1],vertices[2]),
               (vertices[0],vertices[2],vertices[3])]
        image=render_mesh(vertices,faces,(240,180))
        self.assertEqual(image.size,(240,180))
        self.assertNotEqual(image.getpixel((120,90)),image.getpixel((20,20)))
    def test_cache_invalidation(self):
        record={"path":"C:/model.fbx","size_bytes":100,"mtime_ns":1}
        with tempfile.TemporaryDirectory() as directory:
            key=cache_path(record,directory)
            record["mtime_ns"]=2
            self.assertNotEqual(key,cache_path(record,directory))

if __name__=="__main__":
    unittest.main()
