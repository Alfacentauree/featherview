import os
import tempfile
import unittest
from PIL import Image

from featherview.metadata import format_bytes, get_image_metadata


class TestMetadata(unittest.TestCase):

    def test_format_bytes(self):
        self.assertEqual(format_bytes(500), "500 B")
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 3.5), "3.50 MB")

    def test_image_metadata_extraction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "sample.png")
            # Create a 200x100 sample PNG
            img = Image.new("RGB", (200, 100), color=(255, 0, 0))
            img.save(img_path)

            meta = get_image_metadata(img_path)
            self.assertEqual(meta["file"]["name"], "sample.png")
            self.assertEqual(meta["file"]["extension"], "PNG")
            self.assertEqual(meta["image"]["width"], 200)
            self.assertEqual(meta["image"]["height"], 100)
            self.assertEqual(meta["image"]["dimensions"], "200 × 100 px")
            self.assertEqual(meta["image"]["aspect_ratio"], "2:1")


if __name__ == "__main__":
    unittest.main()
