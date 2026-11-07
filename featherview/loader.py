"""Image collection management, directory scanning, and asynchronous loading."""

import os
import re
from typing import Callable, List, Optional, Tuple

import gi
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import GdkPixbuf, GLib

SUPPORTED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".jpe", ".jfif",
    ".gif", ".webp", ".svg", ".svgz",
    ".bmp", ".dib", ".tiff", ".tif",
    ".ico", ".icns", ".pnm", ".pbm", ".pgm", ".ppm",
    ".xbm", ".xpm", ".tga", ".avif", ".heif"
}


def natural_sort_key(text: str) -> list:
    """Sort strings containing numbers naturally (e.g. file1, file2, file10)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", text)]


def is_image_file(path: str) -> bool:
    """Checks if the file extension is a supported image format."""
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


def load_pixbuf(path: str) -> Optional[GdkPixbuf.Pixbuf]:
    """Loads a GdkPixbuf from a file path with EXIF orientation auto-applied."""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        if hasattr(pixbuf, "apply_embedded_orientation"):
            oriented = pixbuf.apply_embedded_orientation()
            if oriented:
                return oriented
        return pixbuf
    except Exception as e:
        print(f"[FeatherView] Error loading {path}: {e}")
        return None


def load_animation(path: str) -> Optional[GdkPixbuf.PixbufAnimation]:
    """Loads a PixbufAnimation (e.g. for animated GIFs)."""
    try:
        anim = GdkPixbuf.PixbufAnimation.new_from_file(path)
        return anim
    except Exception:
        return None


def create_thumbnail(path: str, max_size: int = 96) -> Optional[GdkPixbuf.Pixbuf]:
    """Creates a thumbnail pixbuf preserving aspect ratio."""
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            path, max_size, max_size, preserve_aspect_ratio=True
        )
        if hasattr(pixbuf, "apply_embedded_orientation"):
            oriented = pixbuf.apply_embedded_orientation()
            if oriented:
                return oriented
        return pixbuf
    except Exception:
        return None


class ImageCollection:
    """Manages the list of images in the current folder, sorting, and navigation."""

    SORT_NAME_ASC = "name_asc"
    SORT_NAME_DESC = "name_desc"
    SORT_DATE_DESC = "date_desc"
    SORT_DATE_ASC = "date_asc"
    SORT_SIZE_DESC = "size_desc"
    SORT_SIZE_ASC = "size_asc"

    def __init__(self):
        self.directory: Optional[str] = None
        self.files: List[str] = []
        self.current_index: int = -1
        self.sort_mode: str = self.SORT_NAME_ASC

    def load_path(self, target_path: str) -> bool:
        """Loads an image or directory. If an image is provided, scans its parent directory."""
        abs_path = os.path.abspath(os.path.expanduser(target_path))
        if os.path.isdir(abs_path):
            self.directory = abs_path
            target_file = None
        elif os.path.isfile(abs_path):
            self.directory = os.path.dirname(abs_path)
            target_file = abs_path
        else:
            return False

        self._scan_directory()

        if target_file and target_file in self.files:
            self.current_index = self.files.index(target_file)
        elif self.files:
            self.current_index = 0
        else:
            self.current_index = -1

        return len(self.files) > 0

    def _scan_directory(self) -> None:
        """Scans directory for supported image files."""
        if not self.directory or not os.path.isdir(self.directory):
            self.files = []
            return

        found = []
        try:
            with os.scandir(self.directory) as it:
                for entry in it:
                    if entry.is_file() and not entry.name.startswith("."):
                        if is_image_file(entry.name):
                            found.append(entry.path)
        except Exception as e:
            print(f"[FeatherView] Scan error: {e}")

        self.files = found
        self._apply_sort()

    def set_sort_mode(self, mode: str) -> None:
        """Updates sort mode and re-sorts current list while preserving active image."""
        current_path = self.current_path
        self.sort_mode = mode
        self._apply_sort()
        if current_path and current_path in self.files:
            self.current_index = self.files.index(current_path)

    def _apply_sort(self) -> None:
        if self.sort_mode == self.SORT_NAME_ASC:
            self.files.sort(key=lambda p: natural_sort_key(os.path.basename(p)))
        elif self.sort_mode == self.SORT_NAME_DESC:
            self.files.sort(key=lambda p: natural_sort_key(os.path.basename(p)), reverse=True)
        elif self.sort_mode == self.SORT_DATE_DESC:
            self.files.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
        elif self.sort_mode == self.SORT_DATE_ASC:
            self.files.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
        elif self.sort_mode == self.SORT_SIZE_DESC:
            self.files.sort(key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0, reverse=True)
        elif self.sort_mode == self.SORT_SIZE_ASC:
            self.files.sort(key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0)

    @property
    def current_path(self) -> Optional[str]:
        if 0 <= self.current_index < len(self.files):
            return self.files[self.current_index]
        return None

    @property
    def count(self) -> int:
        return len(self.files)

    def next(self) -> Optional[str]:
        if not self.files:
            return None
        self.current_index = (self.current_index + 1) % len(self.files)
        return self.current_path

    def prev(self) -> Optional[str]:
        if not self.files:
            return None
        self.current_index = (self.current_index - 1 + len(self.files)) % len(self.files)
        return self.current_path

    def first(self) -> Optional[str]:
        if not self.files:
            return None
        self.current_index = 0
        return self.current_path

    def last(self) -> Optional[str]:
        if not self.files:
            return None
        self.current_index = len(self.files) - 1
        return self.current_path

    def go_to_index(self, index: int) -> Optional[str]:
        if 0 <= index < len(self.files):
            self.current_index = index
            return self.current_path
        return None

    def go_to_path(self, path: str) -> Optional[str]:
        if path in self.files:
            self.current_index = self.files.index(path)
            return self.current_path
        return None

    def remove_current(self) -> Optional[str]:
        """Removes the current image from the collection (after delete) and navigates to the next."""
        if not self.files or self.current_index < 0:
            return None

        del self.files[self.current_index]
        if not self.files:
            self.current_index = -1
            return None

        if self.current_index >= len(self.files):
            self.current_index = len(self.files) - 1

        return self.current_path
