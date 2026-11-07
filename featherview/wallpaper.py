"""Desktop wallpaper setter supporting modern Linux desktop environments."""

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote


def set_desktop_wallpaper(image_path: str) -> tuple[bool, str]:
    """Sets the given image as the desktop wallpaper.

    Returns:
        (success: bool, message: str)
    """
    path = os.path.abspath(image_path)
    if not os.path.exists(path):
        return False, f"File not found: {path}"

    file_uri = Path(path).as_uri()
    desktop = (os.environ.get("XDG_CURRENT_DESKTOP") or "").lower()
    session = (os.environ.get("DESKTOP_SESSION") or "").lower()

    # 1. Cinnamon Desktop
    if "cinnamon" in desktop or "cinnamon" in session:
        try:
            subprocess.run(
                ["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", file_uri],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["gsettings", "set", "org.cinnamon.desktop.background", "picture-options", "zoom"],
                check=False,
                capture_output=True,
            )
            return True, "Wallpaper updated (Cinnamon)"
        except Exception as e:
            return False, f"Failed setting Cinnamon wallpaper: {e}"

    # 2. GNOME Desktop
    if "gnome" in desktop or "ubuntu" in desktop:
        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", file_uri],
                check=True,
                capture_output=True,
            )
            # Also set dark mode background in GNOME 42+
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", file_uri],
                check=False,
                capture_output=True,
            )
            return True, "Wallpaper updated (GNOME)"
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
            return True, "Wallpaper updated (MATE)"
        except Exception as e:
            return False, f"Failed setting MATE wallpaper: {e}"

    # 4. XFCE Desktop
    if "xfce" in desktop:
        if shutil.which("xfconf-query"):
            try:
                # Query all backdrop image properties and set them
                out = subprocess.run(
                    ["xfconf-query", "-c", "xfce4-desktop", "-l"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                updated = False
                for prop in out.stdout.splitlines():
                    if "last-image" in prop or "image-path" in prop:
                        subprocess.run(
                            ["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", path],
                            check=False,
                        )
                        updated = True
                if updated:
                    return True, "Wallpaper updated (XFCE)"
            except Exception as e:
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
        try:
            subprocess.run(["feh", "--bg-fill", path], check=True, capture_output=True)
            return True, "Wallpaper updated (via feh)"
        except Exception:
            pass

    if shutil.which("nitrogen"):
        try:
            subprocess.run(["nitrogen", "--set-zoom-fill", path], check=True, capture_output=True)
            return True, "Wallpaper updated (via nitrogen)"
        except Exception:
            pass

    # Fallback to gsettings cinnamon or gnome if binary exists
    if shutil.which("gsettings"):
        for schema in ["org.cinnamon.desktop.background", "org.gnome.desktop.background"]:
            try:
                subprocess.run(
                    ["gsettings", "set", schema, "picture-uri", file_uri],
                    check=True,
                    capture_output=True,
                )
                return True, f"Wallpaper updated (via {schema})"
            except Exception:
                continue

    return False, "Could not determine desktop environment or wallpaper setter tool."
