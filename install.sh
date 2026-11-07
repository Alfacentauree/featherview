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

# 1. Install binary to ~/.local/bin
echo "--> Installing binary to $BIN_DIR/featherview"
if [ -f "$APP_DIR/dist/featherview" ]; then
    cp "$APP_DIR/dist/featherview" "$BIN_DIR/featherview"
else
    cat << EOF > "$BIN_DIR/featherview"
#!/usr/bin/env bash
export PYTHONPATH="$APP_DIR:\$PYTHONPATH"
exec python3 -m featherview.app "\$@"
EOF
fi
chmod +x "$BIN_DIR/featherview"

# 2. Install Desktop Icon
echo "--> Installing application icon to $ICON_DIR"
cp "$APP_DIR/data/icons/featherview.svg" "$ICON_DIR/featherview.svg"

# 3. Install Desktop Entry
echo "--> Installing desktop entry to $DESKTOP_DIR"
sed -e "s|Exec=featherview|Exec=$BIN_DIR/featherview|g" \
    "$APP_DIR/data/featherview.desktop" > "$DESKTOP_DIR/featherview.desktop"
chmod +x "$DESKTOP_DIR/featherview.desktop"

# 4. Update desktop & icon caches
if command -v update-desktop-database >/dev/null 2>&1; then
    echo "--> Updating desktop database..."
    update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    echo "--> Updating icon cache..."
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "=========================================="
echo "  FeatherView successfully installed!     "
echo "  Run via terminal:  featherview <image>  "
echo "  Or find 'FeatherView' in your app menu. "
echo "=========================================="
