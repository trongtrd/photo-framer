"""Gallery labels in the spec cards' Inter faces and shared ink colors."""
from __future__ import annotations

from typing import NamedTuple

from PIL import ImageDraw, ImageStat

from ..color import colors_in_profile
from ..text import PRIMARY_INK, SECONDARY_INK, is_single_line, title_fonts

TITLE_SIZE = .05
SUBTITLE_SIZE = .026
LABEL_GAP = .05
LINE_SPACING = .35
LABEL_INKS = {'dark': (PRIMARY_INK, SECONDARY_INK), 'light': ((246, 244, 238), (214, 212, 206))}


class Label(NamedTuple):
    height: int
    gap: int
    spacing: int
    title_px: int
    subtitle_px: int


def validate_label(settings):
    for value, flag in ((settings.title, '--title'), (settings.subtitle, '--subtitle')):
        if value is not None and (not value.strip() or not is_single_line(value)):
            raise ValueError(f'Use a single-line {flag} up to 200 characters.')
    if settings.subtitle is not None and settings.title is None:
        raise ValueError('--subtitle requires --title.')
    if settings.title is not None:
        if settings.caption:
            raise ValueError('Use either the gallery label (--title/--subtitle) or --caption, not both.')
        if settings.signature is not None:
            raise ValueError('Use either the centered gallery label or --signature, not both.')


def label_metrics(photo_size, settings):
    if settings.title is None:
        return None
    s = min(photo_size)
    title_px, subtitle_px = max(12, round(s*TITLE_SIZE)), max(9, round(s*SUBTITLE_SIZE))
    title_font, subtitle_font = title_fonts(title_px, subtitle_px, settings.font_path)
    gap, spacing = round(s*LABEL_GAP), round(title_px*LINE_SPACING)
    height = gap + sum(title_font.getmetrics())
    if settings.subtitle is not None:
        height += spacing + sum(subtitle_font.getmetrics())
    return Label(height, gap, spacing, title_px, subtitle_px)


def lower_margin(photo_size, original, label, clearance=0):
    """Grow only the lower margin; keep the photo's position and size unchanged."""
    if label is None:
        return original
    return max(original, label.height + max(4, round(min(photo_size)*LABEL_GAP)) + clearance)


def draw_label(canvas, label, settings, profile, slot, *, top, left, right, center,
               check_claims=False):
    title_font, subtitle_font = title_fonts(label.title_px, label.subtitle_px, settings.font_path)
    band = canvas.crop((left, top, right, top+label.height)).convert('L')
    tone = 'light' if ImageStat.Stat(band).mean[0] < 128 else 'dark'
    title_ink, subtitle_ink = colors_in_profile(LABEL_INKS[tone], profile)
    draw = ImageDraw.Draw(canvas)
    lines = [(settings.title, title_font, title_ink, top+label.gap, '--title')]
    if settings.subtitle is not None:
        lines.append((settings.subtitle, subtitle_font, subtitle_ink,
                      top+label.gap+sum(title_font.getmetrics())+label.spacing, '--subtitle'))
    boxes = []
    for text, font, ink, y, flag in lines:
        box = draw.textbbox((center, y), text, font=font, anchor='ma')
        if box[0] < left or box[2] > right:
            raise ValueError(f'{flag} is too wide for the canvas; shorten it.')
        boxes.append((text, font, ink, y, box))
    for text, font, ink, y, box in boxes:
        draw.text((center, y), text, font=font, fill=ink, anchor='ma')
        slot.claim(box, 'Gallery label', check=check_claims)


def draw_margin_label(canvas, plan, photo_size, settings, profile, slot, pos):
    if plan.label is None:
        return
    w, h = photo_size
    draw_label(canvas, plan.label, settings, profile, slot, top=pos[1]+h,
               left=pos[0], right=pos[0]+w, center=pos[0]+w//2, check_claims=True)


def label_notes(settings, **context):
    if settings.title is None:
        return []
    return ['Gallery label: ' + ('title and subtitle' if settings.subtitle is not None else 'title')
            + ' as supplied, centered below the photo; the lower margin grows as needed.']
