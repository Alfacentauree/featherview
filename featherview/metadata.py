"""File and EXIF metadata extractor for FeatherView."""

import math
import os
import time
from typing import Any, Dict, Optional

try:
    from PIL import ExifTags, Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def format_bytes(size: int) -> str:
    """Formats raw byte count into human-readable string (KB, MB, GB)."""
    if size < 1024:
        return f"{size} B"
    for unit in ["KB", "MB", "GB", "TB"]:
        size /= 1024.0
        if size < 1024:
            return f"{size:.2f} {unit}"
    return f"{size:.2f} PB"


def _format_exposure(val: Any) -> str:
    """Formats exposure time as e.g. '1/250 s' or '0.5 s'."""
    try:
        val = float(val)
        if val <= 0:
            return "0 s"
        if val < 1.0:
            denom = round(1.0 / val)
            return f"1/{denom} s"
        return f"{val:.1f} s"
    except Exception:
        return str(val)


def _format_fnumber(val: Any) -> str:
    try:
        return f"f/{float(val):.1f}"
    except Exception:
        return str(val)


def _format_focal_length(val: Any) -> str:
    try:
        return f"{float(val):.1f} mm"
    except Exception:
        return str(val)


def get_image_metadata(path: str, width: Optional[int] = None, height: Optional[int] = None) -> Dict[str, Any]:
    """Extracts file information, dimension details, and EXIF tags from an image file."""
    meta: Dict[str, Any] = {
        "file": {},
        "image": {},
        "exif": {},
    }

    if not os.path.isfile(path):
        return meta

    # 1. File attributes
    stat = os.stat(path)
    meta["file"]["name"] = os.path.basename(path)
    meta["file"]["path"] = os.path.abspath(path)
    meta["file"]["size_bytes"] = stat.st_size
    meta["file"]["size_human"] = format_bytes(stat.st_size)
    meta["file"]["modified"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    meta["file"]["extension"] = ext.upper() if ext else "UNKNOWN"

    img_w, img_h = width, height
    color_mode = "Unknown"

    # 2. Extract image info & EXIF via Pillow if available
    if PIL_AVAILABLE:
        try:
            with Image.open(path) as img:
                if img_w is None or img_h is None:
                    img_w, img_h = img.size
                color_mode = img.mode
                meta["image"]["format"] = img.format or ext.upper()

                raw_exif = img.getexif()
                if raw_exif:
                    # Tag mapping
                    tag_map = {ExifTags.TAGS.get(k, str(k)): v for k, v in raw_exif.items()}

                    # Check Exif sub-IFD (0x8769) for camera settings
                    try:
                        exif_sub = raw_exif.get_ifd(0x8769)
                        if exif_sub:
                            for k, v in exif_sub.items():
                                tag_name = ExifTags.TAGS.get(k, str(k))
                                tag_map[tag_name] = v
                    except Exception:
                        pass

                    # Extract common EXIF keys cleanly
                    if "Make" in tag_map:
                        meta["exif"]["Camera Make"] = str(tag_map["Make"]).strip()
                    if "Model" in tag_map:
                        meta["exif"]["Camera Model"] = str(tag_map["Model"]).strip()
                    if "LensModel" in tag_map:
                        meta["exif"]["Lens Model"] = str(tag_map["LensModel"]).strip()
                    if "DateTimeOriginal" in tag_map:
                        meta["exif"]["Date Taken"] = str(tag_map["DateTimeOriginal"])
                    elif "DateTime" in tag_map:
                        meta["exif"]["Date Taken"] = str(tag_map["DateTime"])

                    if "ExposureTime" in tag_map:
                        meta["exif"]["Exposure Time"] = _format_exposure(tag_map["ExposureTime"])
                    if "FNumber" in tag_map:
                        meta["exif"]["Aperture"] = _format_fnumber(tag_map["FNumber"])
                    if "ISOSpeedRatings" in tag_map:
                        meta["exif"]["ISO"] = str(tag_map["ISOSpeedRatings"])
                    elif "PhotographicSensitivity" in tag_map:
                        meta["exif"]["ISO"] = str(tag_map["PhotographicSensitivity"])
                    if "FocalLength" in tag_map:
                        meta["exif"]["Focal Length"] = _format_focal_length(tag_map["FocalLength"])
                    if "Software" in tag_map:
                        meta["exif"]["Software"] = str(tag_map["Software"]).strip()
                    if "Artist" in tag_map or "Copyright" in tag_map:
                        meta["exif"]["Author/Copyright"] = str(tag_map.get("Artist") or tag_map.get("Copyright")).strip()
        except Exception:
            pass

    # 3. Compute image dimensions and aspect ratio
    if img_w and img_h:
        meta["image"]["width"] = img_w
        meta["image"]["height"] = img_h
        meta["image"]["dimensions"] = f"{img_w} × {img_h} px"
        mp = (img_w * img_h) / 1_000_000.0
        meta["image"]["megapixels"] = f"{mp:.2f} MP"
        meta["image"]["color_mode"] = color_mode

        # Aspect ratio reduction
        gcd = math.gcd(img_w, img_h)
        rw, rh = img_w // gcd, img_h // gcd
        if rw < 50 and rh < 50:
            meta["image"]["aspect_ratio"] = f"{rw}:{rh}"
        else:
            meta["image"]["aspect_ratio"] = f"{img_w / img_h:.2f}:1"

    return meta
