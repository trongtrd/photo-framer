#!/usr/bin/env python3
"""Deterministic photo framing. Python 3.10+, Pillow; no network or AI APIs."""
from __future__ import annotations
import argparse
import io
import json
import os
from pathlib import Path
import tempfile
import warnings

from PIL import Image, ImageCms, ImageDraw, ImageFilter, ImageFont, ImageOps

MAX_INPUT_PIXELS = 30_000_000
MAX_OUTPUT_PIXELS = 60_000_000
Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS
BACKGROUNDS_A = {1: '#ffffff', 2: '#faf8f3', 3: '#f2f2f2'}
BACKGROUNDS_B = {1: '#5a5a5a', 2: '#ffffff', 3: '#faf8f3'}
FRAMES = {1: (32, 32, 31), 2: (242, 242, 240), 3: (66, 66, 65)}
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()

def choices(style, code=None):
    """Style-specific three-number menu, default A=2-2-1, B=1-2-1."""
    if style not in ('A', 'B'):
        raise ValueError('Style must be A or B.')
    code = code or ('2-2-1' if style == 'A' else '1-2-1')
    parts = code.split('-')
    if len(parts) != 3 or any(x not in ('1', '2', '3') for x in parts):
        raise ValueError('Choices must be three numbers from 1 to 3, e.g. 2-2-1.')
    return tuple(map(int, parts))

