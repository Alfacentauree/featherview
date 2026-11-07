import os
import tempfile
import unittest
from PIL import Image

from featherview.wallpaper import (
    get_current_desktop_wallpaper,
    prepare_custom_wallpaper,
    set_desktop_wallpaper,
)


class TestWallpaper(unittest.TestCase):

    def test_nonexistent_file(self):
        success, msg = set_desktop_wallpaper("/nonexistent/path/to/image.jpg")
        self.assertFalse(success)
        self.assertIn("File not found", msg)

    def test_wallpaper_setter_validation(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            img = Image.new("RGB", (400, 300), (50, 100, 150))
            img.save(tmp.name)

            for style in ["zoom", "scaled", "centered", "spanned"]:
                success, msg = set_desktop_wallpaper(tmp.name, style=style, bg_color="#121212")
                self.assertTrue(success)
                self.assertIn("Wallpaper updated", msg)

    def test_custom_dimensions_plus_minus_preparation(self):
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            img = Image.new("RGB", (800, 600), (100, 150, 200))
            img.save(tmp.name)

            # Test generating custom wallpaper with 1366 x 768
            out_file = prepare_custom_wallpaper(
                image_path=tmp.name,
                target_width=1366,
                target_height=768,
                style="zoom",
            )
            self.assertTrue(os.path.exists(out_file))

            with Image.open(out_file) as generated:
                self.assertEqual(generated.size, (1366, 768))

            # Test set_desktop_wallpaper with custom_size
            success, msg = set_desktop_wallpaper(
                image_path=tmp.name,
                style="zoom",
                custom_size=(1366, 768),
            )
            self.assertTrue(success)
            self.assertIn("1366×768", msg)

    def test_get_current_wallpaper(self):
        current = get_current_desktop_wallpaper()
        if current is not None:
            self.assertIsInstance(current, str)


if __name__ == "__main__":
    unittest.main()
