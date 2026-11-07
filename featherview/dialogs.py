"""Dialog windows for image properties, keyboard shortcuts, and confirmations."""

from typing import Any, Dict

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from . import __app_name__, __version__


class ImagePropertiesDialog(Gtk.Dialog):
    """Detailed metadata and EXIF properties dialog."""

    def __init__(self, parent: Gtk.Window, metadata: Dict[str, Any]):
        super().__init__(
            title="Image Properties",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self.set_default_size(440, 520)
        self.add_button("Close", Gtk.ResponseType.CLOSE)

        box = self.get_content_area()
        box.set_spacing(12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        notebook = Gtk.Notebook()
        box.pack_start(notebook, True, True, 0)

        # Tab 1: General Info
        gen_page = self._create_grid_page()
        row = 0

        file_meta = metadata.get("file", {})
        img_meta = metadata.get("image", {})

        fields = [
            ("File Name", file_meta.get("name", "—")),
            ("File Size", f"{file_meta.get('size_human', '—')} ({file_meta.get('size_bytes', 0):,} bytes)"),
            ("Format", f"{file_meta.get('extension', '—')} ({img_meta.get('format', '—')})"),
            ("Dimensions", img_meta.get("dimensions", "—")),
            ("Resolution", img_meta.get("megapixels", "—")),
            ("Aspect Ratio", img_meta.get("aspect_ratio", "—")),
            ("Color Mode", img_meta.get("color_mode", "—")),
            ("Modified", file_meta.get("modified", "—")),
            ("Full Path", file_meta.get("path", "—")),
        ]

        for label_text, val_text in fields:
            self._add_grid_row(gen_page, row, label_text, str(val_text))
            row += 1

        notebook.append_page(self._wrap_scroll(gen_page), Gtk.Label(label="General"))

        # Tab 2: EXIF & Camera Data
        exif_meta = metadata.get("exif", {})
        exif_page = self._create_grid_page()
        if exif_meta:
            row = 0
            for k, v in sorted(exif_meta.items()):
                self._add_grid_row(exif_page, row, k, str(v))
                row += 1
        else:
            empty_lbl = Gtk.Label(label="No EXIF metadata found in this image.")
            empty_lbl.get_style_context().add_class("dim-label")
            empty_lbl.set_margin_top(32)
            exif_page.attach(empty_lbl, 0, 0, 2, 1)

        notebook.append_page(self._wrap_scroll(exif_page), Gtk.Label(label="Camera & EXIF"))

        self.connect("response", lambda d, r: self.destroy())
        self.show_all()

    def _create_grid_page(self) -> Gtk.Grid:
        grid = Gtk.Grid()
        grid.set_column_spacing(16)
        grid.set_row_spacing(10)
        grid.set_margin_start(16)
        grid.set_margin_end(16)
        grid.set_margin_top(16)
        grid.set_margin_bottom(16)
        return grid

    def _add_grid_row(self, grid: Gtk.Grid, row: int, key: str, val: str) -> None:
        lbl_key = Gtk.Label(label=key)
        lbl_key.set_halign(Gtk.Align.START)
        lbl_key.get_style_context().add_class("dim-label")

        lbl_val = Gtk.Label(label=val)
        lbl_val.set_halign(Gtk.Align.START)
        lbl_val.set_line_wrap(True)
        lbl_val.set_selectable(True)

        grid.attach(lbl_key, 0, row, 1, 1)
        grid.attach(lbl_val, 1, row, 1, 1)

    def _wrap_scroll(self, widget: Gtk.Widget) -> Gtk.ScrolledWindow:
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(widget)
        return sw


class ShortcutsDialog(Gtk.Dialog):
    """Keyboard shortcuts helper dialog."""

    SHORTCUTS = [
        ("Navigation", [
            ("Right Arrow / Page Down", "Next image"),
            ("Left Arrow / Page Up", "Previous image"),
            ("Home", "First image in folder"),
            ("End", "Last image in folder"),
            ("Spacebar", "Play / Pause slideshow"),
        ]),
        ("Zoom & Pan", [
            ("+ / =", "Zoom In"),
            ("-", "Zoom Out"),
            ("0 / 1", "Actual Size (100%)"),
            ("W / F", "Fit image to window"),
            ("Scroll Wheel", "Zoom centered at cursor"),
            ("Left Click Drag", "Pan image"),
        ]),
        ("Transforms & View", [
            ("R", "Rotate 90° Clockwise"),
            ("Shift + R", "Rotate 90° Counter-Clockwise"),
            ("H", "Flip Horizontally"),
            ("V", "Flip Vertically"),
            ("F11 / Double-Click", "Toggle Fullscreen"),
            ("T", "Toggle Thumbnail Filmstrip"),
            ("I", "Toggle Image Properties / EXIF"),
        ]),
        ("File Actions", [
            ("Ctrl + O", "Open image or folder"),
            ("Ctrl + S", "Save / Export image as..."),
            ("Ctrl + C", "Copy image to clipboard"),
            ("Delete", "Move image to Trash"),
            ("Ctrl + Q / Escape", "Quit / Exit Fullscreen"),
        ]),
    ]

    def __init__(self, parent: Gtk.Window):
        super().__init__(
            title="Keyboard Shortcuts",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self.set_default_size(520, 560)
        self.add_button("Close", Gtk.ResponseType.CLOSE)

        box = self.get_content_area()
        box.set_spacing(16)
        box.set_margin_start(20)
        box.set_margin_end(20)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(sw, True, True, 0)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        sw.add(main_box)

        for category, items in self.SHORTCUTS:
            cat_label = Gtk.Label()
            cat_label.set_markup(f"<b>{category}</b>")
            cat_label.set_halign(Gtk.Align.START)
            main_box.pack_start(cat_label, False, False, 0)

            grid = Gtk.Grid()
            grid.set_column_spacing(24)
            grid.set_row_spacing(6)
            grid.set_margin_start(12)

            for row_idx, (shortcut, desc) in enumerate(items):
                key_box = Gtk.Box()
                key_lbl = Gtk.Label(label=shortcut)
                key_lbl.get_style_context().add_class("shortcut-pill")
                key_box.pack_start(key_lbl, False, False, 0)

                desc_lbl = Gtk.Label(label=desc)
                desc_lbl.set_halign(Gtk.Align.START)

                grid.attach(key_box, 0, row_idx, 1, 1)
                grid.attach(desc_lbl, 1, row_idx, 1, 1)

            main_box.pack_start(grid, False, False, 0)

        self.connect("response", lambda d, r: self.destroy())
        self.show_all()


class AboutDialog(Gtk.AboutDialog):
    """About dialog for FeatherView."""

    def __init__(self, parent: Gtk.Window):
        super().__init__(
            transient_for=parent,
            modal=True,
            program_name=__app_name__,
            version=__version__,
            comments="Ultra-lightweight, blazing-fast image viewer for Linux desktop.",
            website="https://github.com/featherview/featherview",
            authors=["Senior Software Developer", "Open Source Community"],
            license_type=Gtk.License.MIT_X11,
            logo_icon_name="image-x-generic",
        )
        self.connect("response", lambda d, r: self.destroy())
        self.show_all()
