"""High-performance Cairo-based image rendering canvas with zooming, panning, and animations."""

import math
from typing import Callable, Optional

import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk


class ImageCanvas(Gtk.DrawingArea):
    """Interactive canvas widget for high-performance image display."""

    FIT_AUTO = 0
    FIT_ORIGINAL = 1
    FIT_CUSTOM = 2

    MIN_ZOOM = 0.05
    MAX_ZOOM = 50.0

    def __init__(self):
        super().__init__()

        self.pixbuf: Optional[GdkPixbuf.Pixbuf] = None
        self.original_pixbuf: Optional[GdkPixbuf.Pixbuf] = None
        self.animation: Optional[GdkPixbuf.PixbufAnimation] = None
        self.anim_iter: Optional[GdkPixbuf.PixbufAnimationIter] = None
        self.anim_timer_id: Optional[int] = None

        self.fit_mode = self.FIT_AUTO
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        self.rotation = 0  # 0, 90, 180, 270
        self.flip_h = False
        self.flip_v = False

        self.is_dragging = False
        self.drag_start_x = 0.0
        self.drag_start_y = 0.0
        self.drag_base_offset_x = 0.0
        self.drag_base_offset_y = 0.0

        # Callbacks
        self.on_zoom_changed: Optional[Callable[[float], None]] = None
        self.on_next_requested: Optional[Callable[[], None]] = None
        self.on_prev_requested: Optional[Callable[[], None]] = None
        self.on_toggle_fullscreen: Optional[Callable[[], None]] = None

        # Event masks
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.SMOOTH_SCROLL_MASK
        )

        self.connect("draw", self._on_draw)
        self.connect("size-allocate", self._on_size_allocate)
        self.connect("button-press-event", self._on_button_press)
        self.connect("button-release-event", self._on_button_release)
        self.connect("motion-notify-event", self._on_motion_notify)
        self.connect("scroll-event", self._on_scroll)

        self.set_can_focus(True)

    def set_image(self, pixbuf: Optional[GdkPixbuf.Pixbuf], anim: Optional[GdkPixbuf.PixbufAnimation] = None) -> None:
        """Sets the active image or animation to render."""
        self._stop_animation()

        self.original_pixbuf = pixbuf
        self.pixbuf = pixbuf
        self.animation = anim
        self.rotation = 0
        self.flip_h = False
        self.flip_v = False

        if anim and not anim.is_static_image():
            self._start_animation()

        self.fit_mode = self.FIT_AUTO
        self._recalculate_fit()
        self.queue_draw()

    def _start_animation(self) -> None:
        if not self.animation:
            return
        self.anim_iter = self.animation.get_iter(GLib.get_current_time())
        self._step_animation()

    def _stop_animation(self) -> None:
        if self.anim_timer_id is not None:
            GLib.source_remove(self.anim_timer_id)
            self.anim_timer_id = None
        self.anim_iter = None

    def _step_animation(self) -> bool:
        if not self.anim_iter:
            return False

        self.pixbuf = self.anim_iter.get_pixbuf()
        self.queue_draw()

        delay = self.anim_iter.get_delay_time()
        if delay <= 0:
            delay = 100  # Default 100ms if not specified

        def on_timeout():
            if not self.anim_iter:
                return False
            time_now = GLib.get_current_time()
            self.anim_iter.advance(time_now)
            return self._step_animation()

        self.anim_timer_id = GLib.timeout_add(delay, on_timeout)
        return False  # Handled by next timeout

    def _get_oriented_size(self) -> tuple[int, int]:
        if not self.pixbuf:
            return 0, 0
        w, h = self.pixbuf.get_width(), self.pixbuf.get_height()
        if self.rotation in (90, 270):
            return h, w
        return w, h

    def _recalculate_fit(self) -> None:
        if not self.pixbuf:
            return
        alloc = self.get_allocation()
        win_w, win_h = alloc.width, alloc.height
        if win_w <= 1 or win_h <= 1:
            return

        ow, oh = self._get_oriented_size()
        if ow <= 0 or oh <= 0:
            return

        if self.fit_mode == self.FIT_AUTO:
            scale_x = win_w / ow
            scale_y = win_h / oh
            self.zoom = min(scale_x, scale_y)
            # Center image
            self.offset_x = (win_w - (ow * self.zoom)) / 2.0
            self.offset_y = (win_h - (oh * self.zoom)) / 2.0
        elif self.fit_mode == self.FIT_ORIGINAL:
            self.zoom = 1.0
            self.offset_x = (win_w - ow) / 2.0
            self.offset_y = (win_h - oh) / 2.0

        self._notify_zoom()

    def _notify_zoom(self) -> None:
        if self.on_zoom_changed:
            self.on_zoom_changed(self.zoom)

    def _on_size_allocate(self, widget, allocation):
        if self.fit_mode == self.FIT_AUTO:
            self._recalculate_fit()

    def set_fit_auto(self) -> None:
        self.fit_mode = self.FIT_AUTO
        self._recalculate_fit()
        self.queue_draw()

    def set_actual_size(self) -> None:
        self.fit_mode = self.FIT_ORIGINAL
        self._recalculate_fit()
        self.queue_draw()

    def zoom_in(self, factor: float = 1.25) -> None:
        alloc = self.get_allocation()
        self.zoom_at(alloc.width / 2.0, alloc.height / 2.0, self.zoom * factor)

    def zoom_out(self, factor: float = 1.25) -> None:
        alloc = self.get_allocation()
        self.zoom_at(alloc.width / 2.0, alloc.height / 2.0, self.zoom / factor)

    def zoom_at(self, cursor_x: float, cursor_y: float, new_zoom: float) -> None:
        """Zooms into/out of a specific canvas coordinate (mouse-centered zoom)."""
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, new_zoom))
        if abs(new_zoom - self.zoom) < 1e-5:
            return

        # Coordinate relative to image origin before zoom
        rel_x = (cursor_x - self.offset_x) / self.zoom
        rel_y = (cursor_y - self.offset_y) / self.zoom

        self.zoom = new_zoom
        self.fit_mode = self.FIT_CUSTOM

        # Adjust offset so that (rel_x, rel_y) remains at (cursor_x, cursor_y)
        self.offset_x = cursor_x - (rel_x * self.zoom)
        self.offset_y = cursor_y - (rel_y * self.zoom)

        self._notify_zoom()
        self.queue_draw()

    def rotate_cw(self) -> None:
        self.rotation = (self.rotation + 90) % 360
        self._recalculate_fit()
        self.queue_draw()

    def rotate_ccw(self) -> None:
        self.rotation = (self.rotation - 90 + 360) % 360
        self._recalculate_fit()
        self.queue_draw()

    def toggle_flip_h(self) -> None:
        self.flip_h = not self.flip_h
        self.queue_draw()

    def toggle_flip_v(self) -> None:
        self.flip_v = not self.flip_v
        self.queue_draw()

    def _draw_checkerboard(self, cr: cairo.Context, w: int, h: int) -> None:
        """Draws subtle modern dark checkerboard for alpha transparency."""
        cr.set_source_rgb(0.10, 0.10, 0.12)  # Dark slate base
        cr.paint()

        cr.set_source_rgb(0.14, 0.14, 0.16)
        square = 16
        for y in range(0, h, square):
            offset = 0 if (y // square) % 2 == 0 else square
            for x in range(offset, w, square * 2):
                cr.rectangle(x, y, square, square)
        cr.fill()

    def _on_draw(self, widget, cr: cairo.Context) -> bool:
        alloc = self.get_allocation()
        win_w, win_h = alloc.width, alloc.height

        # Fill background
        self._draw_checkerboard(cr, win_w, win_h)

        if not self.pixbuf:
            # Draw placeholder when empty
            cr.set_source_rgb(0.4, 0.4, 0.45)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(16.0)
            msg = "No image loaded (Drop an image here or press Open)"
            extents = cr.text_extents(msg)
            cr.move_to((win_w - extents.width) / 2.0, (win_h + extents.height) / 2.0)
            cr.show_text(msg)
            return True

        pw = self.pixbuf.get_width()
        ph = self.pixbuf.get_height()

        cr.save()

        # Set interpolation filter
        if self.zoom > 2.0:
            pattern = cr.get_source()
            if pattern:
                pattern.set_filter(cairo.FILTER_NEAREST)
        else:
            pattern = cr.get_source()
            if pattern:
                pattern.set_filter(cairo.FILTER_BILINEAR)

        # Apply transformations:
        # Translate to current canvas offset
        cr.translate(self.offset_x, self.offset_y)
        cr.scale(self.zoom, self.zoom)

        # Center rotation/flip on image center
        cx = pw / 2.0
        cy = ph / 2.0

        if self.rotation != 0 or self.flip_h or self.flip_v:
            ow, oh = self._get_oriented_size()
            ocx = ow / 2.0
            ocy = oh / 2.0
            cr.translate(ocx, ocy)

            if self.rotation != 0:
                cr.rotate(math.radians(self.rotation))
            if self.flip_h:
                cr.scale(-1, 1)
            if self.flip_v:
                cr.scale(1, -1)

            cr.translate(-cx, -cy)

        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.paint()
        cr.restore()

        return True

    def _on_button_press(self, widget, event: Gdk.EventButton) -> bool:
        if event.button == 1:  # Left click
            if event.type == Gdk.EventType._2BUTTON_PRESS:  # Double click
                if self.on_toggle_fullscreen:
                    self.on_toggle_fullscreen()
                return True
            # Start panning
            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.drag_base_offset_x = self.offset_x
            self.drag_base_offset_y = self.offset_y
            self.get_window().set_cursor(Gdk.Cursor.new_from_name(self.get_display(), "grabbing"))
            return True
        elif event.button == 2:  # Middle click
            self.set_fit_auto()
            return True
        elif event.button == 8 or event.button == 9:  # Mouse back/forward buttons
            if event.button == 8 and self.on_prev_requested:
                self.on_prev_requested()
            elif event.button == 9 and self.on_next_requested:
                self.on_next_requested()
            return True
        return False

    def _on_button_release(self, widget, event: Gdk.EventButton) -> bool:
        if event.button == 1:
            self.is_dragging = False
            self.get_window().set_cursor(None)
            return True
        return False

    def _on_motion_notify(self, widget, event: Gdk.EventMotion) -> bool:
        if self.is_dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            self.offset_x = self.drag_base_offset_x + dx
            self.offset_y = self.drag_base_offset_y + dy
            self.queue_draw()
            return True
        return False

    def _on_scroll(self, widget, event: Gdk.EventScroll) -> bool:
        # Check if Ctrl is held for zoom, or default scroll wheel behavior
        state = event.state
        ctrl_pressed = bool(state & Gdk.ModifierType.CONTROL_MASK)

        direction = event.direction
        if direction == Gdk.ScrollDirection.SMOOTH:
            _, dx, dy = event.get_scroll_deltas()
            zoom_multiplier = 1.0 - (dy * 0.15)
            self.zoom_at(event.x, event.y, self.zoom * zoom_multiplier)
            return True
        elif direction == Gdk.ScrollDirection.UP:
            if ctrl_pressed or self.fit_mode == self.FIT_CUSTOM:
                self.zoom_at(event.x, event.y, self.zoom * 1.15)
            else:
                if self.on_prev_requested:
                    self.on_prev_requested()
            return True
        elif direction == Gdk.ScrollDirection.DOWN:
            if ctrl_pressed or self.fit_mode == self.FIT_CUSTOM:
                self.zoom_at(event.x, event.y, self.zoom / 1.15)
            else:
                if self.on_next_requested:
                    self.on_next_requested()
            return True
        return False
