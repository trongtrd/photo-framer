"""Gaussian drop shadow under a rectangle (styles A and B)."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter


def shadow(canvas, box, blur, offset, opacity):
    mask = Image.new('L', canvas.size)
    x0, y0, x1, y1 = box
    dx, dy = offset
    ImageDraw.Draw(mask).rectangle((x0+dx, y0+dy, x1+dx-1, y1+dy-1), fill=opacity)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste((0, 0, 0), (0, 0), mask)
