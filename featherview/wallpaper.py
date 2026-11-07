"""Desktop wallpaper setter supporting modern Linux desktop environments."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def set_desktop_wallpaper(
    image_path: str,
    style: str = "zoom",
    bg_color: str = "#000000"
) -> tuple[bool, str]:
    """Sets the given image as the desktop wallpaper.

    Args:
        image_path: Absolute or relative path to the image file.
        style: Display style ('zoom', 'scaled', 'centered', 'spanned').
        bg_color: Background border color in hex format (e.g. '#000000').

    Returns:
        (success: bool, message: str)
    """
    path = os.path.abspath(image_path)
    if not os.path.exists(path):
        return False, f"File not found: {path}"

    file_uri = Path(path).as_uri()
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP") or "").lower()
    session = (os.environ.get("DESKTOP_SESSION") or "").lower()

    # Normalize style
    valid_styles = {"zoom", "scaled", "centered", "spanned"}
    if style not in valid_styles:
        style = "zoom"

    # 1. Cinnamon Desktop
    if "cinnamon" in desktop or "cinnamon" in session:
        try:
            subprocess.run(
                ["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", file_uri],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.cinnamon.desktop.background", "picture-options", style],
                check=False,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.cinnamon.desktop.background", "primary-color", bg_color],
                check=False,
                capture_output=True,
            )
            return True, f"Wallpaper updated (Cinnamon, style: {style})"
        except Exception as e:
            return False, f"Failed setting Cinnamon wallpaper: {e}"

    # 2. GNOME Desktop / Ubuntu
    if "gnome" in desktop or "ubuntu" in desktop:
        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", file_uri],
                check=True,
                capture_output=True,
            )
            # GNOME 42+ dark mode wallpaper
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", file_uri],
                check=False,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-options", style],
                check=False,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "primary-color", bg_color],
                check=False,
                capture_output=True,
            )
            return True, f"Wallpaper updated (GNOME, style: {style})"
        except Exception as e:
            return False, f"Failed setting GNOME wallpaper: {e}"

    # 3. MATE Desktop
    if "mate" in desktop:
        try:
            subprocess.run(
                ["gsettings", "set", "org.mate.background", "picture-filename", path],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.mate.background", "picture-options", style],
                check=False,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.mate.background", "primary-color", bg_color],
                check=False,
                capture_output=True,
            )
            return True, f"Wallpaper updated (MATE, style: {style})"
        except Exception as e:
            return False, f"Failed setting MATE wallpaper: {e}"

    # 4. XFCE Desktop
    if "xfce" in desktop:
        if shutil.which("xfconf-query"):
            try:
                out = subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-l"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                updated = False
                style_code = {"centered": "1", "tiled": "2", "scaled": "3", "zoom": "4", "spanned": "5"}.get(style, "4")
                for prop in out.stdout.splitlines():
                    if "last-image" in prop or "image-path" in prop:
                        subprocess.run(
                            ["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", path],
                            check=False,
                        )
                        updated = True
                    if "image-style" in prop:
                        subprocess.run(
                            ["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", style_code],
                            check=False,
                        )
                if updated:
                    return True, f"Wallpaper updated (XFCE, style: {style})"
            except Exception:
                pass

    # 5. KDE Plasma
    if "kde" in desktop or "plasma" in desktop:
        kde_script = f"""
        var allDesktops = desktops();
        for (var i = 0; i < allDesktops.length; i++) {{
            var d = allDesktops[i];
            d.wallpaperPlugin = "org.kde.image";
            d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
            d.writeConfig("Image", "{file_uri}");
        }}
        """
        try:
            subprocess.run(
                [
                    "qdbus",
                    "org.kde.plasmashell",
                    "/PlasmaShell",
                    "org.kde.PlasmaShell.evaluateScript",
                    kde_script,
                ],
                check=True,
                capture_output=True,
            )
            return True, "Wallpaper updated (KDE Plasma)"
        except Exception:
            pass

    # 6. Generic tools (feh, nitrogen, swaybg)
    if shutil.which("feh"):
        feh_flag = "--bg-fill" if style == "zoom" else ("--bg-max" if style == "scaled" else "--bg-center")
        try:
            subprocess.run(["feh", feh_flag, path], check=True, capture_output=True)
            return True, f"Wallpaper updated (via feh {feh_flag})"
        except Exception:
            pass

    if shutil.which("nitrogen"):
        nitro_flag = "--set-zoom-fill" if style == "zoom" else ("--set-scaled" if style == "scaled" else "--set-centered")
        try:
            subprocess.run(["nitrogen", nitro_flag, path], check=True, capture_output=True)
            return True, f"Wallpaper updated (via nitrogen {nitro_flag})"
        except Exception:
            pass

    # Fallback to gsettings cinnamon or gnome if schema exists
    if shutil.which("gsettings"):
        for schema in ["org.cinnamon.desktop.background", "org.gnome.desktop.background"]:
            try:
                subprocess.run(
                    ["gsettings", "set", schema, "picture-uri", file_uri],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["gsettings", "set", schema, "picture-options", style],
                    check=False,
                    capture_output=True,
                )
                return True, f"Wallpaper updated (via {schema})"
            except Exception:
                continue

    return False, "Could not determine desktop environment or wallpaper setter tool."


def get_current_desktop_wallpaper() -> Optional[str]:
    """Returns the path to the currently active desktop wallpaper if detectable."""
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP") or "").lower()
    session = (os.environ.get("DESKTOP_SESSION") or "").lower()

    schema = None
    if "cinnamon" in desktop or "cinnamon" in session:
        schema = "org.cinnamon.desktop.background"
    elif "gnome" in desktop or "ubuntu" in desktop:
        schema = "org.gnome.desktop.background"

    if schema and shutil.which("gsettings"):
        try:
            out = subprocess.run(
                ["gsettings", "get", schema, "picture-uri"],
                capture_output=True,
                text=True,
                check=True,
            )
            uri = out.stdout.strip().strip("'\"")
            if uri.startswith("file://"):
                return uri[7:]
            return uri
        except Exception:
            pass
    return None
