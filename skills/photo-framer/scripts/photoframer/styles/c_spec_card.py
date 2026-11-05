"""C — Print / spec card: capture details and the camera brand mark below the photo."""
from __future__ import annotations

from typing import NamedTuple

from PIL import Image

from ..components.spec_band import draw_spec_band
from ..metadata import USER_SPEC_FIELDS, USER_SPEC_FLAGS, apply_user_specs
from ..settings import SPEC_OPTIONS
from .base import COMMON, Row, Style

MARGINS = {1: .022, 2: .035, 3: .055}
BACKGROUNDS = {1: '#ffffff', 2: '#faf8f3', 3: '#f2f2f2'}
MARGIN_ROW = Row(('Margin', 'Viền'), (('Narrow', 'Hẹp'), ('Medium', 'Vừa'), ('Wide', 'Rộng')))
BACKGROUND_ROW = Row(('Background', 'Nền'), (('White', 'Trắng'), ('Ivory', 'Trắng ngà'),
                                              ('Light gray', 'Xám rất nhạt')))


class Layout(NamedTuple):
    size: tuple
    side: int
    band: int
    font_px: int


def layout(photo_size, choices):
    """Shared by C and D: even margins and a taller caption band below."""
    w, h = photo_size
    s = min(w, h)
    side = max(6, round(s * MARGINS[choices[0]]))
    font_px = max(9, round(s*.018))
    band = max(round(s*.12), round(font_px*3.6), 44)
    return Layout((w+2*side, h+side+band), side, band, font_px)


def paint(photo, plan, settings, ctx):
    _, two, three = settings.choices
    canvas = Image.new('RGB', plan.size, BACKGROUNDS[two])
    pos = (plan.side, plan.side)
    canvas.paste(photo, pos)
    meta = ctx.meta or {}
    draw_spec_band(canvas, plan.side, plan.band, three, settings.caption, settings.font_path,
                   plan.font_px, meta, settings.right_text,
                   specs=apply_user_specs(meta, {}, settings)[0], raw_model=bool(settings.raw_model))
    return canvas, pos


def spec_notes(settings, *, share, origins, echo_colors, missing='spec band left without text'):
    if settings.caption:
        return []
    _, origins = apply_user_specs({}, origins, settings)
    notes = []
    sources = set(origins.values()) - {'user'}
    if sources:
        notes.append('Spec caption from ' + ' and '.join(sorted(sources)) + ' metadata.')
    supplied = [USER_SPEC_FLAGS[field] for field, key in USER_SPEC_FIELDS
                if origins.get(key) == 'user']
    if supplied:
        notes.append('Capture details supplied by the user: ' + ', '.join(supplied) + '.')
    return notes or [f'No capture metadata; {missing}.']


STYLE = Style(
    code='C', name=('Print / spec card', 'Thẻ thông số'),
    readme_title='C · Spec card / Thẻ thông số',
    look=('Camera details and brand logo', 'Thông số chụp và logo hãng'),
    preview_label='C / Print · spec card', default='2-1-1',
    rows=(MARGIN_ROW, BACKGROUND_ROW,
          Row(('Caption', 'Chữ'), (('Camera + lens + exposure', 'Máy + ống kính + thông số'),
                                   ('Camera + lens only', 'Chỉ máy + ống kính'),
                                   ('No text', 'Không chữ')))),
    choices_hint='margin-background-left-specs', accepts=COMMON | SPEC_OPTIONS,
    layout=layout, paint=paint, uses_metadata=True, notes=spec_notes)
