"""--signature: a transparent PNG (signature or logo) placed in a slot below the photo."""
from __future__ import annotations

import io as _io
from pathlib import Path

from PIL import Image, ImageCms

from ..color import convert_profile
from ..constants import SRGB

MAX_SIGNATURE_EDGE = 4096
POSITIONS = ('bottom-right', 'bottom-center', 'bottom-left')
DEFAULT_POSITION = 'bottom-right'
DEFAULT_WIDTH = .15        # fraction of canvas width
DEFAULT_OPACITY = 1.0
WIDTH_RANGE = (.02, .5)
OPACITY_RANGE = (.05, 1.0)


def load_signature(path):
    """RGBA in sRGB. PNG only, so transparency is explicit; never upscaled beyond use."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f'--signature file not found: {path.name}')
    with Image.open(path) as source:
        if source.format != 'PNG':
            raise ValueError('Use a PNG file for --signature (transparency is kept).')
        if getattr(source, 'n_frames', 1) != 1:
            raise ValueError('Animated PNGs are not supported for --signature.')
        if max(source.size) > MAX_SIGNATURE_EDGE:
            raise ValueError(f'--signature is larger than {MAX_SIGNATURE_EDGE} px; use a smaller PNG.')
        source.load()
        profile = source.info.get('icc_profile')
        image = source.convert('RGBA')
    if profile:
        ImageCms.ImageCmsProfile(_io.BytesIO(profile))  # Reject broken profiles.
        rgb = convert_profile(image.convert('RGB'), profile, SRGB)
        rgb.putalpha(image.getchannel('A'))
        image = rgb
    return image


def draw_signature(canvas, slot, settings, profile, band=None):
    """band: optional (y0, y1) row to center on, e.g. H's gallery label."""
    if not settings.signature:
        return None
    mark = load_signature(settings.signature)
    width = max(1, round(canvas.width*(settings.signature_width or DEFAULT_WIDTH)))
    height = max(1, round(mark.height*width/mark.width))
    clearance = max(2, round(slot.height*.12))
    if height > slot.height-2*clearance or width > slot.box[2]-slot.box[0]:
        raise ValueError('Signature does not fit below the photo; use a smaller '
                         '--signature-width or a wider margin.')
    # Premultiplied resampling keeps transparent edges free of dark fringes.
    mark = mark.convert('RGBa').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA')
    opacity = settings.signature_opacity if settings.signature_opacity is not None else DEFAULT_OPACITY
    alpha = mark.getchannel('A')
    if opacity < 1:
        alpha = alpha.point(lambda value: round(value*opacity))
    rgb = convert_profile(mark.convert('RGB'), SRGB, profile) if profile else mark.convert('RGB')
    left, right = slot.align
    position = settings.signature_position or DEFAULT_POSITION
    x = {'bottom-left': left, 'bottom-right': right-width,
         'bottom-center': (left+right-width)//2}[position]
    if band:
        y = max(slot.box[1]+clearance, min(slot.box[3]-clearance-height,
                                            (band[0]+band[1]-height)//2))
    else:
        y = slot.box[1]+(slot.height-height)//2
    slot.claim((x, y, x+width, y+height), 'Signature')
    canvas.paste(rgb, (x, y), alpha)
    return x, y, x+width, y+height
