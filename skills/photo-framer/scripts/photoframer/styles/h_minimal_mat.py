"""H — Minimal Mat: fixed 4:5 / 1:1 canvas or a thin border, optional black keyline."""
from __future__ import annotations

from fractions import Fraction
from typing import NamedTuple

from PIL import Image

from ..color import colors_in_profile
from ..components.caption import draw_caption
from ..components.keyline import draw_keyline
from .base import COMMON, Row, Style

# Canvas ratio (width/height) and minimum margin as a fraction of canvas width.
RATIOS = {1: Fraction(4, 5), 2: Fraction(1, 1), 3: None}
MARGINS = {1: .036, 2: .024}
THIN_MARGIN = .015  # Ratio 3: uniform border, fraction of the photo's short edge.
BACKGROUNDS = {1: (255, 255, 255), 2: (235, 229, 229), 3: (250, 248, 243)}
KEYLINES = {1: .0055, 2: 0, 3: .011}
KEYLINE_COLOR = (10, 10, 10)
SHARE_SIZES = {1: (1080, 1350), 2: (1080, 1080)}
RATIO_NOTES = {1: 'fixed 4:5 canvas', 2: 'fixed 1:1 canvas',
               3: "thin even border following the photo's ratio"}


class Layout(NamedTuple):
    size: tuple
    pos: tuple
    keyline: int


def minimal_mat_geometry(photo_size, ratio_choice, keyline_choice):
    """Style H layout: (canvas size, photo position, keyline width).

    Fixed ratios fit the full-resolution photo plus keyline inside an exact
    4:5 or 1:1 canvas with a minimum margin, centered both ways; the photo is
    never scaled or cropped. Ratio 3 follows the photo with a thin even border.
    """
    w, h = photo_size
    s = min(w, h)
    keyline = max(1, round(s*KEYLINES[keyline_choice])) if KEYLINES[keyline_choice] else 0
    box_w, box_h = w+2*keyline, h+2*keyline
    ratio = RATIOS[ratio_choice]
    if ratio is None:
        margin = max(4, round(s*THIN_MARGIN))
        size = (box_w+2*margin, box_h+2*margin)
    else:
        fraction = MARGINS[ratio_choice]
        width = max(box_w/(1-2*fraction), box_h/(1/float(ratio)-2*fraction))
        # Width is a multiple of the ratio numerator so the canvas ratio is exact.
        unit = ratio.numerator
        width = -(-int(width+.999999)//unit)*unit
        size = (width, width*ratio.denominator//unit)
    pos = ((size[0]-box_w)//2+keyline, (size[1]-box_h)//2+keyline)
    return size, pos, keyline


def layout(photo_size, choices):
    return Layout(*minimal_mat_geometry(photo_size, choices[0], choices[2]))


def paint(photo, plan, settings, ctx):
    w, h = photo.size
    background, keyline_color = colors_in_profile(
        (BACKGROUNDS[settings.choices[1]], KEYLINE_COLOR), ctx.profile)
    canvas = Image.new('RGB', plan.size, background)
    pos, keyline = plan.pos, plan.keyline
    draw_keyline(canvas, pos, photo.size, keyline, keyline_color)
    canvas.paste(photo, pos)
    if settings.caption:
        below = pos[1]+h+keyline
        draw_caption(canvas, settings.caption, settings.font_path, min(w, h), pos, photo.size,
                     plan.size[1]-below, below=below)
    return canvas, pos


def share_size(choices):
    return SHARE_SIZES.get(choices[0])


def notes(settings, *, share, **context):
    ratio = settings.choices[0]
    exact = share_size(settings.choices) if share else None
    return ['Minimal Mat: ' + RATIO_NOTES[ratio]
            + '; full-resolution photo centered, never scaled or cropped.'
            + (f' Share copy is exactly {exact[0]}x{exact[1]}.' if exact else '')]


STYLE = Style(
    code='H', name=('Minimal Mat', 'Minimal Mat / Khung tối giản'),
    readme_title='H · Minimal Mat / Khung tối giản',
    look=('Fixed 4:5 or 1:1 canvas for any photo, or a thin border; optional black keyline',
          'Khung cố định 4:5 hoặc 1:1 cho mọi ảnh, hoặc viền mỏng; tùy chọn viền đen'),
    preview_label='H / Minimal Mat 4:5', default='1-1-1',
    rows=(Row(('Canvas ratio', 'Tỷ lệ khung'), (('4:5 portrait', '4:5 dọc'), ('1:1 square', '1:1 vuông'),
                                                ('Follow photo, thin border',
                                                 'Theo ảnh gốc, viền mỏng'))),
          Row(('Mat', 'Nền'), (('White', 'Trắng'), ('Warm light gray', 'Xám ấm nhạt'),
                               ('Ivory', 'Trắng ngà'))),
          Row(('Black keyline', 'Viền đen sát ảnh (keyline)'), (('Thin', 'Mảnh'), ('None', 'Không có'),
                                                                ('Thick', 'Dày')))),
    choices_hint='ratio-background-keyline', accepts=COMMON,
    layout=layout, paint=paint, share_size=share_size, notes=notes)
