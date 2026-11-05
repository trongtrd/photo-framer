"""B — Gallery frame: white mat with inner shadow inside a frame on a wall."""
from __future__ import annotations

from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFilter

from ..components.caption import draw_caption
from ..components.shadow import shadow
from .base import COMMON, Row, Style

MATS = {1: .10, 2: .16, 3: .23}
FRAMES = {1: (32, 32, 31), 2: (242, 242, 240), 3: (66, 66, 65)}
BACKGROUNDS = {1: '#5a5a5a', 2: '#ffffff', 3: '#faf8f3'}


class Layout(NamedTuple):
    size: tuple
    mat: int
    frame: int
    wall: int
    frame_size: tuple


def layout(photo_size, choices):
    w, h = photo_size
    s = min(w, h)
    mat = max(4, round(s * MATS[choices[1]]))
    frame = max(2, round(s*.035))
    wall = max(4, round(s*.18))
    fw, fh = w+2*(mat+frame), h+2*(mat+frame)
    return Layout((fw+2*wall, fh+2*wall), mat, frame, wall, (fw, fh))


def paint(photo, plan, settings, ctx):
    one, _, three = settings.choices
    w, h = photo.size
    s = min(w, h)
    size, mat, frame, wall = plan.size, plan.mat, plan.frame, plan.wall
    fw, fh = plan.frame_size
    canvas = Image.new('RGB', size, BACKGROUNDS[three])
    box = (wall, wall, wall+fw, wall+fh)
    shadow(canvas, box, s*.032, (0, s*.018), 76)
    shadow(canvas, box, s*.009, (0, s*.007), 48)
    d = ImageDraw.Draw(canvas)
    frame_color = FRAMES[one]
    d.rectangle((wall, wall, wall+fw-1, wall+fh-1), fill=frame_color)
    d.line((wall, wall, wall+fw-1, wall), fill=tuple(min(255, c+10) for c in frame_color))
    ix, iy = wall+frame, wall+frame
    iw, ih = w+2*mat, h+2*mat
    mask = Image.new('L', size, 105)
    ImageDraw.Draw(mask).rectangle((ix, iy, ix+iw-1, iy+ih-1), fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(s*.011))
    board = Image.new('RGB', (iw, ih), 'white')
    board.paste((0, 0, 0), (0, 0), mask.crop((ix, iy, ix+iw, iy+ih)))
    canvas.paste(board, (ix, iy))
    pos = (ix+mat, iy+mat)
    canvas.paste(photo, pos)
    if settings.caption:
        draw_caption(canvas, settings.caption, settings.font_path, s, pos, photo.size, mat)
    return canvas, pos


STYLE = Style(
    code='B', name=('Gallery frame', 'Khung gallery'),
    readme_title='B · Gallery',
    look=('Black frame and white mat', 'Khung đen, bo giấy trắng'),
    preview_label='B / Gallery frame', default='1-2-1',
    rows=(Row(('Frame color', 'Màu khung'), (('Black', 'Đen'), ('White', 'Trắng'),
                                              ('Charcoal', 'Xám than'))),
          Row(('White mat', 'Bo giấy trắng'), (('Narrow', 'Hẹp'), ('Medium', 'Vừa'), ('Wide', 'Rộng'))),
          Row(('Outer background', 'Nền ngoài khung'), (('Gray', 'Xám'), ('White', 'Trắng'),
                                                         ('Ivory', 'Trắng ngà')))),
    choices_hint='frame-mat-background', accepts=COMMON,
    layout=layout, paint=paint)
