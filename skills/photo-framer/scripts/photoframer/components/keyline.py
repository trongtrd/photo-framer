"""Solid edge of a given width just outside the photo (E inner edge, H keyline)."""
from __future__ import annotations

from PIL import ImageDraw


def draw_keyline(canvas, photo_pos, photo_size, width, color):
    """Fill the photo rectangle grown by width; the photo is pasted over it later."""
    if not width:
        return
    x, y = photo_pos
    w, h = photo_size
    ImageDraw.Draw(canvas).rectangle((x-width, y-width, x+w+width-1, y+h+width-1), fill=color)
