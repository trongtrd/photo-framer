"""H — Minimal Mat: fixed canvas ratio or a thin border, plain or blurred mat, black keyline."""
from __future__ import annotations

from fractions import Fraction
from typing import NamedTuple

import math

from PIL import Image, ImageFilter, ImageOps

from ..color import colors_in_profile
from ..components.caption import draw_caption
from ..components.gallery_label import (Label, LABEL_INKS, label_metrics, validate_label,
                                         draw_label as paint_label)
from ..components.keyline import draw_keyline
from ..components.slots import Slot
from ..constants import MAX_OUTPUT_PIXELS
from .base import COMMON, Row, Style

# Canvas ratio (width/height); None follows the photo with a thin even border.
RATIOS = {'4:5': Fraction(4, 5), '1:1': Fraction(1, 1), '3:4': Fraction(3, 4),
          '9:16': Fraction(9, 16), '16:9': Fraction(16, 9), 'original': None}
# Menu row 1 keeps its frozen meaning; other fixed ratios exist only as --ratio.
ROW_RATIOS = {1: '4:5', 2: '1:1', 3: 'original'}
# Minimum margin on the binding side, as a fraction of canvas width.
# 16:9 mirrors 9:16's 5% of the short edge: 5% of height = 2.8125% of width.
MARGINS = {'4:5': .036, '1:1': .024, '3:4': .040, '9:16': .050, '16:9': .028125}
THIN_MARGIN = .015  # 'original': uniform border, fraction of the photo's short edge.
BACKGROUNDS = {1: (255, 255, 255), 2: (235, 229, 229), 3: (250, 248, 243)}
KEYLINES = {1: .0055, 2: 0, 3: .011}
KEYLINE_COLOR = (10, 10, 10)
SHARE_SIZES = {'4:5': (1080, 1350), '1:1': (1080, 1080), '3:4': (1080, 1440),
               '9:16': (1080, 1920), '16:9': (1920, 1080)}
RATIO_NOTES = {'4:5': 'fixed 4:5 canvas', '1:1': 'fixed 1:1 canvas', '3:4': 'fixed 3:4 canvas',
               '9:16': 'fixed 9:16 canvas', '16:9': 'fixed 16:9 canvas',
               'original': "thin even border following the photo's ratio"}
# The shared output cap is checked before a full-sized canvas is allocated.

BACKGROUND_MODES = ('blur',)
BLUR_TONES = {'dark': ('multiply', .88), 'neutral': None, 'light': ('lighten', .12)}
DEFAULT_BLUR_TONE = 'dark'
BLUR_WORK_EDGE = 384     # Blur runs on a copy whose longer edge is at most this.
BLUR_RADIUS = .04        # Gaussian radius as a fraction of the working copy's short edge.


class Layout(NamedTuple):
    size: tuple
    pos: tuple
    keyline: int
    label: Label | None = None


def ratio_name(settings):
    return settings.ratio or ROW_RATIOS[settings.choices[0]]


