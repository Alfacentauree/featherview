"""Dialog windows for image properties, keyboard shortcuts, wallpaper settings, and confirmations."""

import os
from typing import Any, Callable, Dict, Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gtk

from . import __app_name__, __version__
from .loader import create_thumbnail
from .wallpaper import set_desktop_wallpaper


class SetWallpaperDialog(Gtk.Dialog):
    """Interactive desktop wallpaper configuration dialog with custom Width/Height controls."""

    def __init__(
        self,
        parent: Gtk.Window,
        image_path: str,
        on_applied: Optional[Callable[[bool, str], None]] = None,
    ):
        super().__init__(
            title="Set as Desktop Wallpaper",
            transient_for=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        self.image_path = image_path
        self.on_applied = on_applied
        self.set_default_size(520, 600)

        # Detect original image dimensions
        self.orig_w, self.orig_h = 1920, 1080
        try:
            from PIL import Image
            with Image.open(image_path) as im:
                self.orig_w, self.orig_h = im.size
        except Exception:
            try:
                pix = GdkPixbuf.Pixbuf.new_from_file(image_path)
                self.orig_w, self.orig_h = pix.get_width(), pix.get_height()
            except Exception:
                pass

        # Detect display monitor resolution
        screen = Gdk.Screen.get_default()
        self.screen_w = screen.get_width() if screen else 1920
        self.screen_h = screen.get_height() if screen else 1080

        # Aspect ratio for locking
        self.aspect_ratio = float(self.orig_w) / float(self.orig_h) if self.orig_h > 0 else 1.777
        self._syncing_dims = False

        # Action Buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        apply_btn = self.add_button("Apply Wallpaper", Gtk.ResponseType.OK)
        apply_btn.get_style_context().add_class("suggested-action")

        # Scrollable container so it fits on any screen height
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.get_content_area().pack_start(scrolled, True, True, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        scrolled.add(content)

        # 1. Image Preview Frame
        preview_frame = Gtk.Frame()
        preview_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_box.set_margin_top(12)
        preview_box.set_margin_bottom(12)
        preview_box.set_margin_start(12)
        preview_box.set_margin_end(12)

        thumb = create_thumbnail(image_path, max_size=180)
        if thumb:
            img_widget = Gtk.Image.new_from_pixbuf(thumb)
        else:
            img_widget = Gtk.Image.new_from_icon_name("preferences-desktop-wallpaper", Gtk.IconSize.DIALOG)
        preview_box.pack_start(img_widget, True, True, 0)

        name_lbl = Gtk.Label(label=f"{os.path.basename(image_path)} ({self.orig_w} × {self.orig_h} px)")
        name_lbl.get_style_context().add_class("dim-label")
        name_lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        preview_box.pack_start(name_lbl, False, False, 0)

        preview_frame.add(preview_box)
        content.pack_start(preview_frame, False, False, 0)

        # 2. Custom Width & Height Controls (with Plus / Minus buttons)
        dim_label = Gtk.Label()
        dim_label.set_markup("<b>Wallpaper Resolution (Width × Height)</b>")
        dim_label.set_halign(Gtk.Align.START)
        content.pack_start(dim_label, False, False, 0)

        dim_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        dim_container.set_margin_start(8)

        # Width Row
        box_w = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl_w = Gtk.Label(label="Width (px):")
        lbl_w.set_size_request(85, -1)
        lbl_w.set_halign(Gtk.Align.START)

        btn_w_minus_50 = Gtk.Button(label="−50")
        btn_w_minus_50.get_style_context().add_class("step-btn")
        btn_w_minus_50.set_tooltip_text("Decrease width by 50 px")

        btn_w_minus_10 = Gtk.Button(label=" − ")
        btn_w_minus_10.get_style_context().add_class("step-btn")
        btn_w_minus_10.set_tooltip_text("Decrease width by 10 px")

        self.spin_w = Gtk.SpinButton.new_with_range(100, 10000, 10)
        self.spin_w.set_value(self.screen_w)
        self.spin_w.set_numeric(True)
        self.spin_w.set_width_chars(6)

        btn_w_plus_10 = Gtk.Button(label=" + ")
        btn_w_plus_10.get_style_context().add_class("step-btn")
        btn_w_plus_10.set_tooltip_text("Increase width by 10 px")

        btn_w_plus_50 = Gtk.Button(label="+50")
        btn_w_plus_50.get_style_context().add_class("step-btn")
        btn_w_plus_50.set_tooltip_text("Increase width by 50 px")

        box_w.pack_start(lbl_w, False, False, 0)
        box_w.pack_start(btn_w_minus_50, False, False, 0)
        box_w.pack_start(btn_w_minus_10, False, False, 0)
        box_w.pack_start(self.spin_w, True, True, 0)
        box_w.pack_start(btn_w_plus_10, False, False, 0)
        box_w.pack_start(btn_w_plus_50, False, False, 0)
        dim_container.pack_start(box_w, False, False, 0)

        # Height Row
        box_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl_h = Gtk.Label(label="Height (px):")
        lbl_h.set_size_request(85, -1)
        lbl_h.set_halign(Gtk.Align.START)

        btn_h_minus_50 = Gtk.Button(label="−50")
        btn_h_minus_50.get_style_context().add_class("step-btn")
        btn_h_minus_50.set_tooltip_text("Decrease height by 50 px")

        btn_h_minus_10 = Gtk.Button(label=" − ")
        btn_h_minus_10.get_style_context().add_class("step-btn")
        btn_h_minus_10.set_tooltip_text("Decrease height by 10 px")

        self.spin_h = Gtk.SpinButton.new_with_range(100, 10000, 10)
        self.spin_h.set_value(self.screen_h)
        self.spin_h.set_numeric(True)
        self.spin_h.set_width_chars(6)

        btn_h_plus_10 = Gtk.Button(label=" + ")
        btn_h_plus_10.get_style_context().add_class("step-btn")
        btn_h_plus_10.set_tooltip_text("Increase height by 10 px")

        btn_h_plus_50 = Gtk.Button(label="+50")
        btn_h_plus_50.get_style_context().add_class("step-btn")
        btn_h_plus_50.set_tooltip_text("Increase height by 50 px")

        box_h.pack_start(lbl_h, False, False, 0)
        box_h.pack_start(btn_h_minus_50, False, False, 0)
        box_h.pack_start(btn_h_minus_10, False, False, 0)
        box_h.pack_start(self.spin_h, True, True, 0)
        box_h.pack_start(btn_h_plus_10, False, False, 0)
        box_h.pack_start(btn_h_plus_50, False, False, 0)
        dim_container.pack_start(box_h, False, False, 0)

        # Connect button click steppers
        btn_w_minus_50.connect("clicked", lambda b: self._step_width(-50))
        btn_w_minus_10.connect("clicked", lambda b: self._step_width(-10))
        btn_w_plus_10.connect("clicked", lambda b: self._step_width(10))
        btn_w_plus_50.connect("clicked", lambda b: self._step_width(50))

        btn_h_minus_50.connect("clicked", lambda b: self._step_height(-50))
        btn_h_minus_10.connect("clicked", lambda b: self._step_height(-10))
        btn_h_plus_10.connect("clicked", lambda b: self._step_height(10))
        btn_h_plus_50.connect("clicked", lambda b: self._step_height(50))

        # Aspect ratio lock & Presets
        options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.chk_aspect = Gtk.CheckButton(label="🔗 Keep Aspect Ratio")
        self.chk_aspect.set_active(True)
        options_box.pack_start(self.chk_aspect, False, False, 0)

        # Quick preset buttons
        btn_preset_screen = Gtk.Button(label=f"🖥️ Screen ({self.screen_w}×{self.screen_h})")
        btn_preset_screen.connect("clicked", lambda b: self._set_dimensions(self.screen_w, self.screen_h))
        options_box.pack_end(btn_preset_screen, False, False, 0)

        btn_preset_orig = Gtk.Button(label=f"🖼️ Original ({self.orig_w}×{self.orig_h})")
        btn_preset_orig.connect("clicked", lambda b: self._set_dimensions(self.orig_w, self.orig_h))
        options_box.pack_end(btn_preset_orig, False, False, 0)

        dim_container.pack_start(options_box, False, False, 0)
        content.pack_start(dim_container, False, False, 0)

        # Connect value-changed listeners for aspect ratio sync
        self.spin_w.connect("value-changed", self._on_width_changed)
        self.spin_h.connect("value-changed", self._on_height_changed)

        # 3. Placement Style Selection
        style_label = Gtk.Label()
        style_label.set_markup("<b>Placement Style</b>")
        style_label.set_halign(Gtk.Align.START)
        content.pack_start(style_label, False, False, 0)

        style_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        style_box.set_margin_start(12)

        self.radio_zoom = Gtk.RadioButton.new_with_label(
            None, "Zoom / Fill Screen (Crops edges to fill display - Recommended)"
        )
        self.radio_scaled = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_zoom, "Fit to Screen (Preserves entire image with border)"
        )
        self.radio_centered = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_zoom, "Center (Displays original resolution in center)"
        )
        self.radio_spanned = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_zoom, "Span (Stretches across multiple displays)"
        )

        self.radio_zoom.set_active(True)

        style_box.pack_start(self.radio_zoom, False, False, 0)
        style_box.pack_start(self.radio_scaled, False, False, 0)
        style_box.pack_start(self.radio_centered, False, False, 0)
        style_box.pack_start(self.radio_spanned, False, False, 0)
        content.pack_start(style_box, False, False, 0)

        # 4. Background Border Color (for Fit and Center modes)
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        color_box.set_margin_start(12)
        color_lbl = Gtk.Label(label="Background Border Color:")
        color_lbl.set_halign(Gtk.Align.START)

        self.color_button = Gtk.ColorButton()
        black_rgba = Gdk.RGBA(0.0, 0.0, 0.0, 1.0)
        self.color_button.set_rgba(black_rgba)

        color_box.pack_start(color_lbl, False, False, 0)
        color_box.pack_start(self.color_button, False, False, 0)
        content.pack_start(color_box, False, False, 0)

        self.connect("response", self._on_response)
        self.show_all()

    def _step_width(self, delta: int) -> None:
        val = self.spin_w.get_value()
        self.spin_w.set_value(max(100, min(10000, val + delta)))

    def _step_height(self, delta: int) -> None:
        val = self.spin_h.get_value()
        self.spin_h.set_value(max(100, min(10000, val + delta)))

    def _set_dimensions(self, width: int, height: int) -> None:
        self._syncing_dims = True
        self.spin_w.set_value(width)
        self.spin_h.set_value(height)
        self._syncing_dims = False

    def _on_width_changed(self, spin: Gtk.SpinButton) -> None:
        if self._syncing_dims:
            return
        if self.chk_aspect.get_active() and self.aspect_ratio > 0:
            self._syncing_dims = True
            new_h = int(round(spin.get_value() / self.aspect_ratio))
            self.spin_h.set_value(max(100, min(10000, new_h)))
            self._syncing_dims = False

    def _on_height_changed(self, spin: Gtk.SpinButton) -> None:
        if self._syncing_dims:
            return
        if self.chk_aspect.get_active() and self.aspect_ratio > 0:
            self._syncing_dims = True
            new_w = int(round(spin.get_value() * self.aspect_ratio))
            self.spin_w.set_value(max(100, min(10000, new_w)))
            self._syncing_dims = False

    def _on_response(self, dialog, response_id: int) -> None:
        if response_id == Gtk.ResponseType.OK:
            # Determine style
            if self.radio_zoom.get_active():
                style = "zoom"
            elif self.radio_scaled.get_active():
                style = "scaled"
            elif self.radio_centered.get_active():
                style = "centered"
            else:
                style = "spanned"

            # Determine background hex color
            rgba = self.color_button.get_rgba()
            r = int(rgba.red * 255)
            g = int(rgba.green * 255)
            b = int(rgba.blue * 255)
            hex_color = f"#{r:02x}{g:02x}{b:02x}"

            # Extract user configured Width and Height
            target_w = int(self.spin_w.get_value())
            target_h = int(self.spin_h.get_value())

            success, message = set_desktop_wallpaper(
                self.image_path,
                style=style,
                bg_color=hex_color,
                custom_size=(target_w, target_h),
            )
            if self.on_applied:
                self.on_applied(success, message)

        self.destroy()


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
        ("Wallpaper & Actions", [
            ("Ctrl + Shift + W / Ctrl + B", "Set as Desktop Wallpaper (with custom +/- Width & Height)"),
            ("Right Click on Image", "Context menu (Set Wallpaper, Copy, etc.)"),
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
        self.set_default_size(540, 580)
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
