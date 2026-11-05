"""F — Film Edge: dark border, side sprockets and two verbatim corner texts."""
from __future__ import annotations

from typing import NamedTuple

from PIL import Image

from ..color import colors_in_profile
from ..components.film import draw_film_border, film_font_px
from ..text import is_single_line
from .base import Row, Style

SIDES = {1: .055, 2: .075, 3: .10}
BACKGROUNDS = {1: (24, 24, 23), 2: (8, 8, 8), 3: (39, 32, 28)}
INK = (245, 239, 221)


class Layout(NamedTuple):
    size: tuple
    side: int
    top: int


def layout(photo_size, choices):
    w, h = photo_size
    s = min(w, h)
    side = max(12, round(s*SIDES[choices[0]]))
    top = max(8, round(s*.04))
    bottom = max(44, round(s*.09), 3*film_font_px(s))
    return Layout((w+2*side, h+top+bottom), side, top)


def validate(settings):
    if settings.left_text is None or settings.right_text is None:
        raise ValueError('Style F requires --left-text and --right-text; '
                         'use an empty string for an intentionally blank corner.')
    for value in (settings.left_text, settings.right_text):
        if not is_single_line(value):
            raise ValueError('Use single-line Film Edge corner texts up to 200 characters each.')
    if settings.caption is not None:
        raise ValueError('For style F, use --left-text and --right-text instead of --caption.')


def paint(photo, plan, settings, ctx):
    _, two, three = settings.choices
    background, ink = colors_in_profile((BACKGROUNDS[two], INK), ctx.profile)
    canvas = Image.new('RGB', plan.size, background)
    draw_film_border(canvas, plan.side, plan.top, photo.size, three, settings.left_text,
                     settings.right_text, settings.font_path, ink)
    pos = (plan.side, plan.top)
    canvas.paste(photo, pos)
    return canvas, pos


def notes(settings, **context):
    return ['Film Edge: two user-supplied corner fields; explicit empty '
            'fields stay blank. No film brand, frame number or metadata inferred.']


STYLE = Style(
    code='F', name=('Film Edge', 'Film Edge / Viền phim'),
    readme_title='F · Film Edge / Viền phim',
    look=('Side sprockets + two custom text fields', 'Lỗ phim hai bên + hai cụm chữ riêng'),
    preview_label='F / Film Edge', default='2-1-1',
    rows=(Row(('Border width', 'Độ rộng viền'), (('Narrow', 'Hẹp'), ('Medium', 'Vừa'), ('Wide', 'Rộng'))),
          Row(('Border background', 'Nền viền'), (('Charcoal', 'Than'), ('Black', 'Đen'),
                                                  ('Dark brown', 'Nâu đậm'))),
          Row(('Side sprockets', 'Lỗ phim hai bên'), (('Standard', 'Tiêu chuẩn'), ('Sparse', 'Thưa'),
                                                      ('Dense', 'Dày')))),
    choices_hint='border-background-sprocket-spacing',
    # F replaces --caption with its two corner fields; validate() rejects it.
    accepts=frozenset({'font_path', 'left_text', 'right_text'}),
    requires=frozenset({'left_text', 'right_text'}),
    layout=layout, paint=paint, validate=validate, notes=notes)
