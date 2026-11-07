import os
import tempfile
import unittest

from featherview.loader import ImageCollection, is_image_file, natural_sort_key


class TestImageLoader(unittest.TestCase):

    def test_natural_sort(self):
        items = ["img10.png", "img1.png", "img2.png", "img20.png"]
        sorted_items = sorted(items, key=natural_sort_key)
        self.assertEqual(sorted_items, ["img1.png", "img2.png", "img10.png", "img20.png"])

    def test_is_image_file(self):
        self.assertTrue(is_image_file("photo.JPG"))
        self.assertTrue(is_image_file("vector.svg"))
        self.assertTrue(is_image_file("animation.gif"))
        self.assertTrue(is_image_file("modern.webp"))
        self.assertFalse(is_image_file("document.pdf"))
        self.assertFalse(is_image_file("script.py"))

    def test_image_collection_navigation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "a.png")
            f2 = os.path.join(tmpdir, "b.jpg")
            f3 = os.path.join(tmpdir, "c.webp")
            for f in (f1, f2, f3):
                with open(f, "w") as fp:
                    fp.write("dummy")

            coll = ImageCollection()
            ok = coll.load_path(f1)
            self.assertTrue(ok)
            self.assertEqual(coll.count, 3)
            self.assertEqual(coll.current_path, f1)

            # Next
            self.assertEqual(coll.next(), f2)
            self.assertEqual(coll.next(), f3)
            self.assertEqual(coll.next(), f1)  # wraps around

            # Prev
            self.assertEqual(coll.prev(), f3)
            self.assertEqual(coll.prev(), f2)

            # First and Last
            self.assertEqual(coll.first(), f1)
            self.assertEqual(coll.last(), f3)

            # Removal
            new_curr = coll.remove_current()
            self.assertEqual(coll.count, 2)
            self.assertEqual(new_curr, f2)


if __name__ == "__main__":
    unittest.main()
