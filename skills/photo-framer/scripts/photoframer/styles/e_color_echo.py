"""E — Color Echo: flat border in one color picked from each photo, optional inner edge."""
from __future__ import annotations

from typing import NamedTuple

from PIL import Image

from ..color import color_echo_colors, colors_in_profile, hex_color
from ..components.caption import draw_caption
from ..components.keyline import draw_keyline
from ..components.signature import draw_signature
from ..components.slots import Slot
from ..settings import SIGNATURE_OPTIONS
from .base import COMMON, Row, Style

MARGINS = {1: .045, 2: .08, 3: .12}


class Layout(NamedTuple):
    size: tuple
    margin: int
    inset: int


def inset_width(short, choice):
    return {1: max(1, round(short*.004)), 2: 0, 3: max(2, round(short*.008))}[choice]


def layout(photo_size, settings):
    choices = settings.choices
    w, h = photo_size
    s = min(w, h)
    margin = max(6, round(s*MARGINS[choices[0]]))
    inset = inset_width(s, choices[2])
    padding = margin + inset
    return Layout((w+2*padding, h+2*padding), margin, inset)


def resolve_colors(photo, profile, settings):
    """sRGB (base, inset) for one photo; computed before render for the JSON notes."""
    return color_echo_colors(photo, profile, settings.choices[1], settings.frame_color)


def paint(photo, plan, settings, ctx):
    colors = ctx.echo_colors if ctx.echo_colors is not None else resolve_colors(
        photo, ctx.profile, settings)
    base_color, inset_color = colors_in_profile(colors, ctx.profile)
    canvas = Image.new('RGB', plan.size, base_color)
    padding = plan.margin + plan.inset
    pos = (padding, padding)
    draw_keyline(canvas, pos, photo.size, plan.inset, inset_color)
    canvas.paste(photo, pos)
    w, h = photo.size
    # The colored border below the photo and its inner edge.
    slot = Slot((pos[0], pos[1]+h+plan.inset, pos[0]+w, plan.size[1]))
    if settings.caption:
        slot.claim(draw_caption(canvas, settings.caption, settings.font_path, min(photo.size), pos,
                                photo.size, plan.margin, ink=inset_color), 'Caption', check=False)
    draw_signature(canvas, slot, settings, ctx.profile)
    return canvas, pos


def notes(settings, *, share, origins, echo_colors):
    color = hex_color(echo_colors[0])
    if settings.frame_color is not None:
        return [f'Color Echo: fixed sRGB frame color {color}; automatic analysis skipped.']
    return [f'Color Echo: automatic sRGB frame color {color}, selected locally from '
            'an edge-weighted sample no larger than 96x96; neutral fallback if needed.']


STYLE = Style(
    code='E', name=('Color Echo', 'Color Echo / Viền đồng sắc'),
    readme_title='E · Color Echo / Viền đồng sắc',
    look=('A border color drawn from each photo', 'Màu viền được chọn từ từng ảnh'),
    preview_label='E / Color Echo', default='2-1-1',
    rows=(Row(('Border width', 'Độ rộng viền'), (('Narrow', 'Hẹp'), ('Medium', 'Vừa'), ('Wide', 'Rộng'))),
          Row(('Auto color tone', 'Sắc độ màu tự chọn'), (('Muted', 'Dịu'), ('Natural', 'Tự nhiên'),
                                                           ('Light', 'Sáng'))),
          Row(('Inner edge', 'Đường viền trong'), (('Thin', 'Mảnh'), ('None', 'Không có'),
                                                   ('Medium', 'Vừa')))),
    choices_hint='margin-auto-tone-inset', accepts=COMMON | SIGNATURE_OPTIONS | {'frame_color'},
    layout=layout, paint=paint, notes=notes)
