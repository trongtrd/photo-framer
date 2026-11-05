"""Film Edge (style F): rounded sprockets beside the photo, two texts below it."""
from __future__ import annotations

from PIL import ImageDraw

from .. import text

SPROCKET_PITCHES = {1: .07, 2: .10, 3: .05}


def film_font_px(short):
    return max(9, round(short*.018))


def draw_film_border(canvas, side, top, photo_size, spacing, left_text, right_text,
                     font_path, ink):
    """Sprockets stay beside the photo; two verbatim texts sit in the lower band."""
    width, height = photo_size
    short = min(photo_size)
    hole_width = min(max(5, round(short*.018)), side-4)
    hole_height = min(height, max(6, round(short*.026)))
    pitch = max(hole_height+4, round(short*SPROCKET_PITCHES[spacing]))
    count = max(1, (height-hole_height)//pitch+1)
    start = top+(height-((count-1)*pitch+hole_height))//2
    draw = ImageDraw.Draw(canvas)
    for index in range(count):
        y = start+index*pitch
        for x in ((side-hole_width)//2, side+width+(side-hole_width)//2):
            draw.rounded_rectangle((x, y, x+hole_width-1, y+hole_height-1),
                                   radius=max(1, round(hole_width*.2)), fill=ink)

    font_px = film_font_px(short)
    _, font, stroke = text.specs_fonts(font_px, font_path)
    entries = []
    for value, alignment in ((left_text, 'left'), (right_text, 'right')):
        if value.strip():
            bounds = draw.textbbox((0, 0), value, font=font, stroke_width=stroke)
            entries.append((value, alignment, bounds))
    if not entries:
        return
    gap = 2*font_px if len(entries) == 2 else 0
    if sum(bounds[2]-bounds[0] for _, _, bounds in entries)+gap > width:
        raise ValueError('Film Edge corner texts do not fit together; '
                         'shorten --left-text or --right-text.')
    band_top = top+height
    band_height = canvas.height-band_top
    min_top = min(bounds[1] for _, _, bounds in entries)
    max_bottom = max(bounds[3] for _, _, bounds in entries)
    text_height = max_bottom-min_top
    if text_height > band_height-4:
        raise ValueError('Film Edge text is too tall for the lower band.')
    y = band_top+(band_height-text_height)//2-min_top
    for value, alignment, bounds in entries:
        x = side-bounds[0] if alignment == 'left' else side+width-bounds[2]
        draw.text((x, y), value, font=font, fill=ink, stroke_width=stroke)
