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

    def test_dialog_live_preview(self):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        from featherview.dialogs import SetWallpaperDialog

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            img = Image.new("RGB", (640, 480), (30, 90, 150))
            img.save(tmp.name)

            parent = Gtk.Window()
            dlg = SetWallpaperDialog(parent, tmp.name)

            # Test live preview updating with _set_dimensions
            dlg._set_dimensions(1920, 1080)
            self.assertIsNotNone(dlg.img_preview.get_pixbuf())
            self.assertIn("1920 × 1080", dlg.lbl_legend_wallpaper.get_text())
            self.assertIn("1366 × 768", dlg.lbl_legend_screen.get_text())

            # Test stepping with aspect locked
            dlg._step_width(50)
            self.assertEqual(dlg.spin_w.get_value(), 1970)

            # Test stepping with aspect unlocked
            dlg.chk_aspect.set_active(False)
            dlg._step_height(-50)
            self.assertEqual(dlg.spin_h.get_value(), 1428)

            # Test style live preview
            dlg.radio_scaled.set_active(True)
            dlg._update_live_preview()
            self.assertIsNotNone(dlg.img_preview.get_pixbuf())

            dlg.destroy()
            parent.destroy()


if __name__ == "__main__":
    unittest.main()
