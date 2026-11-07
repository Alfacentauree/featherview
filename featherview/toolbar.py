"""HeaderBar, menu, and floating overlay toolbar components."""

from typing import Any, Callable, Dict, Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")
from gi.repository import GLib, Gtk


def create_icon_btn(icon_name: str, tooltip: str, callback: Optional[Callable[[], None]] = None) -> Gtk.Button:
    """Helper to create a standard icon button with tooltip."""
    btn = Gtk.Button.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
    btn.set_tooltip_text(tooltip)
    btn.set_can_focus(False)
    if callback:
        btn.connect("clicked", lambda b: callback())
    return btn


class AppHeaderBar(Gtk.HeaderBar):
    """The modern top HeaderBar for FeatherView."""

    def __init__(self, actions: Dict[str, Callable[[], None]]):
        super().__init__()
        self.actions = actions

        self.set_show_close_button(True)
        self.set_title("FeatherView")
        self.set_subtitle("Ultra-lightweight Image Viewer")

        self._build_left_section()
        self._build_right_section()

    def _build_left_section(self) -> None:
        # Open file
        btn_open = create_icon_btn("document-open", "Open Image or Folder (Ctrl+O)", self.actions.get("open"))
        self.pack_start(btn_open)

        # Prev / Next
        self.btn_prev = create_icon_btn("go-previous", "Previous Image (Left Arrow)", self.actions.get("prev"))
        self.btn_next = create_icon_btn("go-next", "Next Image (Right Arrow)", self.actions.get("next"))
        self.pack_start(self.btn_prev)
        self.pack_start(self.btn_next)

        # Counter badge
        self.lbl_counter = Gtk.Label(label="")
        self.lbl_counter.get_style_context().add_class("dim-label")
        self.lbl_counter.set_margin_start(6)
        self.pack_start(self.lbl_counter)

    def _build_right_section(self) -> None:
        # Zoom controls
        btn_zoom_out = create_icon_btn("zoom-out", "Zoom Out (-)", self.actions.get("zoom_out"))
        btn_zoom_fit = create_icon_btn("zoom-fit-best", "Fit to Window (W / F)", self.actions.get("zoom_fit"))
        btn_zoom_100 = create_icon_btn("zoom-original", "Actual Size 1:1 (0 / 1)", self.actions.get("zoom_100"))
        btn_zoom_in = create_icon_btn("zoom-in", "Zoom In (+)", self.actions.get("zoom_in"))

        self.pack_end(self._create_menu_button())
        self.btn_fullscreen = create_icon_btn("view-fullscreen", "Toggle Fullscreen (F11)", self.actions.get("fullscreen"))
        self.pack_end(self.btn_fullscreen)

        self.btn_filmstrip = create_icon_btn("view-list-icons", "Toggle Thumbnails (T)", self.actions.get("thumbnails"))
        self.pack_end(self.btn_filmstrip)

        self.btn_slideshow = create_icon_btn("media-playback-start", "Play Slideshow (Space)", self.actions.get("slideshow"))
        self.pack_end(self.btn_slideshow)

        # Rotate buttons
        btn_rot_cw = create_icon_btn("object-rotate-right", "Rotate Clockwise (R)", self.actions.get("rotate_cw"))
        btn_flip_h = create_icon_btn("object-flip-horizontal", "Flip Horizontal (H)", self.actions.get("flip_h"))

        self.pack_end(btn_flip_h)
        self.pack_end(btn_rot_cw)
        self.pack_end(btn_zoom_in)
        self.pack_end(btn_zoom_100)
        self.pack_end(btn_zoom_fit)
        self.pack_end(btn_zoom_out)

    def _create_menu_button(self) -> Gtk.MenuButton:
        menu_btn = Gtk.MenuButton()
        menu_btn.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        menu_btn.set_tooltip_text("Menu")

        menu = Gtk.Menu()

        def add_item(label: str, action_key: str):
            item = Gtk.MenuItem(label=label)
            item.connect("activate", lambda i: self.actions.get(action_key, lambda: None)())
            menu.append(item)

        add_item("Open File... (Ctrl+O)", "open")
        add_item("Open Folder...", "open_folder")
        menu.append(Gtk.SeparatorMenuItem())
        add_item("Set as Desktop Wallpaper", "set_wallpaper")
        add_item("Copy Image to Clipboard (Ctrl+C)", "copy")
        add_item("Save / Export As... (Ctrl+S)", "save_as")
        add_item("Move to Trash (Delete)", "delete")
        menu.append(Gtk.SeparatorMenuItem())

        # Sort submenu
        sort_item = Gtk.MenuItem(label="Sort Images By")
        sort_menu = Gtk.Menu()
        sort_modes = [
            ("Name (A to Z)", "sort_name_asc"),
            ("Name (Z to A)", "sort_name_desc"),
            ("Date (Newest First)", "sort_date_desc"),
            ("Date (Oldest First)", "sort_date_asc"),
            ("Size (Largest First)", "sort_size_desc"),
        ]
        for s_label, s_action in sort_modes:
            sm_item = Gtk.MenuItem(label=s_label)
            sm_item.connect("activate", lambda w, a=s_action: self.actions.get(a, lambda: None)())
            sort_menu.append(sm_item)
        sort_item.set_submenu(sort_menu)
        menu.append(sort_item)

        menu.append(Gtk.SeparatorMenuItem())
        add_item("Image Properties / EXIF (I)", "properties")
        add_item("Keyboard Shortcuts (?)", "shortcuts")
        add_item("About FeatherView", "about")

        menu.show_all()
        menu_btn.set_popup(menu)
        return menu_btn

    def update_info(self, filename: str, index: int, total: int, width: int, height: int, zoom: float) -> None:
        self.set_title(filename if filename else "FeatherView")
        zoom_pct = int(round(zoom * 100))
        if width > 0 and height > 0:
            self.set_subtitle(f"{width} × {height} px  •  {zoom_pct}%")
        else:
            self.set_subtitle("FeatherView")

        if total > 0:
            self.lbl_counter.set_text(f"{index + 1} / {total}")
        else:
            self.lbl_counter.set_text("")

    def set_slideshow_active(self, active: bool) -> None:
        icon_name = "media-playback-pause" if active else "media-playback-start"
        self.btn_slideshow.set_image(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON))


