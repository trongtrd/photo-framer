"""Capture metadata (EXIF first, then XMP, user values on top), display names,
brand mapping, and the EXIF block copied into outputs."""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
import json
import re

from PIL import Image

from .constants import SKILL_DIR

CAMERAS_FILE = SKILL_DIR / 'assets' / 'cameras.json'
# Settings field -> capture metadata key, in display order.
USER_SPEC_FIELDS = (('camera', 'model'), ('lens', 'lens'), ('iso', 'iso'),
                    ('aperture', 'fnumber'), ('shutter', 'exposure'), ('focal', 'focal'))
USER_SPEC_FLAGS = {'camera': '--camera', 'lens': '--lens', 'iso': '--iso',
                   'aperture': '--aperture', 'shutter': '--shutter', 'focal': '--focal'}
# EXIF tags that are pointers to sub-IFDs; values are offsets, never copied.
EXIF_POINTERS = (0x8769, 0x8825, 0xA005)
EXIF_DROPPED = {0x927C,   # MakerNote: undocumented vendor data, often large.
                700,      # XMLPacket: XMP, including edit history.
                0x8773}   # InterColorProfile: the ICC profile is written separately.

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

    Returns (metadata dict, {key: 'EXIF' or 'XMP'}). Never raises: a file the
    renderer would reject is reported by load_photo instead.
    """
    meta, origins = {}, {}
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
                origins[key] = origin
        for key, exif_value, xmp_keys in (
                ('iso', _scalar(sub.get(34855)), ('ISOSpeedRatings',)),
                ('fnumber', sub.get(33437), ('FNumber',)),
                ('exposure', sub.get(33434), ('ExposureTime',)),
                ('focal', sub.get(37386), ('FocalLength',))):
            value, origin = resolve(exif_value, *xmp_keys)
            number = _fraction(_scalar(value)) if value is not None else None
            if number:
                meta[key] = number
                origins[key] = origin
    except Exception:
        return {}, {}
    return meta, origins


def apply_user_specs(meta, origins, settings):
    """Overlay user-supplied capture details; they win over EXIF/XMP field by field.

    The camera text is shown verbatim (no display-name lookup). Brand marks keep
    following the file's own Make/Model, never the user's camera wording.
    """
    meta, origins = dict(meta), dict(origins)
    for field, key in USER_SPEC_FIELDS:
        value = getattr(settings, field, None)
        if value is not None:
            meta[key] = value
            origins[key] = 'user'
    if origins.get('model') == 'user':
        meta['model_verbatim'] = True
    return meta, origins


def display_model(name):
    """Space glued 'Mark' generations in EXIF model names; display-only.

    Cameras write compact names like 'E-M10MarkIV'; the English word 'Mark'
    is unambiguous, so only it gets spacing. Compact names without it
    ('DC-S1RM2', 'E-M1X') stay verbatim, matching reference spec cards.
    """
    if not name:
        return name
    return MARK_SPACING.sub(' Mark ', name)


@lru_cache(maxsize=1)
def _camera_names():
    with open(CAMERAS_FILE, encoding='utf-8') as stream:
        return json.load(stream)['brands']


def camera_display_name(meta, with_brand):
    """Marketing name for a known EXIF model, e.g. 'ILCE-7C' -> 'Sony α7C' / 'α7C'.

    with_brand=False is for layouts that already show the brand mark. Returns
    None for models not listed in assets/cameras.json; names are never guessed.
    """
    slug, model = brand_slug(meta), meta.get('model')
    entry = (_camera_names().get(slug) or {}).get(model) if slug and model else None
    if not entry:
        return None
    return entry['name'] if with_brand else entry['short']


def gear_name(meta, with_brand=True, raw_model=False):
    """Camera text for the gear line: user wording, display name, or the EXIF model."""
    model = meta.get('model') or meta.get('make')
    if not model or meta.get('model_verbatim'):
        return model
    named = None if raw_model or not meta.get('model') else camera_display_name(meta, with_brand)
    if named:
        return named
    shown = display_model(model)
    return shown if with_brand or raw_model else without_brand_prefix(shown, meta)


def without_brand_prefix(name, meta):
    """'Canon EOS R5' -> 'EOS R5' where the brand mark already names the make.

    Used beside a logo or wordmark (style C) only; the brand word must open
    the name and be followed by more text, so 'SIGMA fp L'-style names lose
    just the duplicate brand and nothing else is rewritten.
    """
    wordmark = brand_wordmark(meta)
    if not wordmark or not name:
        return name
    brand = wordmark.split()[0]
    head, _, rest = name.partition(' ')
    return rest if head.upper() == brand and rest.strip() else name


def format_specs(meta, with_brand=True, raw_model=False):
    """Two style-C caption lines: gear line and exposure line."""
    gear = gear_name(meta, with_brand, raw_model)
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


def read_source_exif(path):
    """The source file's EXIF, or None. Never raises."""
    try:
        with Image.open(path) as source:
            exif = source.getexif()
            return exif if exif else None
    except Exception:
        return None


def _sub_ifd(exif, pointer):
    value = exif.get(pointer)
    if isinstance(value, dict):  # Built in memory rather than read from a file.
        return value
    return exif.get_ifd(pointer) if value is not None else {}


def exif_for_output(exif, size):
    """EXIF bytes for a framed output of `size`, or None when there is nothing to keep.

    Keeps IFD0, the Exif sub-IFD and GPS (including location). Orientation is
    reset to 1 because pixels are already rotated; pixel dimensions follow the
    output. The embedded thumbnail (IFD1), maker notes, XMP packets and the
    interoperability pointer are dropped. A fresh block is built so Pillow
    rewrites every offset. Raises on malformed source EXIF.
    """
    if not exif:
        return None
    out = Image.Exif()
    for tag, value in exif.items():
        if tag not in EXIF_POINTERS and tag not in EXIF_DROPPED:
            out[tag] = value
    if 274 in out:
        out[274] = 1
    for tag, value in ((256, size[0]), (257, size[1])):
        if tag in out:
            out[tag] = value
    for pointer in (0x8769, 0x8825):
        ifd = {tag: value for tag, value in _sub_ifd(exif, pointer).items()
               if tag not in EXIF_POINTERS and tag not in EXIF_DROPPED}
        if pointer == 0x8769:
            for tag, value in ((0xA002, size[0]), (0xA003, size[1])):
                if tag in ifd:
                    ifd[tag] = value
        if ifd:
            out[pointer] = ifd  # A dict value is written as a sub-IFD.
    return out.tobytes() if len(out) else None
