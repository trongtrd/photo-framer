"""Deckled cotton paper (style G): torn silhouette, texture tile and contact shadow."""
from __future__ import annotations

from functools import lru_cache
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from ..color import convert_profile
from ..constants import SRGB

DECKLE_AMPLITUDES = {1: .003, 2: .005, 3: .008}


def deckle_amplitude(short, roughness):
    return max(2, round(short*DECKLE_AMPLITUDES[roughness]))


def _deckle_mask(canvas_size, pad, paper_size, short, roughness):
    """A repeatable irregular outer silhouette; each edge has <=770 points."""
    amplitude = deckle_amplitude(short, roughness)
    rng = random.Random(92753)

    def edge(length):
        step = max(2, round(short*.002), (length+767)//768)
        pitch = max(12, round(short*.02), (length+63)//64)
        knots = [rng.uniform(.2*amplitude, 1.8*amplitude)
                 for _ in range(length//pitch+2)]
        clearance = 2*amplitude+1
        positions = list(range(clearance, length-clearance, step))
        positions.append(length-clearance-1)
        points = []
        for position in positions:
            index, fraction = divmod(position, pitch)
            fraction /= pitch
            offset = knots[index]*(1-fraction)+knots[index+1]*fraction
            offset += rng.uniform(-.28*amplitude, .28*amplitude)
            points.append((position, round(min(2*amplitude, max(0, offset)))))
        return points

    width, height = paper_size
    top = [(pad+x, pad+offset) for x, offset in edge(width)]
    right = [(pad+width-1-offset, pad+y) for y, offset in edge(height)]
    bottom = [(pad+x, pad+height-1-offset) for x, offset in reversed(edge(width))]
    left = [(pad+offset, pad+y) for y, offset in reversed(edge(height))]
    mask = Image.new('L', canvas_size)
    ImageDraw.Draw(mask).polygon(top+right+bottom+left, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(.6))


@lru_cache(maxsize=12)
def _paper_texture(paper_color, profile):
    """A small reusable cotton-paper tile; never texture source photo pixels."""
    rng = random.Random(72819)
    tile = Image.new('RGB', (256, 256))
    tile.putdata([tuple(min(255, max(0, channel+noise)) for channel in paper_color)
                  for noise in (rng.randrange(-3, 4) for _ in range(256*256))])
    draw = ImageDraw.Draw(tile)
    for _ in range(450):
        x, y = rng.randrange(256), rng.randrange(256)
        shift = rng.choice((-3, -2, 2, 3))
        color = tuple(min(255, max(0, channel+shift)) for channel in paper_color)
        draw.line((x, y, x+rng.randrange(2, 13), y+rng.randrange(-2, 3)), fill=color)
    if profile:
        tile = convert_profile(tile, SRGB, profile)
    return tile


def draw_deckled_paper(canvas, photo_size, margin, pad, paper_color, roughness, profile):
    width, height = photo_size
    short = min(photo_size)
    paper_size = (width+2*margin, height+2*margin)
    mask = _deckle_mask(canvas.size, pad, paper_size, short, roughness)
    shade = mask.filter(ImageFilter.GaussianBlur(max(1, round(short*.0035))))
    shade = shade.point(lambda value: value*52//255)
    shade = ImageChops.offset(shade, max(1, round(short*.001)), max(1, round(short*.003)))
    canvas.paste((0, 0, 0), (0, 0), shade)
    tile = _paper_texture(paper_color, profile)
    x, y = pad+margin, pad+margin
    x0, y0, x1, y1 = mask.getbbox()
    # Only allocate/texture the four margins, not a second full-resolution photo.
    boxes = ((x0, y0, x1, y), (x0, y+height, x1, y1),
             (x0, y, x, y+height), (x+width, y, x1, y+height))
    for left, top, right, bottom in boxes:
        strip = Image.new('RGB', (right-left, bottom-top))
        for ty in range(-(top % 256), bottom-top, 256):
            for tx in range(-(left % 256), right-left, 256):
                strip.paste(tile, (tx, ty))
        canvas.paste(strip, (left, top), mask.crop((left, top, right, bottom)))
