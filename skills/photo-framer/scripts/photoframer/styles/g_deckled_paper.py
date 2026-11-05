"""G — Deckled Paper: textured cotton paper with torn outer edges and a soft shadow."""
from __future__ import annotations

from typing import NamedTuple

from PIL import Image

from ..color import colors_in_profile
from ..components.caption import CAPTION_INK, draw_caption
from ..components.paper import deckle_amplitude, draw_deckled_paper
from .base import COMMON, Row, Style

MARGINS = {1: .055, 2: .085, 3: .12}
PAPERS = {1: (250, 248, 242), 2: (253, 253, 251), 3: (246, 239, 220)}
BACKGROUND = (224, 223, 218)


class Layout(NamedTuple):
    size: tuple
    margin: int
    pad: int


def layout(photo_size, settings):
    choices = settings.choices
    w, h = photo_size
    s = min(w, h)
    margin = max(12, round(s*MARGINS[choices[0]]))
    pad = max(10, round(s*.025))
    return Layout((w+2*(margin+pad), h+2*(margin+pad)), margin, pad)


def paint(photo, plan, settings, ctx):
    _, two, three = settings.choices
    s = min(photo.size)
    background, caption_ink = colors_in_profile((BACKGROUND, CAPTION_INK), ctx.profile)
    canvas = Image.new('RGB', plan.size, background)
    draw_deckled_paper(canvas, photo.size, plan.margin, plan.pad, PAPERS[two], three, ctx.profile)
    pos = (plan.pad+plan.margin, plan.pad+plan.margin)
    canvas.paste(photo, pos)
    if settings.caption:
        # Keep clear of the torn edge, which reaches 2x amplitude inward.
        space = max(0, plan.margin-2*deckle_amplitude(s, three)-4)
        draw_caption(canvas, settings.caption, settings.font_path, s, pos, photo.size, space,
                     ink=caption_ink)
    return canvas, pos


def notes(settings, **context):
    return ['Deckled Paper: deterministic cotton-paper texture, torn outer '
            'edges and a soft shadow; the rectangular photo region stays untouched.']


STYLE = Style(
    code='G', name=('Deckled Paper', 'Deckled Paper / Giấy mỹ thuật mép xé'),
    readme_title='G · Deckled Paper / Giấy mép xé',
    look=('Textured warm-white paper with torn edges', 'Giấy trắng ấm, vân nhẹ và mép xé'),
    preview_label='G / Deckled Paper', default='2-1-1',
    rows=(Row(('Paper margin', 'Khoảng giấy quanh ảnh'), (('Narrow', 'Hẹp'), ('Medium', 'Vừa'),
                                                          ('Wide', 'Rộng'))),
          Row(('Paper tone', 'Màu giấy'), (('Warm white', 'Trắng ấm'), ('Bright white', 'Trắng sáng'),
                                           ('Ivory', 'Ngà'))),
          Row(('Torn edges', 'Mép xé'), (('Subtle', 'Nhẹ'), ('Medium', 'Vừa'), ('Rough', 'Rõ')))),
    choices_hint='margin-paper-deckle', accepts=COMMON,
    layout=layout, paint=paint, notes=notes)
