"""Capture metadata (EXIF first, then XMP), display formatting and brand mapping."""
from __future__ import annotations

from fractions import Fraction
import re

from PIL import Image

# Uppercase substring of Make/Model -> logo slug in assets/logos/.
BRAND_LOGOS = (
    ('OLYMPUS', 'om-system'), ('OM DIGITAL', 'om-system'), ('OM SYSTEM', 'om-system'),
    ('PANASONIC', 'lumix'), ('LUMIX', 'lumix'),
    ('SONY', 'sony'), ('CANON', 'canon'), ('NIKON', 'nikon'),
    ('FUJIFILM', 'fujifilm'), ('FUJI', 'fujifilm'),
    ('LEICA', 'leica'), ('RICOH', 'ricoh'), ('PENTAX', 'ricoh'),
    ('APPLE', 'apple'), ('IPHONE', 'apple'), ('IPAD', 'apple'),
    ('HASSELBLAD', 'hasselblad'), ('SAMSUNG', 'samsung'),
    ('XIAOMI', 'xiaomi'), ('REDMI', 'xiaomi'), ('POCO', 'xiaomi'),
    ('HUAWEI', 'huawei'), ('HONOR', 'huawei'),
    ('KODAK', 'kodak'), ('EASTMAN KODAK', 'kodak'), ('GOPRO', 'gopro'),
)
# 'E-M10MarkIV' -> 'E-M10 Mark IV'; already-spaced names pass through.
MARK_SPACING = re.compile(r' *Mark *(?=[IVX]+\d*$|\d+$)')
COMPANY_SUFFIXES = ('CORPORATION', 'CORP.', 'CORP', 'INC.', 'INC',
                    'LTD.', 'LTD', 'LIMITED', 'CO.', 'CO', '&')


def _xmp_description(xmp):
    try:
        return ((xmp.get('xmpmeta') or {}).get('RDF') or {}).get('Description') or {}
    except AttributeError:
        return {}


def _xmp_value(description, *keys):
    """First scalar value for the given XMP attribute names, unwrapping Seq/Bag lists."""
    for key in keys:
        value = description.get(key)
        if isinstance(value, dict):
            for container in ('Seq', 'Bag', 'Alt'):
                items = value.get(container)
                if isinstance(items, dict):
                    value = items.get('li')
                    break
        if isinstance(value, list):
            value = value[0] if value else None
        if value not in (None, ''):
            return str(value)
    return None


def _fraction(value):
    """Parse EXIF/XMP rationals such as '1/200', IFDRational or plain numbers."""
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(Fraction(str(value).strip()))
        except (ValueError, ZeroDivisionError):
            return None


def _scalar(value):
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _text(value):
    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text.lower() == 'unknown' else text


def read_capture_metadata(path):
    """Merge capture metadata; EXIF wins, XMP (Lightroom exports) fills the gaps.

    Returns (metadata dict, set of source names). Never raises: a file the
    renderer would reject is reported by load_photo instead.
    """
    meta, sources = {}, set()
    try:
        with Image.open(path) as source:
            exif = source.getexif()
            sub = exif.get_ifd(0x8769)
            description = _xmp_description(source.getxmp() or {})
        def resolve(exif_value, *xmp_keys):
            value, origin = exif_value, 'EXIF'
            if value in (None, ''):
                value, origin = _xmp_value(description, *xmp_keys), 'XMP'
            return value, origin
        for key, exif_value, xmp_keys in (
                ('make', exif.get(271), ('Make',)),
                ('model', exif.get(272), ('Model',)),
                ('lens', sub.get(42036), ('LensModel', 'Lens'))):
            value, origin = resolve(exif_value, *xmp_keys)
            value = _text(value)
            if value:
                meta[key] = value
                sources.add(origin)
        for key, exif_value, xmp_keys in (
                ('iso', _scalar(sub.get(34855)), ('ISOSpeedRatings',)),
                ('fnumber', sub.get(33437), ('FNumber',)),
                ('exposure', sub.get(33434), ('ExposureTime',)),
                ('focal', sub.get(37386), ('FocalLength',))):
            value, origin = resolve(exif_value, *xmp_keys)
            number = _fraction(_scalar(value)) if value is not None else None
            if number:
                meta[key] = number
                sources.add(origin)
    except Exception:
        return {}, set()
    return meta, sources


def display_model(name):
    """Space glued 'Mark' generations in EXIF model names; display-only.

    Cameras write compact names like 'E-M10MarkIV'; the English word 'Mark'
    is unambiguous, so only it gets spacing. Compact names without it
    ('DC-S1RM2', 'E-M1X') stay verbatim, matching reference spec cards.
    """
    if not name:
        return name
    return MARK_SPACING.sub(' Mark ', name)


def format_specs(meta):
    """Two style-C caption lines: gear line and exposure line."""
    gear = display_model(meta.get('model') or meta.get('make'))
    line1 = ' | '.join(part for part in (gear, meta.get('lens')) if part) or None
    iso, fnumber, exposure, focal = (meta.get(key)
                                     for key in ('iso', 'fnumber', 'exposure', 'focal'))
    if None not in (iso, fnumber, exposure, focal) and exposure > 0:
        shutter = f'{exposure:g}s' if exposure >= 1 else f'1/{round(1 / exposure)}s'
        line2 = f'ISO {round(iso)}  f/{fnumber:g}  {shutter}  {focal:g}mm'
    else:
        line2 = None
    return line1, line2


def brand_slug(meta):
    haystack = ' '.join(filter(None, (meta.get('make'), meta.get('model')))).upper()
    for needle, slug in BRAND_LOGOS:
        if needle in haystack:
            return slug
    return None


def brand_wordmark(meta):
    make = meta.get('make')
    if not make:
        return None
    words = [word for word in str(make).replace(',', ' ').split()
             if word.upper() not in COMPANY_SUFFIXES]
    return ' '.join(words).upper() or None
