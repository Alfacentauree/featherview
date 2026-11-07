# 🪶 FeatherView

An ultra-lightweight, blazing-fast, modern image viewer engineered specifically for the Linux desktop.

Built with Python 3, GTK 3, and Cairo, **FeatherView** starts up in under **100ms** and consumes minimal memory (~35MB RAM), delivering instant navigation, sub-pixel smooth panning, cursor-centered zooming, and comprehensive Linux desktop integration.

---

## ✨ Features

- **⚡ Blazing Fast & Lightweight**: Zero Chromium, zero Electron bloat. Starts up instantaneously with a lean memory footprint.
- **🔍 Mouse-Centered Zooming**: Zoom in and out precisely focused on your cursor position with the scroll wheel (from 5% to 5,000%).
- **✋ Smooth Panning**: Click and drag to fluidly pan across high-resolution photos.
- **🎞️ Asynchronous Thumbnail Filmstrip**: Fast, non-blocking preview bar at the bottom with instant jump and smooth auto-scrolling.
- **🔄 Instant Transformations**: 90° Clockwise/Counter-Clockwise rotations, horizontal and vertical flips.
- **🎬 Slideshow Mode**: Auto-advancing full-screen or windowed slideshow.
- **🖥️ Desktop Wallpaper Integration**: One-click wallpaper setter supporting Cinnamon, GNOME, XFCE, MATE, KDE Plasma, and window managers.
- **📋 Clipboard Integration**: Copy any active image directly to system clipboard (`Ctrl+C`).
- **ℹ️ EXIF & Properties Inspector**: Detailed breakdown of dimensions, megapixel count, aspect ratio, camera make/model, shutter speed, aperture, ISO, and focal length.
- **🗑️ Safe File Management**: Move unwanted images straight to the desktop Trash bin with confirmation (`Delete`).
- **🎨 Sleek Dark Modern Interface**: Minimalist Adwaita-style dark aesthetic with auto-hiding translucent HUD overlay in fullscreen.
- **📦 Wide Format Support**: PNG, JPEG, WebP, GIF (including animated playback), SVG, BMP, TIFF, ICO, AVIF, PNM, TGA, etc.
- **🗂️ Drag & Drop**: Drop images or folders directly into the window from any file manager.

---

## ⌨️ Keyboard & Mouse Shortcuts

| Category | Shortcut | Action |
| :--- | :--- | :--- |
| **Navigation** | `Right Arrow` / `Page Down` | Next image in folder |
| | `Left Arrow` / `Page Up` | Previous image in folder |
| | `Home` / `End` | Jump to first / last image |
| | `Spacebar` | Play / Pause slideshow |
| **Zoom & Pan** | `Scroll Wheel` | Zoom centered at mouse cursor |
| | `+` or `=` | Zoom In |
| | `-` | Zoom Out |
| | `0` or `1` | Actual Size (100% 1:1) |
| | `W` or `F` | Fit image to window |
| | `Left Click Drag` | Pan around zoomed image |
| | `Middle Click` | Reset zoom to Fit |
| **Transformations** | `R` | Rotate 90° Clockwise |
| | `Shift + R` | Rotate 90° Counter-Clockwise |
| | `H` | Flip Horizontal |
| | `V` | Flip Vertical |
| **View Modes** | `F11` / `Double Click` | Toggle Fullscreen |
| | `T` | Toggle Thumbnail Filmstrip |
| | `I` | Toggle Image Properties & EXIF |
| | `?` | Keyboard Shortcuts dialog |
| | `Esc` | Exit Fullscreen |
| **File Actions** | `Ctrl + O` | Open Image or Folder |
| | `Ctrl + S` | Save / Export As... |
| | `Ctrl + C` | Copy image to clipboard |
| | `Delete` | Move image to Trash |
| | `Ctrl + Q` | Quit FeatherView |

---

## 🚀 Installation

### One-line Quick Install
Run the provided installer script from the repository:

```bash
cd /home/add/Desktop/Github/featherview
./install.sh
```

This installs:
- Executable to `~/.local/bin/featherview`
- Desktop launcher into `~/.local/share/applications/featherview.desktop`
- Scalable SVG icon into `~/.local/share/icons/hicolor/scalable/apps/featherview.svg`
- Updates desktop application and icon caches

FeatherView will immediately appear in your desktop application launcher (under **Graphics** / **Image Viewer**) and can be set as your system's default image viewer!

### Running Without Installing
You can also launch directly from the repository:

```bash
./bin/featherview [optional_image_or_folder]
```

---

## 💻 Command Line Usage

```bash
# Open an image
featherview photo.jpg

# Open a folder
featherview ~/Pictures

# Start immediately in fullscreen mode
featherview -f photo.jpg

# Start immediately in slideshow mode
featherview -s ~/Pictures

# Check version
featherview --version
```

---

## 🧪 Running Tests

The test suite covers natural sorting, collection navigation, metadata/EXIF extraction, and canvas geometry:

```bash
python3 -m unittest discover tests
```

---

## 🗑️ Uninstallation

To cleanly remove FeatherView from your system:

```bash
./uninstall.sh
```

---

## 📄 License

FeatherView is open-source software licensed under the [MIT License](LICENSE).
