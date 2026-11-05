"""A — Floating photo: soft two-layer shadow on a light background."""
from __future__ import annotations

from typing import NamedTuple

from PIL import Image

from ..components.caption import draw_caption
from ..components.shadow import shadow
from .base import COMMON, Row, Style

MARGINS = {1: .10, 2: .165, 3: .23}
STRENGTHS = {1: .60, 2: 1., 3: 1.40}
BACKGROUNDS = {1: '#ffffff', 2: '#faf8f3', 3: '#f2f2f2'}


class Layout(NamedTuple):
    size: tuple
    margin: int


def layout(photo_size, choices):
    w, h = photo_size
    margin = max(4, round(min(w, h) * MARGINS[choices[0]]))
    return Layout((w+2*margin, h+2*margin), margin)


def paint(photo, plan, settings, ctx):
    _, two, three = settings.choices
    w, h = photo.size
    s = min(w, h)
    margin = plan.margin
    canvas = Image.new('RGB', plan.size, BACKGROUNDS[three])
    box = (margin, margin, margin+w, margin+h)
    strength = STRENGTHS[two]
    shadow(canvas, box, s*.018, (-s*.014, s*.014), round(85*strength))
    shadow(canvas, box, s*.006, (-s*.006, s*.006), round(41*strength))
    pos = (margin, margin)
    canvas.paste(photo, pos)
    if settings.caption:
        draw_caption(canvas, settings.caption, settings.font_path, s, pos, photo.size, margin)
    return canvas, pos


STYLE = Style(
    code='A', name=('Floating photo', 'Ảnh nổi'),
    readme_title='A · Floating / Ảnh nổi',
    look=('Soft shadow on a light background', 'Bóng mềm trên nền sáng'),
    preview_label='A / Floating photo', default='2-2-1',
    rows=(Row(('Margin', 'Khoảng trắng'), (('Narrow', 'Hẹp'), ('Medium', 'Vừa'), ('Wide', 'Rộng'))),
          Row(('Shadow', 'Bóng đổ'), (('Light', 'Nhẹ'), ('Soft medium', 'Mềm vừa'), ('Strong', 'Rõ'))),
          Row(('Background', 'Nền'), (('White', 'Trắng'), ('Ivory', 'Trắng ngà'),
                                       ('Light gray', 'Xám rất nhạt')))),
    choices_hint='margin-shadow-background', accepts=COMMON,
    layout=layout, paint=paint)
