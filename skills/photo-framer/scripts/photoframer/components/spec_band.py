"""Caption band of the spec cards: capture details left, brand mark or user text right."""
from __future__ import annotations

from PIL import Image, ImageDraw

from .. import text
from ..constants import LOGO_DIR
from ..metadata import brand_slug, brand_wordmark, format_specs

GEAR_INK = (30, 30, 30)
EXPOSURE_INK = (115, 115, 115)
WORDMARK_INK = (40, 40, 40)


def load_logo(slug):
    path = LOGO_DIR / f'{slug}.png'
    if not path.is_file():
        return None
    with Image.open(path) as logo:
        return logo.convert('RGBA')


def draw_spec_band(canvas, side, band, mode, caption, font_path, font_px, meta,
                   right_text=None):
    """Auto specs on the left; C has a brand mark, D has exact user text."""
    band_top = canvas.height - band
    photo_right = canvas.width - side
    regular_font, emphasis_font, stroke = text.specs_fonts(font_px, font_path)
    d = ImageDraw.Draw(canvas)
    slug = brand_slug(meta) if right_text is None else None
    logo = load_logo(slug) if slug else None
    mark_width = 0
    wordmark = None
    mark_font = None
    if right_text is not None:
        right_bounds = d.textbbox((0, 0), right_text, font=emphasis_font,
                                  stroke_width=stroke)
        mark_width = right_bounds[2] - right_bounds[0]
        if mark_width > canvas.width - 2*side or right_bounds[3] - right_bounds[1] > band - 4:
            raise ValueError('Custom text does not fit; shorten --right-text.')
    elif logo is not None:
        logo_h = min(round(font_px*2.8), round(band*.66))
        scale = logo_h / logo.height
        logo_w = round(logo.width * scale)
        max_w = max(24, round((canvas.width - 2*side) * .34))
        if logo_w > max_w:
            logo_w = max_w
            logo_h = max(1, round(logo.height * (max_w / logo.width)))
        logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        mark_width = logo_w
    elif mode != 3 or caption:
        wordmark = brand_wordmark(meta)
        if wordmark:
            mark_font, mark_stroke = text.wordmark_font(font_px, font_path)
            mark_width = round(d.textlength(wordmark, font=mark_font))
    if caption:
        lines = [(caption, True)]
    elif mode == 3:
        lines = []
    else:
        line1, line2 = format_specs(meta or {})
        lines = [(line, True) for line in ((line1,) if line1 else ())]
        if mode == 1 and line2:
            lines.append((line2, False))
    separation = max(round(side*.6), 2*font_px) if right_text is not None else round(side*.6)
    limit = canvas.width - 2*side - (mark_width + separation if mark_width else 0)
    kept = []
    for line, emphasis in lines:
        font = emphasis_font if emphasis else regular_font
        if right_text is not None:
            bounds = d.textbbox((0, 0), line, font=font,
                                stroke_width=stroke if emphasis else 0)
            if bounds[2] - bounds[0] > limit:
                raise ValueError('Custom text does not fit beside the capture details; '
                                 'shorten --right-text or choose fewer left-side details.')
            kept.append((line, emphasis))
            continue
        while line and d.textlength(line, font=font) > limit and ' | ' in line:
            line = line.rsplit(' | ', 1)[0]
        if line and d.textlength(line, font=font) <= limit:
            kept.append((line, emphasis))
    if kept:
        gap = round(font_px * .55)
        block = len(kept)*font_px + (len(kept)-1)*gap
        y = band_top + max(2, (band - block)//2)
        # Hierarchy like the reference prints: the gear line near-black in the
        # heavier face; the exposure line lighter gray in the regular face.
        for line, emphasis in kept:
            d.text((side, y), line,
                   font=emphasis_font if emphasis else regular_font,
                   fill=GEAR_INK if emphasis else EXPOSURE_INK,
                   stroke_width=stroke if emphasis else 0)
            y += font_px + gap
    if right_text is not None:
        right_height = right_bounds[3] - right_bounds[1]
        d.text((photo_right - right_bounds[2],
                band_top + (band - right_height)//2 - right_bounds[1]),
               right_text, font=emphasis_font, fill=GEAR_INK,
               stroke_width=stroke)
    elif logo is not None:
        canvas.paste(logo, (photo_right - logo_w, band_top + (band - logo_h)//2), logo)
    elif wordmark:
        d.text((photo_right - mark_width,
                band_top + (band - round(font_px*1.6))//2),
               wordmark, font=mark_font, fill=WORDMARK_INK,
               stroke_width=mark_stroke)
