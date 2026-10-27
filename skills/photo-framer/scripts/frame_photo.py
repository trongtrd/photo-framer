#!/usr/bin/env python3
"""Deterministic photo framing. Python 3.10+, Pillow; no network or AI APIs."""
from __future__ import annotations
import argparse
import colorsys
import io
import json
import os
import random
import re
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import tempfile
import warnings

from PIL import Image, ImageChops, ImageCms, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

MAX_INPUT_PIXELS = 30_000_000
MAX_OUTPUT_PIXELS = 60_000_000
Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS
BACKGROUNDS_A = {1: '#ffffff', 2: '#faf8f3', 3: '#f2f2f2'}
BACKGROUNDS_B = {1: '#5a5a5a', 2: '#ffffff', 3: '#faf8f3'}
BACKGROUNDS_C = {1: '#ffffff', 2: '#faf8f3', 3: '#f2f2f2'}
C_MARGINS = {1: .022, 2: .035, 3: .055}
E_MARGINS = {1: .045, 2: .08, 3: .12}
E_NEUTRAL = (232, 228, 220)
F_SIDES = {1: .055, 2: .075, 3: .10}
F_BACKGROUNDS = {1: (24, 24, 23), 2: (8, 8, 8), 3: (39, 32, 28)}
G_MARGINS = {1: .055, 2: .085, 3: .12}
G_PAPERS = {1: (250, 248, 242), 2: (253, 253, 251), 3: (246, 239, 220)}
G_BACKGROUND = (224, 223, 218)
FRAMES = {1: (32, 32, 31), 2: (242, 242, 240), 3: (66, 66, 65)}
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
LOGO_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'logos'
FONTS_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'fonts'
SPECS_FONT_FILES = ('Inter-Regular.ttf', 'Inter-SemiBold.ttf')
# 'E-M10MarkIV' -> 'E-M10 Mark IV'; already-spaced names pass through.
MARK_SPACING = re.compile(r' *Mark *(?=[IVX]+\d*$|\d+$)')
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()

def choices(style, code=None):
    """Style-specific menu; C and D share margin/background/spec choices."""
    if style not in ('A', 'B', 'C', 'D', 'E', 'F', 'G'):
        raise ValueError('Style must be A, B, C, D, E, F or G.')
    code = code or {'A': '2-2-1', 'B': '1-2-1', 'C': '2-1-1',
                    'D': '2-1-1', 'E': '2-1-1', 'F': '2-1-1', 'G': '2-1-1'}[style]
    parts = code.split('-')
    if len(parts) != 3 or any(x not in ('1', '2', '3') for x in parts):
        raise ValueError('Choices must be three numbers from 1 to 3, e.g. 2-2-1.')
    return tuple(map(int, parts))

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
             if word.upper() not in ('CORPORATION', 'CORP.', 'CORP', 'INC.', 'INC',
                                     'LTD.', 'LTD', 'LIMITED', 'CO.', 'CO', '&')]
    return ' '.join(words).upper() or None

def load_logo(slug):
    path = LOGO_DIR / f'{slug}.png'
    if not path.is_file():
        return None
    with Image.open(path) as logo:
        return logo.convert('RGBA')

def specs_fonts(font_px, font_path=None):
    """Caption-band pair: (regular, emphasis, stroke).

    Bundled Inter gives true Regular + SemiBold faces. A user-supplied --font
    replaces both faces and loses the weight step. Without either, Pillow's
    default face is used and a thin stroke imitates the heavier weight.
    """
    if font_path:
        face = ImageFont.truetype(str(font_path), font_px)
        return face, face, 0
    try:
        regular = ImageFont.truetype(str(FONTS_DIR / SPECS_FONT_FILES[0]), font_px)
        emphasis = ImageFont.truetype(str(FONTS_DIR / SPECS_FONT_FILES[1]), font_px)
        return regular, emphasis, 0
    except OSError:
        face = ImageFont.load_default(size=font_px)
        return face, face, max(1, round(font_px * .028))

def wordmark_font(font_px, font_path=None):
    """Face for the text wordmark fallback, mirroring the emphasis weight."""
    size = round(font_px * 1.6)
    if font_path:
        return ImageFont.truetype(str(font_path), size), 0
    try:
        return ImageFont.truetype(str(FONTS_DIR / SPECS_FONT_FILES[1]), size), 0
    except OSError:
        return ImageFont.load_default(size=size), max(1, round(font_px * .028))

