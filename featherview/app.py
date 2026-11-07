"""Main application window and event handling logic for FeatherView."""

import argparse
import os
import sys
from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gdk, Gio, GLib, Gtk

from . import __app_id__, __app_name__, __version__
from .canvas import ImageCanvas
from .dialogs import AboutDialog, ImagePropertiesDialog, SetWallpaperDialog, ShortcutsDialog
from .loader import ImageCollection, is_image_file, load_animation, load_pixbuf
from .metadata import get_image_metadata
from .thumbnails import ThumbnailStrip
from .toolbar import AppHeaderBar, FloatingOverlay
from .wallpaper import set_desktop_wallpaper


class FeatherViewWindow(Gtk.ApplicationWindow):
    """The main FeatherView window."""

    SLIDESHOW_INTERVAL = 3  # seconds

    def __init__(self, app: Gtk.Application):
        super().__init__(application=app, title=__app_name__)

        self.set_default_size(1000, 680)
        self.set_position(Gtk.WindowPosition.CENTER)

        # State
        self.collection = ImageCollection()
        self.is_fullscreen = False
        self.slideshow_active = False
        self.slideshow_timer_id: Optional[int] = None
        self.show_thumbnails = False

        # Load Custom CSS
        self._load_styles()

        # Build UI
        self._setup_ui()

        # Connect Drag and Drop
        self._setup_drag_and_drop()

        # Keyboard shortcuts
        self.connect("key-press-event", self._on_key_press)
        self.connect("motion-notify-event", self._on_window_motion)
        self.connect("destroy", self._on_destroy)

    def _load_styles(self) -> None:
        try:
            import pkgutil
            css_data = pkgutil.get_data("featherview", "styles.css")
            if css_data:
                css_provider = Gtk.CssProvider()
                css_provider.load_from_data(css_data)
                Gtk.StyleContext.add_provider_for_screen(
                    Gdk.Screen.get_default(),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )
                return
        except Exception:
            pass

        # Fallback to local file path
        css_provider = Gtk.CssProvider()
        css_file = os.path.join(os.path.dirname(__file__), "styles.css")
        if os.path.exists(css_file):
            css_provider.load_from_path(css_file)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _setup_ui(self) -> None:
        # Actions mapping for toolbar and menus
        actions = {
            "open": self.open_file_dialog,
            "open_folder": self.open_folder_dialog,
            "prev": self.prev_image,
            "next": self.next_image,
            "zoom_in": lambda: self.canvas.zoom_in(),
            "zoom_out": lambda: self.canvas.zoom_out(),
            "zoom_fit": lambda: self.canvas.set_fit_auto(),
            "zoom_100": lambda: self.canvas.set_actual_size(),
            "rotate_cw": lambda: self.canvas.rotate_cw(),
            "rotate_ccw": lambda: self.canvas.rotate_ccw(),
            "flip_h": lambda: self.canvas.toggle_flip_h(),
            "flip_v": lambda: self.canvas.toggle_flip_v(),
            "slideshow": self.toggle_slideshow,
            "thumbnails": self.toggle_thumbnails,
            "fullscreen": self.toggle_fullscreen,
            "set_wallpaper": self.set_as_wallpaper,
            "quick_wallpaper": self.quick_set_wallpaper,
            "copy": self.copy_to_clipboard,
            "save_as": self.save_as_dialog,
            "delete": self.delete_current_image,
            "properties": self.show_properties,
            "shortcuts": self.show_shortcuts,
            "about": self.show_about,
            "sort_name_asc": lambda: self._apply_sort(ImageCollection.SORT_NAME_ASC),
            "sort_name_desc": lambda: self._apply_sort(ImageCollection.SORT_NAME_DESC),
            "sort_date_desc": lambda: self._apply_sort(ImageCollection.SORT_DATE_DESC),
            "sort_date_asc": lambda: self._apply_sort(ImageCollection.SORT_DATE_ASC),
            "sort_size_desc": lambda: self._apply_sort(ImageCollection.SORT_SIZE_DESC),
        }

        # HeaderBar
        self.headerbar = AppHeaderBar(actions)
        self.set_titlebar(self.headerbar)

        # Main Layout
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root_vbox)

        # Notification banner / InfoBar
        self.infobar = Gtk.InfoBar()
        self.infobar.set_show_close_button(True)
        self.infobar.connect("response", lambda b, r: self.infobar.set_visible(False))
        self.infobar_label = Gtk.Label()
        self.infobar.get_content_area().add(self.infobar_label)
        self.infobar.set_no_show_all(True)
        root_vbox.pack_start(self.infobar, False, False, 0)

        # Overlay for Canvas + Floating HUD
        self.overlay = Gtk.Overlay()
        root_vbox.pack_start(self.overlay, True, True, 0)

        # Canvas
        self.canvas = ImageCanvas()
        self.canvas.on_zoom_changed = self._on_zoom_changed
        self.canvas.on_next_requested = self.next_image
        self.canvas.on_prev_requested = self.prev_image
        self.canvas.on_toggle_fullscreen = self.toggle_fullscreen
        self.canvas.on_context_menu = self._on_canvas_context_menu
        self.overlay.add(self.canvas)

        # Fullscreen Floating HUD Overlay
        self.floating_hud = FloatingOverlay(actions)
        self.floating_hud.set_no_show_all(True)
        self.overlay.add_overlay(self.floating_hud)

        # Filmstrip
        self.thumbnail_strip = ThumbnailStrip(on_select=self._on_thumbnail_selected)
        self.thumbnail_strip.set_no_show_all(True)
        root_vbox.pack_end(self.thumbnail_strip, False, False, 0)

    def _setup_drag_and_drop(self) -> None:
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect("drag-data-received", self._on_drag_data_received)

    def _on_drag_data_received(self, widget, context, x, y, data, info, time):
        uris = data.get_uris()
        if uris:
            first_uri = uris[0]
            try:
                filepath, _ = GLib.filename_from_uri(first_uri)
                if filepath:
                    self.open_path(filepath)
                    context.finish(True, False, time)
                    return
            except Exception as e:
                print(f"[FeatherView] DnD error: {e}")
        context.finish(False, False, time)

    def open_path(self, path: str) -> bool:
        """Loads a file or directory into FeatherView."""
        if not self.collection.load_path(path):
            self.show_notification(f"No supported images found in '{os.path.basename(path)}'", Gtk.MessageType.WARNING)
            return False

        if self.show_thumbnails:
            self.thumbnail_strip.load_files(self.collection.files, self.collection.current_index)

        self._display_current()
        return True

    def _display_current(self) -> None:
        path = self.collection.current_path
        if not path or not os.path.exists(path):
            self.canvas.set_image(None)
            self.headerbar.update_info("", -1, 0, 0, 0, 1.0)
            return

        # Check for animation
        ext = os.path.splitext(path)[1].lower()
        anim = None
        if ext == ".gif":
            anim = load_animation(path)

        pixbuf = load_pixbuf(path)
        if pixbuf:
            self.canvas.set_image(pixbuf, anim)
            w = pixbuf.get_width()
            h = pixbuf.get_height()
            fname = os.path.basename(path)
            self.headerbar.update_info(fname, self.collection.current_index, self.collection.count, w, h, self.canvas.zoom)
        else:
            self.show_notification(f"Could not decode image: {os.path.basename(path)}", Gtk.MessageType.ERROR)

        if self.show_thumbnails:
            self.thumbnail_strip.highlight_active(self.collection.current_index)

    def _on_zoom_changed(self, zoom: float) -> None:
        path = self.collection.current_path
        fname = os.path.basename(path) if path else ""
        ow, oh = self.canvas._get_oriented_size()
        self.headerbar.update_info(fname, self.collection.current_index, self.collection.count, ow, oh, zoom)

    def _on_thumbnail_selected(self, index: int) -> None:
        if self.collection.go_to_index(index):
            self._display_current()

    def _apply_sort(self, mode: str) -> None:
        self.collection.set_sort_mode(mode)
        if self.show_thumbnails:
            self.thumbnail_strip.load_files(self.collection.files, self.collection.current_index)
        self._display_current()

    def next_image(self) -> None:
        if self.collection.next():
            self._display_current()

    def prev_image(self) -> None:
        if self.collection.prev():
            self._display_current()

    def first_image(self) -> None:
        if self.collection.first():
            self._display_current()

    def last_image(self) -> None:
        if self.collection.last():
            self._display_current()

    def toggle_slideshow(self) -> None:
        if self.slideshow_active:
            self.stop_slideshow()
        else:
            self.start_slideshow()

    def start_slideshow(self) -> None:
        if self.collection.count <= 1:
            return
        self.slideshow_active = True
        self.headerbar.set_slideshow_active(True)
        self.floating_hud.set_slideshow_active(True)

        def step():
            if not self.slideshow_active:
                return False
            self.next_image()
            return True

        self.slideshow_timer_id = GLib.timeout_add_seconds(self.SLIDESHOW_INTERVAL, step)
        self.show_notification("Slideshow started (Press Space to pause)", Gtk.MessageType.INFO)

    def stop_slideshow(self) -> None:
        self.slideshow_active = False
        if self.slideshow_timer_id is not None:
            GLib.source_remove(self.slideshow_timer_id)
            self.slideshow_timer_id = None
        self.headerbar.set_slideshow_active(False)
        self.floating_hud.set_slideshow_active(False)
        self.show_notification("Slideshow paused", Gtk.MessageType.INFO)

    def toggle_thumbnails(self) -> None:
        self.show_thumbnails = not self.show_thumbnails
        if self.show_thumbnails:
            self.thumbnail_strip.load_files(self.collection.files, self.collection.current_index)
            self.thumbnail_strip.show_all()
        else:
            self.thumbnail_strip.hide()

    def toggle_fullscreen(self) -> None:
        if not self.is_fullscreen:
            self.fullscreen()
            self.is_fullscreen = True
            self.floating_hud.trigger_activity()
        else:
            self.unfullscreen()
            self.is_fullscreen = False
            self.floating_hud.hide()

    def _on_window_motion(self, widget, event: Gdk.EventMotion) -> bool:
        if self.is_fullscreen:
            self.floating_hud.trigger_activity()
        return False

    def copy_to_clipboard(self) -> None:
        if not self.canvas.pixbuf:
            return
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_image(self.canvas.pixbuf)
        clipboard.store()
        self.show_notification("Image copied to clipboard", Gtk.MessageType.INFO)

    def set_as_wallpaper(self) -> None:
        path = self.collection.current_path
        if not path:
            self.show_notification("No image loaded to set as wallpaper", Gtk.MessageType.WARNING)
            return
        SetWallpaperDialog(self, path, on_applied=self._on_wallpaper_applied)

    def quick_set_wallpaper(self) -> None:
        path = self.collection.current_path
        if not path:
            return
        success, msg = set_desktop_wallpaper(path, style="zoom")
        self._on_wallpaper_applied(success, msg)

    def _on_wallpaper_applied(self, success: bool, msg: str) -> None:
        m_type = Gtk.MessageType.INFO if success else Gtk.MessageType.WARNING
        self.show_notification(msg, m_type)

    def _on_canvas_context_menu(self, event: Gdk.EventButton) -> None:
        path = self.collection.current_path
        if not path:
            return

        menu = Gtk.Menu()

        item_wall = Gtk.MenuItem(label="Set as Desktop Wallpaper...")
        item_wall.connect("activate", lambda w: self.set_as_wallpaper())
        menu.append(item_wall)

        item_qwall = Gtk.MenuItem(label="Quick Set as Wallpaper (Fill Screen)")
        item_qwall.connect("activate", lambda w: self.quick_set_wallpaper())
        menu.append(item_qwall)

        menu.append(Gtk.SeparatorMenuItem())

        item_copy = Gtk.MenuItem(label="Copy Image (Ctrl+C)")
        item_copy.connect("activate", lambda w: self.copy_to_clipboard())
        menu.append(item_copy)

        item_rot_cw = Gtk.MenuItem(label="Rotate Clockwise (R)")
        item_rot_cw.connect("activate", lambda w: self.canvas.rotate_cw())
        menu.append(item_rot_cw)

        item_rot_ccw = Gtk.MenuItem(label="Rotate Counter-Clockwise (Shift+R)")
        item_rot_ccw.connect("activate", lambda w: self.canvas.rotate_ccw())
        menu.append(item_rot_ccw)

        menu.append(Gtk.SeparatorMenuItem())

        item_props = Gtk.MenuItem(label="Image Properties & EXIF (I)")
        item_props.connect("activate", lambda w: self.show_properties())
        menu.append(item_props)

        item_del = Gtk.MenuItem(label="Move to Trash (Delete)")
        item_del.connect("activate", lambda w: self.delete_current_image())
        menu.append(item_del)

        menu.show_all()
        menu.popup_at_pointer(event)

    def delete_current_image(self) -> None:
        path = self.collection.current_path
        if not path:
            return

        fname = os.path.basename(path)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Move '{fname}' to Trash?",
        )
        dialog.format_secondary_text("The file can be restored from the desktop Trash bin.")
        res = dialog.run()
        dialog.destroy()

        if res == Gtk.ResponseType.OK:
            try:
                gfile = Gio.File.new_for_path(path)
                gfile.trash()
                self.show_notification(f"Moved '{fname}' to Trash", Gtk.MessageType.INFO)
                self.collection.remove_current()
                if self.show_thumbnails:
                    self.thumbnail_strip.load_files(self.collection.files, self.collection.current_index)
                self._display_current()
            except Exception as e:
                self.show_notification(f"Failed to trash file: {e}", Gtk.MessageType.ERROR)

    def open_file_dialog(self) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Open Image",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        # Filters
        filter_img = Gtk.FileFilter()
        filter_img.set_name("All Supported Images")
        filter_img.add_pixbuf_formats()
        filter_img.add_pattern("*.webp")
        filter_img.add_pattern("*.svg")
        filter_img.add_pattern("*.avif")
        dialog.add_filter(filter_img)

        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        if self.collection.directory and os.path.isdir(self.collection.directory):
            dialog.set_current_folder(self.collection.directory)

        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            chosen = dialog.get_filename()
            dialog.destroy()
            if chosen:
                self.open_path(chosen)
        else:
            dialog.destroy()

    def open_folder_dialog(self) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Open Folder Containing Images",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        if self.collection.directory:
            dialog.set_current_folder(self.collection.directory)

        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            chosen = dialog.get_filename()
            dialog.destroy()
            if chosen:
                self.open_path(chosen)
        else:
            dialog.destroy()

    def save_as_dialog(self) -> None:
        if not self.canvas.pixbuf:
            return

        dialog = Gtk.FileChooserDialog(
            title="Save Image As",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)

        path = self.collection.current_path
        if path:
            dialog.set_current_folder(os.path.dirname(path))
            dialog.set_current_name(f"copy_{os.path.basename(path)}")

        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            dest = dialog.get_filename()
            dialog.destroy()
            if dest:
                ext = os.path.splitext(dest)[1].lower().lstrip(".")
                fmt = ext if ext in ["png", "jpeg", "ico", "bmp", "tiff"] else "png"
                if fmt == "jpg":
                    fmt = "jpeg"
                try:
                    self.canvas.pixbuf.savev(dest, fmt, [], [])
                    self.show_notification(f"Image saved: {os.path.basename(dest)}", Gtk.MessageType.INFO)
                except Exception as e:
                    self.show_notification(f"Error saving image: {e}", Gtk.MessageType.ERROR)
        else:
            dialog.destroy()

    def show_properties(self) -> None:
        path = self.collection.current_path
        if not path:
            return
        w = self.canvas.pixbuf.get_width() if self.canvas.pixbuf else None
        h = self.canvas.pixbuf.get_height() if self.canvas.pixbuf else None
        meta = get_image_metadata(path, w, h)
        ImagePropertiesDialog(self, meta)

    def show_shortcuts(self) -> None:
        ShortcutsDialog(self)

    def show_about(self) -> None:
        AboutDialog(self)

    def show_notification(self, text: str, message_type: Gtk.MessageType) -> None:
        self.infobar.set_message_type(message_type)
        self.infobar_label.set_text(text)
        self.infobar.set_visible(True)
        # Auto hide after 3 seconds
        GLib.timeout_add_seconds(3, lambda: self.infobar.set_visible(False))

    def _on_key_press(self, widget, event: Gdk.EventKey) -> bool:
        key = Gdk.keyval_name(event.keyval)
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(event.state & Gdk.ModifierType.SHIFT_MASK)

        # Ctrl combinations
        if ctrl:
            if key in ("b", "B") or (key in ("w", "W") and shift):
                self.set_as_wallpaper()
                return True
            elif key in ("o", "O"):
                self.open_file_dialog()
                return True
            elif key in ("s", "S"):
                self.save_as_dialog()
                return True
            elif key in ("c", "C"):
                self.copy_to_clipboard()
                return True
            elif key in ("q", "Q"):
                self.close()
                return True
            elif key in ("r", "R"):
                if shift:
                    self.canvas.rotate_ccw()
                else:
                    self.canvas.rotate_cw()
                return True

        # Standard navigation keys
        if key in ("Right", "Page_Down"):
            self.next_image()
            return True
        elif key in ("Left", "Page_Up"):
            self.prev_image()
            return True
        elif key == "Home":
            self.first_image()
            return True
        elif key == "End":
            self.last_image()
            return True
        elif key == "space":
            self.toggle_slideshow()
            return True

        # Zoom keys
        elif key in ("plus", "equal", "KP_Add"):
            self.canvas.zoom_in()
            return True
        elif key in ("minus", "KP_Subtract"):
            self.canvas.zoom_out()
            return True
        elif key in ("0", "1", "KP_0", "KP_1"):
            self.canvas.set_actual_size()
            return True
        elif key in ("w", "W", "f", "F") and not self.is_fullscreen:
            self.canvas.set_fit_auto()
            return True

        # Transforms
        elif key in ("r", "R"):
            if shift:
                self.canvas.rotate_ccw()
            else:
                self.canvas.rotate_cw()
            return True
        elif key in ("h", "H"):
            self.canvas.toggle_flip_h()
            return True
        elif key in ("v", "V"):
            self.canvas.toggle_flip_v()
            return True

        # Views & Toggles
        elif key == "F11":
            self.toggle_fullscreen()
            return True
        elif key == "Escape":
            if self.is_fullscreen:
                self.toggle_fullscreen()
                return True
        elif key in ("t", "T"):
            self.toggle_thumbnails()
            return True
        elif key in ("i", "I"):
            self.show_properties()
            return True
        elif key in ("question", "slash") and shift:
            self.show_shortcuts()
            return True
        elif key == "Delete":
            self.delete_current_image()
            return True

        return False

    def _on_destroy(self, widget) -> None:
        self.stop_slideshow()


