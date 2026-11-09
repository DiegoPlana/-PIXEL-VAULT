import unittest
from pixel_vault.updater import validate_release,UpdateError,version_tuple

class UpdaterTests(unittest.TestCase):
    def release(self,version="0.4.0",digest="a"*64):
        name=f"PIXEL-VAULT-Setup-{version}.exe"
        return {"tag_name":f"v{version}","draft":False,"prerelease":False,
                "assets":[{"name":name,"size":2048,"digest":"sha256:"+digest,
                 "browser_download_url":
                 "https://github.com/DiegoPlana/-PIXEL-VAULT/releases/download/v"
                 +version+"/"+name}]}
    def test_detect_new_version(self):
        data=validate_release(self.release(),current="0.3.0")
        self.assertEqual(data["version"],"0.4.0")
    def test_dont_offer_old_version(self):
        self.assertIsNone(validate_release(self.release("0.2.0"),current="0.3.0"))
    def test_mandatory_digest(self):
        with self.assertRaises(UpdateError):
            validate_release(self.release(digest="bad"),current="0.3.0")
    def test_reject_external_host(self):
        release=self.release()
        release["assets"][0]["browser_download_url"]="https://example.com/evil.exe"
        with self.assertRaises(UpdateError):
            validate_release(release,current="0.3.0")
    def test_invalid_version(self):
        with self.assertRaises(UpdateError):
            version_tuple("v1.2.3-rc1")
