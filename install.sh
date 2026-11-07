#!/usr/bin/env bash
set -e

echo "=========================================="
echo "    Installing FeatherView Image Viewer   "
echo "=========================================="

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# 1. Ensure latest compilation
if [ ! -f "$APP_DIR/dist/featherview" ]; then
    echo "--> Compiling standalone binary..."
    "$APP_DIR/build.sh"
fi

# 2. Install binary to ~/.local/bin
echo "--> Installing binary to $BIN_DIR/featherview"
cp "$APP_DIR/dist/featherview" "$BIN_DIR/featherview"
chmod +x "$BIN_DIR/featherview"

# 3. Install Desktop Icon
echo "--> Installing application icon to $ICON_DIR"
cp "$APP_DIR/data/icons/featherview.svg" "$ICON_DIR/featherview.svg"

# 4. Install Desktop Entry
echo "--> Installing desktop entry to $DESKTOP_DIR"
sed -e "s|Exec=featherview|Exec=$BIN_DIR/featherview|g" \
    "$APP_DIR/data/featherview.desktop" > "$DESKTOP_DIR/featherview.desktop"
chmod +x "$DESKTOP_DIR/featherview.desktop"

# 5. Update desktop & icon caches
if command -v update-desktop-database >/dev/null 2>&1; then
    echo "--> Updating desktop database..."
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    echo "--> Updating icon cache..."
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

# 6. Set FeatherView as Default Image Viewer
echo "--> Setting FeatherView as default image viewer..."
MIME_TYPES=(
    "image/jpeg"
    "image/jpg"
    "image/png"
    "image/webp"
    "image/gif"
    "image/bmp"
    "image/tiff"
    "image/svg+xml"
    "image/avif"
    "image/heif"
    "image/x-tga"
    "image/x-bmp"
    "image/x-png"
    "image/x-portable-anymap"
    "image/x-portable-bitmap"
    "image/x-portable-graymap"
    "image/x-portable-pixmap"
    "image/x-xbitmap"
    "image/x-xpixmap"
    "image/x-icns"
    "image/x-icon"
    "image/vnd.microsoft.icon"
)

for mime in "${MIME_TYPES[@]}"; do
    if command -v gio >/dev/null 2>&1; then
        gio mime "$mime" featherview.desktop >/dev/null 2>&1 || true
    fi
    if command -v xdg-mime >/dev/null 2>&1; then
        xdg-mime default featherview.desktop "$mime" >/dev/null 2>&1 || true
    fi
done

echo "=========================================="
echo "  FeatherView successfully installed!     "
echo "  ✓ Set as Default Image Viewer           "
echo "  ✓ Installed binary: $BIN_DIR/featherview"
echo "  ✓ Desktop icon and launcher registered  "
echo "=========================================="