class FeatherViewApp(Gtk.Application):
    """The Gtk.Application instance."""

    def __init__(self, target_path: Optional[str] = None, slideshow: bool = False, fullscreen: bool = False):
        super().__init__(
            application_id=__app_id__,
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.target_path = target_path
        self.initial_slideshow = slideshow
        self.initial_fullscreen = fullscreen
        self.window: Optional[FeatherViewWindow] = None

    def do_activate(self) -> None:
        if not self.window:
            self.window = FeatherViewWindow(self)

        self.window.show_all()
        self.window.present()

        if self.target_path:
            self.window.open_path(self.target_path)

        if self.initial_fullscreen:
            self.window.toggle_fullscreen()

        if self.initial_slideshow:
            self.window.start_slideshow()

    def do_open(self, files: list, n_files: int, hint: str) -> None:
        self.activate()
        if files and self.window:
            path = files[0].get_path()
            if path:
                self.window.open_path(path)


def main():
    parser = argparse.ArgumentParser(description=f"{__app_name__} - Ultra-lightweight image viewer for Linux desktop")
    parser.add_argument("path", nargs="?", default=None, help="Image file or directory path to open")
    parser.add_argument("-s", "--slideshow", action="store_true", help="Start immediately in slideshow mode")
    parser.add_argument("-f", "--fullscreen", action="store_true", help="Start immediately in fullscreen mode")
    parser.add_argument("-v", "--version", action="version", version=f"{__app_name__} {__version__}")

    args = parser.parse_args()

    app = FeatherViewApp(
        target_path=args.path,
        slideshow=args.slideshow,
        fullscreen=args.fullscreen,
    )
    sys.exit(app.run([sys.argv[0]]))


if __name__ == "__main__":
    main()
