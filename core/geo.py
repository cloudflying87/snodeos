"""GPS extraction from EXIF metadata in uploaded images.

EXIF stores GPS coordinates as a 3-tuple (degrees, minutes, seconds), each
as a Pillow IFDRational. The N/S/E/W reference comes from a separate tag.
"""
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def _to_degrees(value):
    """Convert a Pillow EXIF GPS tuple ((d,n), (m,n), (s,n)) → float degrees."""
    try:
        d, m, s = value
        return float(d) + float(m) / 60 + float(s) / 3600
    except Exception:
        return None


def extract_gps(image_file):
    """Return (lat, lng) tuple from an image file, or (None, None) if absent.

    Accepts a file-like (UploadedFile, path str, etc.) — anything PIL.open
    accepts. Rewinds file-likes after read so subsequent saves still work.
    """
    rewind = hasattr(image_file, 'seek')
    try:
        if rewind:
            image_file.seek(0)
        with Image.open(image_file) as img:
            exif = img._getexif() or {}
    except Exception as exc:
        logger.debug('No EXIF readable on image: %s', exc)
        return (None, None)
    finally:
        if rewind:
            try:
                image_file.seek(0)
            except Exception:
                pass

    # EXIF tag 34853 = GPSInfo
    gps = exif.get(34853)
    if not gps:
        return (None, None)

    # Inside GPSInfo: 1=GPSLatitudeRef, 2=GPSLatitude, 3=GPSLongitudeRef, 4=GPSLongitude
    lat = _to_degrees(gps.get(2)) if gps.get(2) else None
    lng = _to_degrees(gps.get(4)) if gps.get(4) else None
    if lat is None or lng is None:
        return (None, None)

    if gps.get(1) == 'S':
        lat = -lat
    if gps.get(3) == 'W':
        lng = -lng

    return (round(lat, 6), round(lng, 6))


def create_image_with_gps(Model, image_file, **kwargs):
    """Create an *Image model row, extracting GPS coords from EXIF if present.

    Use this in place of `Model.objects.create(image=img, ...)` for any
    image attached to an Announcement / TrailCondition / TrailWorkLog.
    """
    lat, lng = extract_gps(image_file)
    return Model.objects.create(image=image_file, lat=lat, lng=lng, **kwargs)
