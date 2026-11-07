#!/usr/bin/env bash
set -e

echo "=================================================="
echo "         Compiling FeatherView Linux App          "
echo "=================================================="

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$BASE_DIR/dist"
BUILD_DIR="$BASE_DIR/build"

# Clean build and dist
rm -rf "$DIST_DIR" "$BUILD_DIR"
mkdir -p "$DIST_DIR" "$BUILD_DIR"

# -------------------------------------------------------------------------
# 1. Compile Python Bytecode (.pyc)
# -------------------------------------------------------------------------
echo "[1/4] Compiling Python source to optimized bytecode..."
python3 -O -m compileall -q "$BASE_DIR/featherview"

# -------------------------------------------------------------------------
# 2. Compile Standalone Single-File Executable (ZipApp)
# -------------------------------------------------------------------------
echo "[2/4] Building standalone single-file executable: dist/featherview..."
STAGE_ZIPAPP="$BUILD_DIR/zipapp_staging"
mkdir -p "$STAGE_ZIPAPP"
cp -r "$BASE_DIR/featherview" "$STAGE_ZIPAPP/"
cat << 'EOF' > "$STAGE_ZIPAPP/__main__.py"
from featherview.app import main
if __name__ == "__main__":
    main()
EOF

python3 -m zipapp "$STAGE_ZIPAPP" \
    -o "$DIST_DIR/featherview" \
    -p "/usr/bin/env python3" \
    --compress

chmod +x "$DIST_DIR/featherview"

# -------------------------------------------------------------------------
# 3. Compile Native C ELF Binary Launcher (with GCC)
# -------------------------------------------------------------------------
echo "[3/4] Compiling native C ELF binary: dist/featherview-native..."
if command -v gcc >/dev/null 2>&1; then
    gcc -O2 -Wall "$BASE_DIR/src/main.c" -o "$DIST_DIR/featherview-native"
    strip "$DIST_DIR/featherview-native"
    chmod +x "$DIST_DIR/featherview-native"
fi

# -------------------------------------------------------------------------
# 4. Build Debian Package (.deb)
# -------------------------------------------------------------------------
echo "[4/4] Building Debian/Ubuntu package: dist/featherview_1.0.0_all.deb..."
DEB_STAGE="$BUILD_DIR/deb_staging"
mkdir -p "$DEB_STAGE/DEBIAN"
mkdir -p "$DEB_STAGE/usr/bin"
mkdir -p "$DEB_STAGE/usr/lib/featherview"
mkdir -p "$DEB_STAGE/usr/share/applications"
mkdir -p "$DEB_STAGE/usr/share/icons/hicolor/scalable/apps"

# Control file
cat << 'EOF' > "$DEB_STAGE/DEBIAN/control"
Package: featherview
Version: 1.0.0
Section: graphics
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0, python3-pil
Maintainer: FeatherView Developers <info@featherview.org>
Description: Ultra-lightweight, blazing-fast image viewer for Linux desktop
 FeatherView is an ultra-fast modern image viewer engineered for Linux desktop.
 Features smooth mouse-centered zoom, smooth panning, rotation, slideshow,
 desktop wallpaper setup with live preview, and thumbnail filmstrip.
EOF

# Postinst & postrm scripts
cat << 'EOF' > "$DEB_STAGE/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 755 "$DEB_STAGE/DEBIAN/postinst"

cat << 'EOF' > "$DEB_STAGE/DEBIAN/postrm"
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 755 "$DEB_STAGE/DEBIAN/postrm"

# Copy files
cp -r "$BASE_DIR/featherview" "$DEB_STAGE/usr/lib/featherview/"
cp "$DIST_DIR/featherview" "$DEB_STAGE/usr/bin/featherview"
cp "$BASE_DIR/data/featherview.desktop" "$DEB_STAGE/usr/share/applications/"
cp "$BASE_DIR/data/icons/featherview.svg" "$DEB_STAGE/usr/share/icons/hicolor/scalable/apps/"

dpkg-deb --build --root-owner-group "$DEB_STAGE" "$DIST_DIR/featherview_1.0.0_all.deb" >/dev/null

# Clean build staging
rm -rf "$BUILD_DIR"

echo "=================================================="
echo "              Compilation Successful!             "
echo "=================================================="
echo "Artifacts generated in $DIST_DIR:"
ls -lh "$DIST_DIR"
echo "=================================================="
echo "1. Run Standalone Binary directly:"
echo "   $DIST_DIR/featherview [image]"
echo ""
echo "2. Install Debian package (.deb) system-wide:"
echo "   sudo dpkg -i $DIST_DIR/featherview_1.0.0_all.deb"
echo "=================================================="