def minimal_mat_geometry(photo_size, ratio, keyline_choice, label_height=0):
    """Style H layout: (canvas size, photo position, keyline width).

    ratio is a RATIOS key. Fixed ratios fit the full-resolution photo plus
    keyline (and the gallery label below it, if any) inside an exact canvas
    with a minimum margin, centered both ways as one block, so a label moves
    the photo up; the photo is never scaled or cropped. 'original' adds a thin
    even border.
    """
    w, h = photo_size
    s = min(w, h)
    keyline = max(1, round(s*KEYLINES[keyline_choice])) if KEYLINES[keyline_choice] else 0
    box_w, box_h = w+2*keyline, h+2*keyline+label_height
    fraction_ratio = RATIOS[ratio]
    if fraction_ratio is None:
        margin = max(4, round(s*THIN_MARGIN))
        size = (box_w+2*margin, box_h+2*margin)
    else:
        fraction = MARGINS[ratio]
        width = max(box_w/(1-2*fraction), box_h/(1/float(fraction_ratio)-2*fraction))
        # Width is a multiple of the ratio numerator so the canvas ratio is exact.
        unit = fraction_ratio.numerator
        width = -(-int(width+.999999)//unit)*unit
        size = (width, width*fraction_ratio.denominator//unit)
    pos = ((size[0]-box_w)//2+keyline, (size[1]-box_h)//2+keyline)
    return size, pos, keyline


def validate(settings):
    if settings.ratio is not None and settings.ratio not in RATIOS:
        raise ValueError('--ratio must be one of ' + ', '.join(RATIOS) + '.')
    if settings.background is not None and settings.background not in BACKGROUND_MODES:
        raise ValueError('--background must be blur.')
    validate_label(settings)
    if settings.blur_tone is not None:
        if settings.background != 'blur':
            raise ValueError('--blur-tone requires --background blur.')
        if settings.blur_tone not in BLUR_TONES:
            raise ValueError('--blur-tone must be dark, neutral or light.')


def layout(photo_size, settings):
    label = label_metrics(photo_size, settings)
    size, pos, keyline = minimal_mat_geometry(photo_size, ratio_name(settings), settings.choices[2],
                                              label.height if label else 0)
    return Layout(size, pos, keyline, label)


def text_limits(plan, photo_size, ratio):
    """Horizontal room for label text: the canvas inside its minimum margins."""
    width = plan.size[0]
    if RATIOS[ratio] is None:
        inset = plan.pos[0]-plan.keyline
    else:
        inset = math.ceil(width*MARGINS[ratio])
    return inset, width-inset


def draw_label(canvas, plan, photo_size, settings, profile, slot):
    """Centered title (and subtitle) in the band reserved below the photo."""
    w, h = photo_size
    top = plan.pos[1]+h+plan.keyline
    left, right = text_limits(plan, photo_size, ratio_name(settings))
    paint_label(canvas, plan.label, settings, profile, slot, top=top, left=left, right=right,
                center=plan.pos[0]+w//2)


def blurred_background(photo, size, tone):
    """The photo scaled to cover the canvas, blurred small and scaled back up.

    Uses the source RGB values, so no color conversion is needed; the intact
    photo is pasted over it afterwards.
    """
    scale = min(1, BLUR_WORK_EDGE / max(size))
    work = (max(1, round(size[0]*scale)), max(1, round(size[1]*scale)))
    small = ImageOps.fit(photo, work, Image.Resampling.BOX)
    small = small.filter(ImageFilter.GaussianBlur(max(1, min(work)*BLUR_RADIUS)))
    adjustment = BLUR_TONES[tone]
    if adjustment:
        kind, amount = adjustment
        if kind == 'multiply':
            small = small.point(lambda value: round(value*amount))
        else:
            small = small.point(lambda value: round(value+(255-value)*amount))
    return small.resize(size, Image.Resampling.BICUBIC)


def paint(photo, plan, settings, ctx):
    w, h = photo.size
    background, keyline_color = colors_in_profile(
        (BACKGROUNDS[settings.choices[1]], KEYLINE_COLOR), ctx.profile)
    if settings.background == 'blur':
        canvas = blurred_background(photo, plan.size, settings.blur_tone or DEFAULT_BLUR_TONE)
    else:
        canvas = Image.new('RGB', plan.size, background)
    pos, keyline = plan.pos, plan.keyline
    draw_keyline(canvas, pos, photo.size, keyline, keyline_color)
    canvas.paste(photo, pos)
    below = pos[1]+h+keyline
    left, right = text_limits(plan, photo.size, ratio_name(settings))
    slot = Slot((left, below, right, plan.size[1]), align=(pos[0], pos[0]+w))
    if settings.caption:
        slot.claim(draw_caption(canvas, settings.caption, settings.font_path, min(w, h), pos,
                                photo.size, plan.size[1]-below, below=below), 'Caption', check=False)
    if plan.label:
        draw_label(canvas, plan, photo.size, settings, ctx.profile, slot)
    return canvas, pos


def share_size(settings):
    return SHARE_SIZES.get(ratio_name(settings))


def notes(settings, *, share, **context):
    ratio = ratio_name(settings)
    exact = share_size(settings) if share else None
    text = ('Minimal Mat: ' + RATIO_NOTES[ratio]
            + '; full-resolution photo centered, never scaled or cropped.'
            + (f' Share copy is exactly {exact[0]}x{exact[1]}.' if exact else ''))
    result = [text]
    if settings.title is not None:
        result.append('Gallery label: ' + ('title and subtitle' if settings.subtitle is not None
                                            else 'title') + ' as supplied, centered below the photo; '
                      + ('the canvas grows to make room.' if RATIOS[ratio] is None
                         else 'the photo sits higher to make room.'))
    if settings.background == 'blur':
        result.append(f'Blurred background ({settings.blur_tone or DEFAULT_BLUR_TONE} tone) made from '
                      'the photo itself, outside the photo only; the mat color choice is not used.')
    return result


STYLE = Style(
    code='H', name=('Minimal Mat', 'Minimal Mat / Khung tối giản'),
    readme_title='H · Minimal Mat / Khung tối giản',
    look=('Fixed 4:5, 1:1, 3:4, 9:16 or 16:9 canvas for any photo, or a thin border; '
          'black keyline; plain or blurred background',
          'Khung cố định 4:5, 1:1, 3:4, 9:16 hoặc 16:9 cho mọi ảnh, hoặc viền mỏng; '
          'viền đen; nền trơn hoặc nền mờ từ ảnh'),
    preview_label='H / Minimal Mat 4:5', default='1-1-1',
    rows=(Row(('Canvas ratio', 'Tỷ lệ khung'), (('4:5 portrait', '4:5 dọc'), ('1:1 square', '1:1 vuông'),
                                                ('Follow photo, thin border',
                                                 'Theo ảnh gốc, viền mỏng'))),
          Row(('Mat', 'Nền'), (('White', 'Trắng'), ('Warm light gray', 'Xám ấm nhạt'),
                               ('Ivory', 'Trắng ngà'))),
          Row(('Black keyline', 'Viền đen sát ảnh (keyline)'), (('Thin', 'Mảnh'), ('None', 'Không có'),
                                                                ('Thick', 'Dày')))),
    choices_hint='ratio-background-keyline',
    # No --signature: a corner mark beside the centered label looks unbalanced (owner decision).
    accepts=COMMON | {'ratio', 'background', 'blur_tone', 'title', 'subtitle'},
    layout=layout, paint=paint, validate=validate, share_size=share_size, notes=notes,
    max_output_pixels=MAX_OUTPUT_PIXELS)
