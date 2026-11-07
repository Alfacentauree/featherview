import unittest
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf

from featherview.canvas import ImageCanvas


class TestCanvas(unittest.TestCase):

    def setUp(self):
        self.canvas = ImageCanvas()
        self.pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 400, 300)

    def test_initial_state(self):
        self.assertEqual(self.canvas.zoom, 1.0)
        self.assertEqual(self.canvas.rotation, 0)
        self.assertFalse(self.canvas.flip_h)
        self.assertFalse(self.canvas.flip_v)

    def test_image_assignment(self):
        self.canvas.set_image(self.pixbuf)
        self.assertIsNotNone(self.canvas.pixbuf)
        ow, oh = self.canvas._get_oriented_size()
        self.assertEqual((ow, oh), (400, 300))

    def test_rotations(self):
        self.canvas.set_image(self.pixbuf)
        self.canvas.rotate_cw()
        self.assertEqual(self.canvas.rotation, 90)
        self.assertEqual(self.canvas.rotate_ccw(), None)
        self.assertEqual(self.canvas.rotation, 0)

    def test_zoom_limits(self):
        self.canvas.zoom_at(0, 0, 100.0)
        self.assertLessEqual(self.canvas.zoom, ImageCanvas.MAX_ZOOM)
        self.canvas.zoom_at(0, 0, 0.001)
        self.assertGreaterEqual(self.canvas.zoom, ImageCanvas.MIN_ZOOM)


if __name__ == "__main__":
    unittest.main()