class FloatingOverlay(Gtk.Box):
    """Floating translucent HUD toolbar that auto-hides during fullscreen playback."""

    def __init__(self, actions: Dict[str, Callable[[], None]]):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.actions = actions
        self.hide_timer_id: Optional[int] = None

        self.get_style_context().add_class("floating-overlay")
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.END)
        self.set_margin_bottom(24)

        # Controls
        self.btn_prev = create_icon_btn("go-previous", "Previous", actions.get("prev"))
        self.btn_play = create_icon_btn("media-playback-start", "Play/Pause Slideshow", actions.get("slideshow"))
        self.btn_next = create_icon_btn("go-next", "Next", actions.get("next"))
        btn_fit = create_icon_btn("zoom-fit-best", "Fit Window", actions.get("zoom_fit"))
        btn_in = create_icon_btn("zoom-in", "Zoom In", actions.get("zoom_in"))
        btn_out = create_icon_btn("zoom-out", "Zoom Out", actions.get("zoom_out"))
        btn_exit = create_icon_btn("view-restore", "Exit Fullscreen (Esc)", actions.get("fullscreen"))

        self.pack_start(self.btn_prev, False, False, 0)
        self.pack_start(self.btn_play, False, False, 0)
        self.pack_start(self.btn_next, False, False, 0)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4)
        self.pack_start(btn_fit, False, False, 0)
        self.pack_start(btn_out, False, False, 0)
        self.pack_start(btn_in, False, False, 0)
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4)
        self.pack_start(btn_exit, False, False, 0)

    def trigger_activity(self) -> None:
        """Shows the floating HUD and resets auto-hide timer."""
        self.set_visible(True)
        if self.hide_timer_id is not None:
            GLib.source_remove(self.hide_timer_id)

        def do_hide():
            self.set_visible(False)
            self.hide_timer_id = None
            return False

        self.hide_timer_id = GLib.timeout_add(2500, do_hide)

    def set_slideshow_active(self, active: bool) -> None:
        icon_name = "media-playback-pause" if active else "media-playback-start"
        self.btn_play.set_image(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON))
