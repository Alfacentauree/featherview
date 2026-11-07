#!/usr/bin/env bash
set -e

echo "Uninstalling FeatherView..."

rm -f "$HOME/.local/bin/featherview"
rm -f "$HOME/.local/share/applications/featherview.desktop"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/featherview.svg"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

echo "FeatherView has been removed."
