"""D — Custom spec card: C's layout with the user's exact text instead of the logo."""
from __future__ import annotations

from ..text import is_single_line
from .base import COMMON, Row, Style
from .c_spec_card import BACKGROUND_ROW, MARGIN_ROW, layout, paint, spec_notes


def validate(settings):
    text = settings.right_text
    if text is None or not text.strip():
        raise ValueError('Style D requires --right-text with your exact text.')
    if not is_single_line(text):
        raise ValueError('Use a single-line --right-text up to 200 characters.')


def notes(settings, **context):
    return spec_notes(settings, **context, missing='left spec area left without text')


STYLE = Style(
    code='D', name=('Custom spec card', 'Thẻ thông số có chữ riêng'),
    readme_title='D · Custom spec card / Thẻ có chữ riêng',
    look=('Camera details + your text at bottom right',
          'Thông số chụp + chữ của bạn bên phải'),
    preview_label='D / Custom text', default='2-1-1',
    rows=(MARGIN_ROW, BACKGROUND_ROW,
          Row(('Left-side details', 'Thông tin bên trái'),
              (('Camera + lens + exposure', 'Máy + ống kính + thông số'),
               ('Camera + lens only', 'Chỉ máy + ống kính'),
               ('No details', 'Không thông tin')))),
    choices_hint='margin-background-left-specs', accepts=COMMON | {'right_text'},
    layout=layout, paint=paint, validate=validate, uses_metadata=True, notes=notes)