def load_photo(path, crop=None):
    notes = []
    # Pillow decodes some 16-bit PNG color types into 8-bit RGB/RGBA.
    # Inspect the encoded depth before decoding; mode alone cannot detect it.
    with open(path, 'rb') as stream:
        header = stream.read(29)
    if (len(header) >= 29 and header[:8] == b'\x89PNG\r\n\x1a\n'
            and header[8:16] == b'\x00\x00\x00\rIHDR' and header[24] > 8):
        raise ValueError('High-bit-depth images are unsupported; export an 8-bit RGB copy.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(path) as source:
            if source.format not in ('JPEG', 'PNG'):
                raise ValueError('Version 0.1 supports JPEG and PNG only.')
            if getattr(source, 'n_frames', 1) != 1:
                raise ValueError('Animated images are not supported.')
            if source.width * source.height > MAX_INPUT_PIXELS:
                raise ValueError('Input exceeds 30 megapixels; provide a smaller copy.')
            source.load()  # Never accept truncated files.
            profile = source.info.get('icc_profile')
            photo = ImageOps.exif_transpose(source).copy()
    if crop:
        x0, y0, x1, y1 = crop
        if not (0 <= x0 < x1 <= photo.width and 0 <= y0 < y1 <= photo.height):
            raise ValueError('Crop must fit within the oriented image.')
        photo = photo.crop(crop)
        notes.append('Explicit crop applied.')
    if photo.mode.startswith('I') or photo.mode == 'F':
        raise ValueError('High-bit-depth images are unsupported; export an 8-bit RGB copy.')
    # Preserve alpha/tRNS in the source mode before ICC conversion can discard
    # alpha or reinterpret a grayscale transparency key as an RGB key.
    alpha = None
    if photo.mode in ('RGBA', 'LA') or 'transparency' in photo.info:
        alpha = photo.convert('RGBA').getchannel('A')
    if photo.mode == 'LA':
        photo = photo.getchannel('L')
    if profile:
        # Validate profiles; do not silently discard broken color information.
        source_profile = ImageCms.ImageCmsProfile(io.BytesIO(profile))
        if photo.mode not in ('RGB', 'RGBA', 'P'):
            photo = ImageCms.profileToProfile(photo, source_profile,
                        ImageCms.ImageCmsProfile(io.BytesIO(SRGB)), outputMode='RGB')
            profile = SRGB
            notes.append('Converted profiled non-RGB source to sRGB.')
    elif photo.mode == 'CMYK':
        raise ValueError('CMYK JPEG without an ICC profile: export an sRGB copy first.')
    else:
        profile = profile or SRGB
    if alpha is not None:
        rgba = photo.convert('RGBA')
        rgba.putalpha(alpha)
        if alpha.getextrema()[0] < 255:
            # A physical print has an opaque paper backing.
            backing = Image.new('RGBA', photo.size, 'white')
            photo = Image.alpha_composite(backing, rgba).convert('RGB')
            notes.append('Transparency flattened on white paper; output is opaque.')
        else:
            photo = rgba.convert('RGB')
    else:
        photo = photo.convert('RGB')
    return photo, profile, notes

def shadow(canvas, box, blur, offset, opacity):
    mask = Image.new('L', canvas.size)
    x0, y0, x1, y1 = box
    dx, dy = offset
    ImageDraw.Draw(mask).rectangle((x0+dx, y0+dy, x1+dx-1, y1+dy-1), fill=opacity)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste((0, 0, 0), (0, 0), mask)

def render(photo, style='A', code=None, caption=None, font_path=None):
    one, two, three = choices(style, code)
    w, h = photo.size
    s = min(w, h)
    if s < 16:
        raise ValueError('The shorter image edge must be at least 16 pixels.')
    if style == 'A':
        margin = max(4, round(s * {1: .10, 2: .165, 3: .23}[one]))
        size = (w+2*margin, h+2*margin)
    else:
        mat = max(4, round(s * {1: .10, 2: .16, 3: .23}[two]))
        frame = max(2, round(s*.035))
        wall = max(4, round(s*.18))
        fw, fh = w+2*(mat+frame), h+2*(mat+frame)
        size = (fw+2*wall, fh+2*wall)
    if size[0]*size[1] > MAX_OUTPUT_PIXELS:
        raise ValueError('Framed output exceeds 60 megapixels; provide a smaller copy.')
    if style == 'A':
        canvas = Image.new('RGB', size, BACKGROUNDS_A[three])
        box = (margin, margin, margin+w, margin+h)
        strength = {1: .60, 2: 1., 3: 1.40}[two]
        shadow(canvas, box, s*.018, (-s*.014, s*.014), round(85*strength))
        shadow(canvas, box, s*.006, (-s*.006, s*.006), round(41*strength))
        pos = (margin, margin)
        caption_space = margin
    else:
        canvas = Image.new('RGB', size, BACKGROUNDS_B[three])
        box = (wall, wall, wall+fw, wall+fh)
        shadow(canvas, box, s*.032, (0, s*.018), 76)
        shadow(canvas, box, s*.009, (0, s*.007), 48)
        d = ImageDraw.Draw(canvas)
        frame_color = FRAMES[one]
        d.rectangle((wall, wall, wall+fw-1, wall+fh-1), fill=frame_color)
        d.line((wall, wall, wall+fw-1, wall), fill=tuple(min(255,c+10) for c in frame_color))
        ix, iy = wall+frame, wall+frame
        iw, ih = w+2*mat, h+2*mat
        mask = Image.new('L', size, 105)
        ImageDraw.Draw(mask).rectangle((ix, iy, ix+iw-1, iy+ih-1), fill=0)
        mask = mask.filter(ImageFilter.GaussianBlur(s*.011))
        board = Image.new('RGB', (iw, ih), 'white')
        board.paste((0,0,0), (0,0), mask.crop((ix, iy, ix+iw, iy+ih)))
        canvas.paste(board, (ix, iy))
        pos = (ix+mat, iy+mat)
        caption_space = mat
    canvas.paste(photo, pos)
    if caption:
        if not font_path:
            raise ValueError('A Unicode-capable --font file is required for captions.')
        if '\n' in caption or len(caption) > 200:
            raise ValueError('Use a single-line caption up to 200 characters.')
        font = ImageFont.truetype(str(font_path), max(9, round(s*.018)))
        d = ImageDraw.Draw(canvas)
        bounds = d.textbbox((0,0), caption, font=font)
        tw, th = bounds[2]-bounds[0], bounds[3]-bounds[1]
        if tw > w or th > caption_space*.65:
            raise ValueError('Caption does not fit; shorten it or choose a wider border.')
        left = pos[0]+w-tw-bounds[0]
        top = pos[1]+h+(caption_space-th)//2-bounds[1]
        d.text((left, top), caption, font=font, fill=(100,100,100))
    return canvas, pos

def save_verified(image, destination, profile, original=None, photo_pos=None):
    """Validate complete encoded file before publishing; never overwrite an existing file."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.framer-', suffix='.tmp', dir=destination.parent)
    try:
        fmt = 'JPEG' if destination.suffix.lower() in ('.jpg', '.jpeg') else 'PNG'
        with os.fdopen(fd, 'wb') as stream:
            image.save(stream, format=fmt, icc_profile=profile,
                       **({'quality': 92, 'subsampling': 0} if fmt == 'JPEG' else {}))
            stream.flush()
            os.fsync(stream.fileno())
        with Image.open(temporary) as check:
            check.verify()
        with Image.open(temporary) as check:
            check.load()
            if check.size != image.size:
                raise ValueError('Output dimensions failed verification.')
            if original is not None and fmt == 'PNG':
                x, y = photo_pos
                region = check.crop((x,y,x+original.width,y+original.height))
                if region.tobytes() != original.tobytes():
                    raise ValueError('Photo pixel preservation failed verification.')
        candidate = destination
        for count in range(10000):
            try:
                os.link(temporary, candidate)  # Atomic, refuses to replace existing paths.
                return candidate.resolve()
            except FileExistsError:
                candidate = destination.with_name(f'{destination.stem}_{count+2}{destination.suffix}')
        raise ValueError('Too many existing output files with the same name.')
    finally:
        Path(temporary).unlink(missing_ok=True)

def preview(photo, profile):
    # Convert only the small preview to sRGB; final RGB PNG retains source pixels/profile.
    photo = photo.copy()
    photo.thumbnail((1100,1100), Image.Resampling.LANCZOS)
    photo = ImageCms.profileToProfile(photo,
                ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.ImageCmsProfile(io.BytesIO(SRGB)), outputMode='RGB')
    results = [render(photo, style)[0] for style in ('A','B')]
    for image in results:
        image.thumbnail((760,980), Image.Resampling.LANCZOS)
    height = max(i.height for i in results)+90
    board = Image.new('RGB',(1600,height),(238,238,238))
    d = ImageDraw.Draw(board)
    font = ImageFont.load_default(size=24)
    for i,(label,image) in enumerate(zip(('A / Floating photo','B / Gallery frame'),results)):
        d.text((i*800+20,18),label,font=font,fill=(30,30,30))
        board.paste(image,(i*800+(800-image.width)//2,65+(height-75-image.height)//2))
    return board

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path, nargs='+')
    parser.add_argument('--style', choices=['A','B'], default='A')
    parser.add_argument('--choices', help='A: margin-shadow-background; B: frame-mat-background')
    parser.add_argument('--preview', action='store_true', help='Preview A/B on the first input only')
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--share', action='store_true', help='Also export an sRGB JPEG, max 2048 px')
    parser.add_argument('--crop', type=int, nargs=4, metavar=('LEFT','TOP','RIGHT','BOTTOM'))
    parser.add_argument('--caption')
    parser.add_argument('--font', type=Path)
    args = parser.parse_args(argv)
    choices(args.style, args.choices)
    if args.crop and len(args.inputs) != 1:
        parser.error('--crop accepts exactly one input to avoid unintended batch cropping.')
    results = []
    for path in (args.inputs[:1] if args.preview else args.inputs):
        try:
            photo, profile, notes = load_photo(path, args.crop)
            stem = path.stem
            if args.preview:
                image = preview(photo, profile)
                outputs = [save_verified(image,args.out_dir/f'{stem}_AB_preview.jpg',SRGB)]
            else:
                image, pos = render(photo,args.style,args.choices,args.caption,args.font)
                outputs = [save_verified(image,args.out_dir/f'{stem}_{args.style}.png',profile,photo,pos)]
                if args.share:
                    image.thumbnail((2048,2048),Image.Resampling.LANCZOS)
                    image = ImageCms.profileToProfile(image,
                                ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                                ImageCms.ImageCmsProfile(io.BytesIO(SRGB)),outputMode='RGB')
                    outputs.append(save_verified(image,args.out_dir/f'{stem}_{args.style}_share.jpg',SRGB))
            results.append({'input': str(path), 'status':'ok', 'outputs':list(map(str,outputs)), 'notes':notes})
        except Exception as error:
            results.append({'input':str(path),'status':'error','error':str(error)})
    # ASCII JSON escapes preserve Unicode paths even on legacy Windows stdout.
    print(json.dumps({'results':results},ensure_ascii=True,indent=2))
    return int(any(r['status']=='error' for r in results))

if __name__ == '__main__':
    raise SystemExit(main())
