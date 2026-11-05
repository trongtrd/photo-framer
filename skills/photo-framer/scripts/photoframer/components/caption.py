"""Optional single-line --caption, right-aligned in the margin below the photo."""
from __future__ import annotations

from PIL import ImageDraw

from ..text import SECONDARY_INK, specs_fonts

CAPTION_INK = SECONDARY_INK  # Same gray as the exposure line and H's subtitle.


def draw_caption(canvas, caption, font_path, short, photo_pos, photo_size, space,
                 ink=CAPTION_INK, below=None):
    """space: free height under the photo; below: y where that space starts.

    Returns the caption's ink box so later overlays can avoid it.
    """
    w, h = photo_size
    # Bundled Inter Regular, the spec cards' face, unless --font is supplied.
    font, _, _ = specs_fonts(max(9, round(short*.018)), font_path)
    d = ImageDraw.Draw(canvas)
    bounds = d.textbbox((0, 0), caption, font=font)
    tw, th = bounds[2]-bounds[0], bounds[3]-bounds[1]
    if tw > w or th > space*.65:
        raise ValueError('Caption does not fit; shorten it or choose a wider border.')
    left = photo_pos[0]+w-tw-bounds[0]
    below = photo_pos[1]+h if below is None else below
    top = below+(space-th)//2-bounds[1]
    d.text((left, top), caption, font=font, fill=ink)
    return (left+bounds[0], top+bounds[1], left+bounds[2], top+bounds[3])
