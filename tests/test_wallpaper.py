import os
import tempfile
import unittest

from featherview.wallpaper import get_current_desktop_wallpaper, set_desktop_wallpaper


class TestWallpaper(unittest.TestCase):

    def test_nonexistent_file(self):
        success, msg = set_desktop_wallpaper("/nonexistent/path/to/image.jpg")
        self.assertFalse(success)
        self.assertIn("File not found", msg)

    def test_wallpaper_setter_validation(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            # Test with various placement styles
            for style in ["zoom", "scaled", "centered", "spanned"]:
                success, msg = set_desktop_wallpaper(tmp.name, style=style, bg_color="#121212")
                self.assertTrue(success)
                self.assertIn("Wallpaper updated", msg)

    def test_get_current_wallpaper(self):
        current = get_current_desktop_wallpaper()
        # Should return a string path or None depending on environment
        if current is not None:
            self.assertIsInstance(current, str)


if __name__ == "__main__":
    unittest.main()
