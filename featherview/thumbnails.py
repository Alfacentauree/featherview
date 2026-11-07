"""Horizontal thumbnail filmstrip widget with asynchronous thumbnail generation."""

import threading
from typing import Callable, Dict, List, Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import GdkPixbuf, GLib, Gtk

from .loader import create_thumbnail


class ThumbnailStrip(Gtk.ScrolledWindow):
    """Horizontal filmstrip showing previews of all images in the folder."""

    THUMB_SIZE = 72

    def __init__(self, on_select: Callable[[int], None]):
        super().__init__()
        self.on_select = on_select
        self.current_index = -1
        self.buttons: List[Gtk.Button] = []
        self.images: List[Gtk.Image] = []
        self.cache: Dict[str, GdkPixbuf.Pixbuf] = {}
        self.generation_token = 0

        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.set_min_content_height(self.THUMB_SIZE + 24)
        self.get_style_context().add_class("thumbnail-strip")

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.box.set_margin_start(8)
        self.box.set_margin_end(8)
        self.box.set_margin_top(6)
        self.box.set_margin_bottom(6)
        self.add(self.box)

    def load_files(self, file_paths: List[str], active_index: int = 0) -> None:
        """Populates thumbnail placeholders and starts background loading."""
        self.generation_token += 1
        current_token = self.generation_token

        # Clear existing
        for child in self.box.get_children():
            self.box.remove(child)
        self.buttons.clear()
        self.images.clear()
        self.current_index = active_index

        for idx, path in enumerate(file_paths):
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("thumb-btn")
            btn.set_tooltip_text(f"{idx + 1}. {GLib.path_get_basename(path)}")

            img = Gtk.Image()
            img.set_size_request(self.THUMB_SIZE, self.THUMB_SIZE)
            btn.add(img)

            # Connect click callback
            btn.connect("clicked", lambda b, i=idx: self.on_select(i))

            self.box.pack_start(btn, False, False, 0)
            self.buttons.append(btn)
            self.images.append(img)

        self.box.show_all()
        self.highlight_active(active_index)

        # Start background thumbnail loading thread
        threading.Thread(
            target=self._load_thumbnails_async,
            args=(list(file_paths), current_token),
            daemon=True,
        ).start()

    def highlight_active(self, index: int) -> None:
        """Highlights the active thumbnail and scrolls it into view."""
        if 0 <= self.current_index < len(self.buttons):
            self.buttons[self.current_index].get_style_context().remove_class("thumb-btn-active")

        self.current_index = index

        if 0 <= index < len(self.buttons):
            btn = self.buttons[index]
            btn.get_style_context().add_class("thumb-btn-active")

            # Scroll into view smoothly
            def scroll_to_btn():
                alloc = btn.get_allocation()
                adj = self.get_hadjustment()
                if adj and alloc.width > 0:
                    page_size = adj.get_page_size()
                    target_x = alloc.x - (page_size - alloc.width) / 2.0
                    target_x = max(0, min(adj.get_upper() - page_size, target_x))
                    adj.set_value(target_x)
                return False

            GLib.idle_add(scroll_to_btn)

    def _load_thumbnails_async(self, paths: List[str], token: int) -> None:
        """Background thread worker to generate thumbnails progressively."""
        # Prioritize near current index first
        indices = list(range(len(paths)))
        if 0 <= self.current_index < len(paths):
            indices.sort(key=lambda i: abs(i - self.current_index))

        for idx in indices:
            if token != self.generation_token:
                return  # Outdated scan

            path = paths[idx]
            pixbuf = self.cache.get(path)
            if not pixbuf:
                pixbuf = create_thumbnail(path, self.THUMB_SIZE)
                if pixbuf:
                    self.cache[path] = pixbuf

            if pixbuf and idx < len(self.images):
                GLib.idle_add(self._update_image_widget, idx, pixbuf, token)

    def _update_image_widget(self, index: int, pixbuf: GdkPixbuf.Pixbuf, token: int) -> bool:
        if token == self.generation_token and index < len(self.images):
            self.images[index].set_from_pixbuf(pixbuf)
        return False
