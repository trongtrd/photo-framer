"""Loading inputs safely and publishing verified outputs without overwriting."""
from __future__ import annotations

from contextlib import contextmanager
import io
import os
from pathlib import Path
import tempfile
import warnings

from PIL import Image, ImageCms, ImageOps

from .color import convert_profile
from .constants import MAX_INPUT_PIXELS, SRGB


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
                raise ValueError('Version 0.2 supports JPEG and PNG only.')
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
        ImageCms.ImageCmsProfile(io.BytesIO(profile))
        if photo.mode not in ('RGB', 'RGBA', 'P'):
            photo = convert_profile(photo, profile, SRGB)
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


@contextmanager
def _allow_pixels(count):
    """Re-open our own just-written output, which may exceed the input limit.

    Image.MAX_IMAGE_PIXELS guards untrusted inputs (Pillow refuses twice that
    many pixels). Raise it only to the exact size just encoded, then restore it.
    """
    previous = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = max(previous or 0, count)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', Image.DecompressionBombWarning)
            yield
    finally:
        Image.MAX_IMAGE_PIXELS = previous


def save_verified(image, destination, profile, original=None, photo_pos=None, exif=None):
    """Validate complete encoded file before publishing; never overwrite an existing file."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.framer-', suffix='.tmp', dir=destination.parent)
    try:
        fmt = 'JPEG' if destination.suffix.lower() in ('.jpg', '.jpeg') else 'PNG'
        with os.fdopen(fd, 'wb') as stream:
            options = {'quality': 92, 'subsampling': 0} if fmt == 'JPEG' else {}
            if exif:
                options['exif'] = exif
            image.save(stream, format=fmt, icc_profile=profile, **options)
            stream.flush()
            os.fsync(stream.fileno())
        with _allow_pixels(image.width*image.height), Image.open(temporary) as check:
            check.verify()
        with _allow_pixels(image.width*image.height), Image.open(temporary) as check:
            check.load()
            if check.size != image.size:
                raise ValueError('Output dimensions failed verification.')
            if original is not None and fmt == 'PNG':
                x, y = photo_pos
                region = check.crop((x, y, x+original.width, y+original.height))
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
