"""Reduced comparison sheet of every style on the first photo."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .color import color_echo_colors, convert_profile
from .constants import SRGB
from .registry import STYLES
from .renderer import render
from .settings import Settings


def preview_styles(right_text=None, left_text=None):
    """F may preview without wording; final F always needs two explicit fields."""
    if left_text is not None and right_text is None:
        raise ValueError('Supply both --left-text and --right-text for the Film Edge preview; '
                         'use an empty string for a blank corner.')
    include_d = right_text is not None and (left_text is None or bool(right_text.strip()))
    return ''.join(code for code in STYLES if code != 'D' or include_d)


def _preview_settings(code, right_text, left_text, specs):
    if code == 'C':
        return Settings('C', **specs)
    if code == 'D':
        return Settings('D', right_text=right_text, **specs)
    if code == 'F':
        # Blank corners until both fields are supplied; not a final blank choice.
        return Settings('F', left_text=left_text if left_text is not None else '',
                        right_text=right_text if left_text is not None else '')
    return Settings(code)


def preview(photo, profile, meta=None, right_text=None, frame_color=None, left_text=None,
            specs=None):
    """specs: user-supplied capture details (Settings fields) applied to C and D."""
    # Convert only the small preview to sRGB; final RGB PNG retains source pixels/profile.
    # Resolve E once from the original prepared photo, so its preview matches the final.
    styles = preview_styles(right_text, left_text)
    echo_colors = color_echo_colors(photo, profile, frame_color=frame_color)
    photo = photo.copy()
    photo.thumbnail((1100, 1100), Image.Resampling.LANCZOS)
    photo = convert_profile(photo, profile, SRGB)
    results, labels = [], []
    for code in styles:
        context = {'meta': meta} if STYLES[code].uses_metadata else {}
        if code == 'E':
            context = {'echo_colors': echo_colors}
        results.append(render(photo, _preview_settings(code, right_text, left_text, specs or {}), **context)[0])
        label = STYLES[code].preview_label
        if code == 'F' and left_text is None:
            label += ' (text after choosing)'
        labels.append(label)
    for image in results:
        image.thumbnail((760, 980), Image.Resampling.LANCZOS)
    height = max(i.height for i in results)+90
    columns = 2 if len(results) == 4 else 3
    rows = (len(results)+columns-1)//columns
    board = Image.new('RGB', (columns*800, rows*height), (238, 238, 238))
    d = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=24)
    for i, (label, image) in enumerate(zip(labels, results)):
        left, top = (i % columns)*800, (i // columns)*height
        d.text((left+20, top+18), label, font=font, fill=(30, 30, 30))
        board.paste(image, (left+(800-image.width)//2, top+65+(height-75-image.height)//2))
    return board