def load_photo(path, crop=None):
    notes = []
    # Pillow decodes some 16-bit PNG color types into 8-bit RGB/RGBA.
    # Inspect the encoded depth before decoding; mode alone cannot detect it.
    with open(path, 'rb') as stream:
        header = stream.read(29)
    if (len(header) >= 29 and header[:8] == b'\x89PNG\r\n\x1a\n'
            and header[8:16] == b'\x00\x00\x00\rIHDR' and header[24] > 8):
        raise ValueError('High-bit-depth images are unsupported; export an 8-bit RGB copy.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as source:
            if source.format not in ('JPEG', 'PNG'):
                raise ValueError('Version 0.2 supports JPEG and PNG only.')
            if getattr(source, 'n_frames', 1) != 1:
                raise ValueError('Animated images are not supported.')
            if source.width * source.height > MAX_INPUT_PIXELS:
                raise ValueError('Input exceeds 30 megapixels; provide a smaller copy.')
            source.load()  # Never accept truncated files.
            profile = source.info.get('icc_profile')
            photo = ImageOps.exif_transpose(source).copy()
    if crop:
        x0, y0, x1, y1 = crop
        if not (0 <= x0 < x1 <= photo.width and 0 <= y0 < y1 <= photo.height):
            raise ValueError('Crop must fit within the oriented image.')
        photo = photo.crop(crop)
        notes.append('Explicit crop applied.')
    if photo.mode.startswith('I') or photo.mode == 'F':
        raise ValueError('High-bit-depth images are unsupported; export an 8-bit RGB copy.')
    # Preserve alpha/tRNS in the source mode before ICC conversion can discard
    # alpha or reinterpret a grayscale transparency key as an RGB key.
    alpha = None
    if photo.mode in ('RGBA', 'LA') or 'transparency' in photo.info:
        alpha = photo.convert('RGBA').getchannel('A')
    if photo.mode == 'LA':
        photo = photo.getchannel('L')
    if profile:
        # Validate profiles; do not silently discard broken color information.
        source_profile = ImageCms.ImageCmsProfile(io.BytesIO(profile))
        if photo.mode not in ('RGB', 'RGBA', 'P'):
            photo = ImageCms.profileToProfile(photo, source_profile,
                        ImageCms.ImageCmsProfile(io.BytesIO(SRGB)), outputMode='RGB')
            profile = SRGB
            notes.append('Converted profiled non-RGB source to sRGB.')
    elif photo.mode == 'CMYK':
        raise ValueError('CMYK JPEG without an ICC profile: export an sRGB copy first.')
    else:
        profile = profile or SRGB
    if alpha is not None:
        rgba = photo.convert('RGBA')
        rgba.putalpha(alpha)
        if alpha.getextrema()[0] < 255:
            # A physical print has an opaque paper backing.
            backing = Image.new('RGBA', photo.size, 'white')
            photo = Image.alpha_composite(backing, rgba).convert('RGB')
            notes.append('Transparency flattened on white paper; output is opaque.')
        else:
            photo = rgba.convert('RGB')
    else:
        photo = photo.convert('RGB')
    return photo, profile, notes

def shadow(canvas, box, blur, offset, opacity):
    mask = Image.new('L', canvas.size)
    x0, y0, x1, y1 = box
    dx, dy = offset
    ImageDraw.Draw(mask).rectangle((x0+dx, y0+dy, x1+dx-1, y1+dy-1), fill=opacity)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste((0, 0, 0), (0, 0), mask)


def color_echo_color(photo, profile=None, tone=1, frame_color=None):
    """One deterministic sRGB color, from <=96x96 samples; no AI or variants."""
    if frame_color is not None:
        try:
            color = ImageColor.getrgb(frame_color)
        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError('Use an opaque RGB --frame-color, e.g. #ad896c or navy.') from error
        if len(color) != 3 or any(channel < 0 or channel > 255 for channel in color):
            raise ValueError('--frame-color must be an opaque RGB color.')
        return color

    scale = min(1, 96 / max(photo.size))
    sample = photo.resize((max(1, round(photo.width*scale)),
                           max(1, round(photo.height*scale))), Image.Resampling.BOX)
    if profile:
        sample = ImageCms.profileToProfile(sample,
                    ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                    ImageCms.ImageCmsProfile(io.BytesIO(SRGB)), outputMode='RGB')
    buckets = {}
    width, height = sample.size
    for y in range(height):
        for x in range(width):
            red, green, blue = sample.getpixel((x, y))
            _, lightness, saturation = colorsys.rgb_to_hls(red/255, green/255, blue/255)
            if saturation < .10 or not .14 <= lightness <= .86:
                continue
            weight = 3 if (x < width*.2 or x >= width*.8 or
                           y < height*.2 or y >= height*.8) else 1
            key = (red//24, green//24, blue//24)
            totals = buckets.setdefault(key, [0, 0, 0, 0])
            totals[0] += weight
            for channel, value in enumerate((red, green, blue), 1):
                totals[channel] += weight*value
    if not buckets:
        return E_NEUTRAL

    candidates = []
    for key, (weight, red, green, blue) in buckets.items():
        rgb = (red/weight/255, green/weight/255, blue/weight/255)
        hue, lightness, saturation = colorsys.rgb_to_hls(*rgb)
        # Midtones count more than dark roof/shadow or bright highlight areas.
        score = weight * max(.1, 1-abs(lightness-.5)/.4) * (.7+.3*min(saturation/.5, 1))
        candidates.append((score, key, hue, lightness, saturation))
    _, _, hue, lightness, saturation = max(candidates)
    if tone == 1:  # Muted default; adjust the border, never the photo.
        lightness = min(.68, max(.36, lightness+.06))
        saturation = min(.48, max(.18, saturation*.7))
    elif tone == 3:
        lightness = .80
        saturation = min(.35, saturation*.5)
    return tuple(round(value*255) for value in colorsys.hls_to_rgb(hue, lightness, saturation))


def color_echo_colors(photo, profile=None, tone=1, frame_color=None):
    """Base and contrasting inset, expressed in sRGB for reusable hex colors."""
    base = color_echo_color(photo, profile, tone, frame_color)
    brightness = sum(value*weight for value, weight in zip(base, (.2126, .7152, .0722)))/255
    inset = (24, 28, 36) if brightness >= .45 else (244, 240, 232)
    return base, inset


def colors_in_profile(colors, profile):
    """Convert only decorative sRGB colors; keep source RGB pixels/profile intact."""
    if not profile:
        return colors
    palette = Image.new('RGB', (len(colors), 1))
    palette.putdata(colors)
    converted = ImageCms.profileToProfile(palette,
                    ImageCms.ImageCmsProfile(io.BytesIO(SRGB)),
                    ImageCms.ImageCmsProfile(io.BytesIO(profile)), outputMode='RGB')
    return tuple(converted.getpixel((index, 0)) for index in range(len(colors)))

def draw_spec_band(canvas, side, band, mode, caption, font_path, font_px, meta,
                   right_text=None):
    """Auto specs on the left; C has a brand mark, D has exact user text."""
    band_top = canvas.height - band
    photo_right = canvas.width - side
    regular_font, emphasis_font, stroke = specs_fonts(font_px, font_path)
    d = ImageDraw.Draw(canvas)
    slug = brand_slug(meta) if right_text is None else None
    logo = load_logo(slug) if slug else None
    mark_width = 0
    wordmark = None
    mark_font = None
    if right_text is not None:
        right_bounds = d.textbbox((0, 0), right_text, font=emphasis_font,
                                  stroke_width=stroke)
        mark_width = right_bounds[2] - right_bounds[0]
        if mark_width > canvas.width - 2*side or right_bounds[3] - right_bounds[1] > band - 4:
            raise ValueError('Custom text does not fit; shorten --right-text.')
    elif logo is not None:
        logo_h = min(round(font_px*2.8), round(band*.66))
        scale = logo_h / logo.height
        logo_w = round(logo.width * scale)
        max_w = max(24, round((canvas.width - 2*side) * .34))
        if logo_w > max_w:
            logo_w = max_w
            logo_h = max(1, round(logo.height * (max_w / logo.width)))
        logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        mark_width = logo_w
    elif mode != 3 or caption:
        wordmark = brand_wordmark(meta)
        if wordmark:
            mark_font, mark_stroke = wordmark_font(font_px, font_path)
            mark_width = round(d.textlength(wordmark, font=mark_font))
    if caption:
        lines = [(caption, True)]
    elif mode == 3:
        lines = []
    else:
        line1, line2 = format_specs(meta or {})
        lines = [(line, True) for line in ((line1,) if line1 else ())]
        if mode == 1 and line2:
            lines.append((line2, False))
    separation = max(round(side*.6), 2*font_px) if right_text is not None else round(side*.6)
    limit = canvas.width - 2*side - (mark_width + separation if mark_width else 0)
    kept = []
    for line, emphasis in lines:
        font = emphasis_font if emphasis else regular_font
        if right_text is not None:
            bounds = d.textbbox((0, 0), line, font=font,
                                stroke_width=stroke if emphasis else 0)
            if bounds[2] - bounds[0] > limit:
                raise ValueError('Custom text does not fit beside the capture details; '
                                 'shorten --right-text or choose fewer left-side details.')
            kept.append((line, emphasis))
            continue
        while line and d.textlength(line, font=font) > limit and ' | ' in line:
            line = line.rsplit(' | ', 1)[0]
        if line and d.textlength(line, font=font) <= limit:
            kept.append((line, emphasis))
    if kept:
        gap = round(font_px * .55)
        block = len(kept)*font_px + (len(kept)-1)*gap
        y = band_top + max(2, (band - block)//2)
        # Hierarchy like the reference prints: the gear line near-black in the
        # heavier face; the exposure line lighter gray in the regular face.
        for line, emphasis in kept:
            d.text((side, y), line,
                   font=emphasis_font if emphasis else regular_font,
                   fill=(30, 30, 30) if emphasis else (115, 115, 115),
                   stroke_width=stroke if emphasis else 0)
            y += font_px + gap
    if right_text is not None:
        right_height = right_bounds[3] - right_bounds[1]
        d.text((photo_right - right_bounds[2],
                band_top + (band - right_height)//2 - right_bounds[1]),
               right_text, font=emphasis_font, fill=(30, 30, 30),
               stroke_width=stroke)
    elif logo is not None:
        canvas.paste(logo, (photo_right - logo_w, band_top + (band - logo_h)//2), logo)
    elif wordmark:
        d.text((photo_right - mark_width,
                band_top + (band - round(font_px*1.6))//2),
               wordmark, font=mark_font, fill=(40, 40, 40),
               stroke_width=mark_stroke)

def _deckle_mask(canvas_size, pad, paper_size, short, roughness):
    """A repeatable irregular outer silhouette; each edge has <=770 points."""
    amplitude = max(2, round(short*{1: .003, 2: .005, 3: .008}[roughness]))
    rng = random.Random(92753)

    def edge(length):
        step = max(2, round(short*.002), (length+767)//768)
        pitch = max(12, round(short*.02), (length+63)//64)
        knots = [rng.uniform(.2*amplitude, 1.8*amplitude)
                 for _ in range(length//pitch+2)]
        clearance = 2*amplitude+1
        positions = list(range(clearance, length-clearance, step))
        positions.append(length-clearance-1)
        points = []
        for position in positions:
            index, fraction = divmod(position, pitch)
            fraction /= pitch
            offset = knots[index]*(1-fraction)+knots[index+1]*fraction
            offset += rng.uniform(-.28*amplitude, .28*amplitude)
            points.append((position, round(min(2*amplitude, max(0, offset)))))
        return points

    width, height = paper_size
    top = [(pad+x, pad+offset) for x, offset in edge(width)]
    right = [(pad+width-1-offset, pad+y) for y, offset in edge(height)]
    bottom = [(pad+x, pad+height-1-offset) for x, offset in reversed(edge(width))]
    left = [(pad+offset, pad+y) for y, offset in reversed(edge(height))]
    mask = Image.new('L', canvas_size)
    ImageDraw.Draw(mask).polygon(top+right+bottom+left, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(.6))


@lru_cache(maxsize=12)
def _paper_texture(paper_color, profile):
    """A small reusable cotton-paper tile; never texture source photo pixels."""
    rng = random.Random(72819)
    tile = Image.new('RGB', (256, 256))
    tile.putdata([tuple(min(255, max(0, channel+noise)) for channel in paper_color)
                  for noise in (rng.randrange(-3, 4) for _ in range(256*256))])
    draw = ImageDraw.Draw(tile)
    for _ in range(450):
        x, y = rng.randrange(256), rng.randrange(256)
        shift = rng.choice((-3, -2, 2, 3))
        color = tuple(min(255, max(0, channel+shift)) for channel in paper_color)
        draw.line((x, y, x+rng.randrange(2, 13), y+rng.randrange(-2, 3)), fill=color)
    if profile:
        tile = ImageCms.profileToProfile(tile,
                    ImageCms.ImageCmsProfile(io.BytesIO(SRGB)),
                    ImageCms.ImageCmsProfile(io.BytesIO(profile)), outputMode='RGB')
    return tile


def draw_deckled_paper(canvas, photo_size, margin, pad, paper_color, roughness, profile):
    width, height = photo_size
    short = min(photo_size)
    paper_size = (width+2*margin, height+2*margin)
    mask = _deckle_mask(canvas.size, pad, paper_size, short, roughness)
    shade = mask.filter(ImageFilter.GaussianBlur(max(1, round(short*.0035))))
    shade = shade.point(lambda value: value*52//255)
    shade = ImageChops.offset(shade, max(1, round(short*.001)), max(1, round(short*.003)))
    canvas.paste((0, 0, 0), (0, 0), shade)
    tile = _paper_texture(paper_color, profile)
    x, y = pad+margin, pad+margin
    x0, y0, x1, y1 = mask.getbbox()
    # Only allocate/texture the four margins, not a second full-resolution photo.
    boxes = ((x0, y0, x1, y), (x0, y+height, x1, y1),
             (x0, y, x, y+height), (x+width, y, x1, y+height))
    for left, top, right, bottom in boxes:
        strip = Image.new('RGB', (right-left, bottom-top))
        for ty in range(-(top % 256), bottom-top, 256):
            for tx in range(-(left % 256), right-left, 256):
                strip.paste(tile, (tx, ty))
        canvas.paste(strip, (left, top), mask.crop((left, top, right, bottom)))


def draw_film_border(canvas, side, top, photo_size, spacing, left_text, right_text,
                     font_path, ink):
    """Sprockets stay beside the photo; two verbatim texts sit in the lower band."""
    width, height = photo_size
    short = min(photo_size)
    hole_width = min(max(5, round(short*.018)), side-4)
    hole_height = min(height, max(6, round(short*.026)))
    pitch = max(hole_height+4, round(short*{1: .07, 2: .10, 3: .05}[spacing]))
    count = max(1, (height-hole_height)//pitch+1)
    start = top+(height-((count-1)*pitch+hole_height))//2
    draw = ImageDraw.Draw(canvas)
    for index in range(count):
        y = start+index*pitch
        for x in ((side-hole_width)//2, side+width+(side-hole_width)//2):
            draw.rounded_rectangle((x, y, x+hole_width-1, y+hole_height-1),
                                   radius=max(1, round(hole_width*.2)), fill=ink)

    font_px = max(9, round(short*.018))
    _, font, stroke = specs_fonts(font_px, font_path)
    entries = []
    for text, alignment in ((left_text, 'left'), (right_text, 'right')):
        if text.strip():
            bounds = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
            entries.append((text, alignment, bounds))
    if not entries:
        return
    gap = 2*font_px if len(entries) == 2 else 0
    if sum(bounds[2]-bounds[0] for _, _, bounds in entries)+gap > width:
        raise ValueError('Film Edge corner texts do not fit together; '
                         'shorten --left-text or --right-text.')
    band_top = top+height
    band_height = canvas.height-band_top
    min_top = min(bounds[1] for _, _, bounds in entries)
    max_bottom = max(bounds[3] for _, _, bounds in entries)
    text_height = max_bottom-min_top
    if text_height > band_height-4:
        raise ValueError('Film Edge text is too tall for the lower band.')
    y = band_top+(band_height-text_height)//2-min_top
    for text, alignment, bounds in entries:
        x = side-bounds[0] if alignment == 'left' else side+width-bounds[2]
        draw.text((x, y), text, font=font, fill=ink, stroke_width=stroke)


def render(photo, style='A', code=None, caption=None, font_path=None, meta=None,
           right_text=None, frame_color=None, profile=None, echo_colors=None,
           left_text=None):
    one, two, three = choices(style, code)
    if left_text is not None and style != 'F':
        raise ValueError('--left-text is supported only with style F (or --preview).')
    if frame_color is not None and style != 'E':
        raise ValueError('--frame-color is supported only with style E (or --preview).')
    if style == 'D':
        if right_text is None or not right_text.strip():
            raise ValueError('Style D requires --right-text with your exact text.')
        if len(right_text) > 200 or any(char in right_text for char in '\r\n\t'):
            raise ValueError('Use a single-line --right-text up to 200 characters.')
    elif style == 'F':
        if left_text is None or right_text is None:
            raise ValueError('Style F requires --left-text and --right-text; '
                             'use an empty string for an intentionally blank corner.')
        for text in (left_text, right_text):
            if len(text) > 200 or any(char in text for char in '\r\n\t'):
                raise ValueError('Use single-line Film Edge corner texts up to 200 characters each.')
        if caption is not None:
            raise ValueError('For style F, use --left-text and --right-text instead of --caption.')
    elif right_text is not None:
        raise ValueError('--right-text is supported only with style D or F (or --preview).')
    w, h = photo.size
    s = min(w, h)
    if s < 16:
        raise ValueError('The shorter image edge must be at least 16 pixels.')
    if caption:
        if not font_path:
            raise ValueError('A Unicode-capable --font file is required for captions.')
        if '\n' in caption or len(caption) > 200:
            raise ValueError('Use a single-line caption up to 200 characters.')
    if style == 'A':
        margin = max(4, round(s * {1: .10, 2: .165, 3: .23}[one]))
        size = (w+2*margin, h+2*margin)
    elif style == 'B':
        mat = max(4, round(s * {1: .10, 2: .16, 3: .23}[two]))
        frame = max(2, round(s*.035))
        wall = max(4, round(s*.18))
        fw, fh = w+2*(mat+frame), h+2*(mat+frame)
        size = (fw+2*wall, fh+2*wall)
    elif style == 'E':
        margin = max(6, round(s*E_MARGINS[one]))
        inset = {1: max(1, round(s*.004)), 2: 0, 3: max(2, round(s*.008))}[three]
        padding = margin + inset
        size = (w+2*padding, h+2*padding)
    elif style == 'F':
        side = max(12, round(s*F_SIDES[one]))
        top = max(8, round(s*.04))
        bottom = max(44, round(s*.09), 3*max(9, round(s*.018)))
        size = (w+2*side, h+top+bottom)
    elif style == 'G':
        margin = max(12, round(s*G_MARGINS[one]))
        pad = max(10, round(s*.025))
        size = (w+2*(margin+pad), h+2*(margin+pad))
    else:
        side = max(6, round(s * C_MARGINS[one]))
        font_px = max(9, round(s*.018))
        band = max(round(s*.12), round(font_px*3.6), 44)
        size = (w+2*side, h+side+band)
    if size[0]*size[1] > MAX_OUTPUT_PIXELS:
        raise ValueError('Framed output exceeds 60 megapixels; provide a smaller copy.')
    caption_ink = (100, 100, 100)
    if style == 'A':
        canvas = Image.new('RGB', size, BACKGROUNDS_A[three])
        box = (margin, margin, margin+w, margin+h)
        strength = {1: .60, 2: 1., 3: 1.40}[two]
        shadow(canvas, box, s*.018, (-s*.014, s*.014), round(85*strength))
        shadow(canvas, box, s*.006, (-s*.006, s*.006), round(41*strength))
        pos = (margin, margin)
        caption_space = margin
    elif style == 'B':
        canvas = Image.new('RGB', size, BACKGROUNDS_B[three])
        box = (wall, wall, wall+fw, wall+fh)
        shadow(canvas, box, s*.032, (0, s*.018), 76)
        shadow(canvas, box, s*.009, (0, s*.007), 48)
        d = ImageDraw.Draw(canvas)
        frame_color = FRAMES[one]
        d.rectangle((wall, wall, wall+fw-1, wall+fh-1), fill=frame_color)
        d.line((wall, wall, wall+fw-1, wall), fill=tuple(min(255,c+10) for c in frame_color))
        ix, iy = wall+frame, wall+frame
        iw, ih = w+2*mat, h+2*mat
        mask = Image.new('L', size, 105)
        ImageDraw.Draw(mask).rectangle((ix, iy, ix+iw-1, iy+ih-1), fill=0)
        mask = mask.filter(ImageFilter.GaussianBlur(s*.011))
        board = Image.new('RGB', (iw, ih), 'white')
        board.paste((0,0,0), (0,0), mask.crop((ix, iy, ix+iw, iy+ih)))
        canvas.paste(board, (ix, iy))
        pos = (ix+mat, iy+mat)
        caption_space = mat
    elif style == 'E':
        colors = echo_colors if echo_colors is not None else color_echo_colors(
            photo, profile, two, frame_color)
        base_color, inset_color = colors_in_profile(colors, profile)
        canvas = Image.new('RGB', size, base_color)
        if inset:
            ImageDraw.Draw(canvas).rectangle(
                (margin, margin, margin+w+2*inset-1, margin+h+2*inset-1), fill=inset_color)
        pos = (padding, padding)
        caption_space = margin
        caption_ink = inset_color
    elif style == 'F':
        background, ink = colors_in_profile((F_BACKGROUNDS[two], (245, 239, 221)), profile)
        canvas = Image.new('RGB', size, background)
        draw_film_border(canvas, side, top, (w, h), three, left_text, right_text,
                         font_path, ink)
        pos = (side, top)
    elif style == 'G':
        background, caption_ink = colors_in_profile((G_BACKGROUND, (100, 100, 100)), profile)
        canvas = Image.new('RGB', size, background)
        draw_deckled_paper(canvas, (w, h), margin, pad, G_PAPERS[two], three, profile)
        pos = (pad+margin, pad+margin)
        amplitude = max(2, round(s*{1: .003, 2: .005, 3: .008}[three]))
        caption_space = max(0, margin-2*amplitude-4)
    else:
        canvas = Image.new('RGB', size, BACKGROUNDS_C[two])
        pos = (side, side)
        canvas.paste(photo, pos)
        draw_spec_band(canvas, side, band, three, caption, font_path, font_px,
                       meta or {}, right_text)
        return canvas, pos
    canvas.paste(photo, pos)
    if caption:
        font = ImageFont.truetype(str(font_path), max(9, round(s*.018)))
        d = ImageDraw.Draw(canvas)
        bounds = d.textbbox((0,0), caption, font=font)
        tw, th = bounds[2]-bounds[0], bounds[3]-bounds[1]
        if tw > w or th > caption_space*.65:
            raise ValueError('Caption does not fit; shorten it or choose a wider border.')
        left = pos[0]+w-tw-bounds[0]
        top = pos[1]+h+(caption_space-th)//2-bounds[1]
        d.text((left, top), caption, font=font, fill=caption_ink)
    return canvas, pos

def save_verified(image, destination, profile, original=None, photo_pos=None):
    """Validate complete encoded file before publishing; never overwrite an existing file."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.framer-', suffix='.tmp', dir=destination.parent)
    try:
        fmt = 'JPEG' if destination.suffix.lower() in ('.jpg', '.jpeg') else 'PNG'
        with os.fdopen(fd, 'wb') as stream:
            image.save(stream, format=fmt, icc_profile=profile,
                       **({'quality': 92, 'subsampling': 0} if fmt == 'JPEG' else {}))
            stream.flush()
            os.fsync(stream.fileno())
        with Image.open(temporary) as check:
            check.verify()
        with Image.open(temporary) as check:
            check.load()
            if check.size != image.size:
                raise ValueError('Output dimensions failed verification.')
            if original is not None and fmt == 'PNG':
                x, y = photo_pos
                region = check.crop((x,y,x+original.width,y+original.height))
                if region.tobytes() != original.tobytes():
                    raise ValueError('Photo pixel preservation failed verification.')
        candidate = destination
        for count in range(10000):
            try:
                os.link(temporary, candidate)  # Atomic, refuses to replace existing paths.
                return candidate.resolve()
            except FileExistsError:
                candidate = destination.with_name(f'{destination.stem}_{count+2}{destination.suffix}')
        raise ValueError('Too many existing output files with the same name.')
    finally:
        Path(temporary).unlink(missing_ok=True)

def preview_styles(right_text=None, left_text=None):
    """F may preview without wording; final F always needs two explicit fields."""
    if left_text is not None and right_text is None:
        raise ValueError('Supply both --left-text and --right-text for the Film Edge preview; '
                         'use an empty string for a blank corner.')
    include_d = right_text is not None and (left_text is None or bool(right_text.strip()))
    return 'ABC' + ('D' if include_d else '') + 'EFG'


def preview(photo, profile, meta=None, right_text=None, frame_color=None,
            left_text=None):
    # Convert only the small preview to sRGB; final RGB PNG retains source pixels/profile.
    # Resolve E once from the original prepared photo, so its preview matches the final.
    styles = preview_styles(right_text, left_text)
    echo_colors = color_echo_colors(photo, profile, frame_color=frame_color)
    photo = photo.copy()
    photo.thumbnail((1100,1100), Image.Resampling.LANCZOS)
    photo = ImageCms.profileToProfile(photo,
                ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.ImageCmsProfile(io.BytesIO(SRGB)), outputMode='RGB')
    results = [render(photo, style, meta=meta)[0] for style in ('A','B','C')]
    if 'D' in styles:
        results.append(render(photo, 'D', meta=meta, right_text=right_text)[0])
    results.append(render(photo, 'E', echo_colors=echo_colors)[0])
    results.append(render(photo, 'F', left_text=left_text if left_text is not None else '',
                          right_text=right_text if left_text is not None else '')[0])
    results.append(render(photo, 'G')[0])
    for image in results:
        image.thumbnail((760,980), Image.Resampling.LANCZOS)
    height = max(i.height for i in results)+90
    columns = 2 if len(results) == 4 else 3
    rows = (len(results)+columns-1)//columns
    board = Image.new('RGB',(columns*800,rows*height),(238,238,238))
    d = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=24)
    labels = ['A / Floating photo','B / Gallery frame','C / Print · spec card']
    if 'D' in styles:
        labels.append('D / Custom text')
    labels.append('E / Color Echo')
    labels.append('F / Film Edge' if left_text is not None else
                  'F / Film Edge (text after choosing)')
    labels.append('G / Deckled Paper')
    for i,(label,image) in enumerate(zip(labels,results)):
        left, top = (i % columns)*800, (i // columns)*height
        d.text((left+20,top+18),label,font=font,fill=(30,30,30))
        board.paste(image,(left+(800-image.width)//2,top+65+(height-75-image.height)//2))
    return board

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path, nargs='+')
    parser.add_argument('--style', choices=['A','B','C','D','E','F','G'], default='A')
    parser.add_argument('--choices', help='A: margin-shadow-background; B: frame-mat-background; C/D: margin-background-left-specs; E: margin-auto-tone-inset; F: border-background-sprocket-spacing; G: margin-paper-deckle')
    parser.add_argument('--preview', action='store_true', help='Preview A/B/C/E/F/G; include D when nonempty --right-text is supplied, first input only')
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--share', action='store_true', help='Also export an sRGB JPEG, max 2048 px')
    parser.add_argument('--crop', type=int, nargs=4, metavar=('LEFT','TOP','RIGHT','BOTTOM'))
    parser.add_argument('--caption')
    parser.add_argument('--left-text', help='Style F: exact lower-left text; empty string means intentionally blank')
    parser.add_argument('--right-text', help='Style D or F: exact lower-right text; F allows an intentionally empty string')
    parser.add_argument('--frame-color', help='Style E: one fixed sRGB hex/name for the entire batch, skips auto analysis')
    parser.add_argument('--font', type=Path)
    args = parser.parse_args(argv)
    choices(args.style, args.choices)
    if args.crop and len(args.inputs) != 1:
        parser.error('--crop accepts exactly one input to avoid unintended batch cropping.')
    results = []
    for path in (args.inputs[:1] if args.preview else args.inputs):
        try:
            meta, sources = ({}, set()) if args.style in ('E', 'F', 'G') and not args.preview else read_capture_metadata(path)
            photo, profile, notes = load_photo(path, args.crop)
            stem = path.stem
            if args.preview:
                image = preview(photo, profile, meta, args.right_text, args.frame_color, args.left_text)
                styles = preview_styles(args.right_text, args.left_text)
                outputs = [save_verified(image,args.out_dir/f'{stem}_{styles}_preview.jpg',SRGB)]
            else:
                echo_colors = (color_echo_colors(photo, profile,
                               choices('E', args.choices)[1], args.frame_color)
                               if args.style == 'E' else None)
                image, pos = render(photo,args.style,args.choices,args.caption,args.font,
                                    meta,args.right_text,args.frame_color,profile,echo_colors,args.left_text)
                outputs = [save_verified(image,args.out_dir/f'{stem}_{args.style}.png',profile,photo,pos)]
                if args.share:
                    image.thumbnail((2048,2048),Image.Resampling.LANCZOS)
                    image = ImageCms.profileToProfile(image,
                                ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                                ImageCms.ImageCmsProfile(io.BytesIO(SRGB)),outputMode='RGB')
                    outputs.append(save_verified(image,args.out_dir/f'{stem}_{args.style}_share.jpg',SRGB))
                if args.style in ('C', 'D') and not args.caption:
                    if sources:
                        notes.append('Spec caption from ' + ' and '.join(sorted(sources)) + ' metadata.')
                    else:
                        notes.append('No capture metadata; left spec area left without text.'
                                     if args.style == 'D' else
                                     'No capture metadata; spec band left without text.')
                if args.style == 'E':
                    color_hex = '#' + ''.join(f'{channel:02x}' for channel in echo_colors[0])
                    notes.append(f'Color Echo: fixed sRGB frame color {color_hex}; automatic analysis skipped.'
                                 if args.frame_color is not None else
                                 f'Color Echo: automatic sRGB frame color {color_hex}, selected locally from '
                                 'an edge-weighted sample no larger than 96x96; neutral fallback if needed.')
                if args.style == 'F':
                    notes.append('Film Edge: two user-supplied corner fields; explicit empty '
                                 'fields stay blank. No film brand, frame number or metadata inferred.')
                if args.style == 'G':
                    notes.append('Deckled Paper: deterministic cotton-paper texture, torn outer '
                                 'edges and a soft shadow; the rectangular photo region stays untouched.')
            if args.preview or args.style in ('C', 'D'):
                model = meta.get('model')
                if model and display_model(model) != model:
                    notes.append(f"Model display formatted: '{model}' -> '{display_model(model)}'.")
                if args.preview or args.style == 'C':
                    slug = brand_slug(meta)
                    if slug and (LOGO_DIR / f'{slug}.png').is_file():
                        notes.append(f'Brand mark: {slug}.')
                    elif brand_wordmark(meta):
                        notes.append('Brand wordmark drawn; no logo file for this brand.')
                if (args.preview and 'D' in styles) or (not args.preview and args.style == 'D'):
                    notes.append('Style D: user text replaces the brand mark; '
                                 'same font, size and weight as the gear line.')
            results.append({'input': str(path), 'status':'ok', 'outputs':list(map(str,outputs)), 'notes':notes})
        except Exception as error:
            results.append({'input':str(path),'status':'error','error':str(error)})
    # ASCII JSON escapes preserve Unicode paths even on legacy Windows stdout.
    print(json.dumps({'results':results},ensure_ascii=True,indent=2))
    return int(any(r['status']=='error' for r in results))

if __name__ == '__main__':
    raise SystemExit(main())
