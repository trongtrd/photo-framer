"""ICC helpers and the deterministic Color Echo (style E) color picker."""
from __future__ import annotations

import colorsys
import io

from PIL import Image, ImageCms, ImageColor

from .constants import SRGB

E_NEUTRAL = (232, 228, 220)  # Fallback when no sample color is usable.


def convert_profile(image, source, target):
    """Convert RGB pixels between two ICC profiles given as bytes."""
    return ImageCms.profileToProfile(image,
                ImageCms.ImageCmsProfile(io.BytesIO(source)),
                ImageCms.ImageCmsProfile(io.BytesIO(target)), outputMode='RGB')


def colors_in_profile(colors, profile):
    """Convert only decorative sRGB colors; keep source RGB pixels/profile intact."""
    if not profile:
        return colors
    palette = Image.new('RGB', (len(colors), 1))
    palette.putdata(colors)
    converted = convert_profile(palette, SRGB, profile)
    return tuple(converted.getpixel((index, 0)) for index in range(len(colors)))


def color_echo_color(photo, profile=None, tone=1, frame_color=None):
    """One deterministic sRGB color, from <=96x96 samples; no AI or variants."""
    if frame_color is not None:
        try:
            color = ImageColor.getrgb(frame_color)
        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError('Use an opaque RGB --frame-color, e.g. #ad896c or navy.') from error
        if len(color) != 3 or any(channel < 0 or channel > 255 for channel in color):
            raise ValueError('--frame-color must be an opaque RGB color.')
        return color

    scale = min(1, 96 / max(photo.size))
    sample = photo.resize((max(1, round(photo.width*scale)),
                           max(1, round(photo.height*scale))), Image.Resampling.BOX)
    if profile:
        sample = convert_profile(sample, profile, SRGB)
    buckets = {}
    width, height = sample.size
    for y in range(height):
        for x in range(width):
            red, green, blue = sample.getpixel((x, y))
            _, lightness, saturation = colorsys.rgb_to_hls(red/255, green/255, blue/255)
            if saturation < .10 or not .14 <= lightness <= .86:
                continue
            weight = 3 if (x < width*.2 or x >= width*.8 or
                           y < height*.2 or y >= height*.8) else 1
            key = (red//24, green//24, blue//24)
            totals = buckets.setdefault(key, [0, 0, 0, 0])
            totals[0] += weight
            for channel, value in enumerate((red, green, blue), 1):
                totals[channel] += weight*value
    if not buckets:
        return E_NEUTRAL

    candidates = []
    for key, (weight, red, green, blue) in buckets.items():
        rgb = (red/weight/255, green/weight/255, blue/weight/255)
        hue, lightness, saturation = colorsys.rgb_to_hls(*rgb)
        # Midtones count more than dark roof/shadow or bright highlight areas.
        score = weight * max(.1, 1-abs(lightness-.5)/.4) * (.7+.3*min(saturation/.5, 1))
        candidates.append((score, key, hue, lightness, saturation))
    _, _, hue, lightness, saturation = max(candidates)
    if tone == 1:  # Muted default; adjust the border, never the photo.
        lightness = min(.68, max(.36, lightness+.06))
        saturation = min(.48, max(.18, saturation*.7))
    elif tone == 3:
        lightness = .80
        saturation = min(.35, saturation*.5)
    return tuple(round(value*255) for value in colorsys.hls_to_rgb(hue, lightness, saturation))


def color_echo_colors(photo, profile=None, tone=1, frame_color=None):
    """Base and contrasting inset, expressed in sRGB for reusable hex colors."""
    base = color_echo_color(photo, profile, tone, frame_color)
    brightness = sum(value*weight for value, weight in zip(base, (.2126, .7152, .0722)))/255
    inset = (24, 28, 36) if brightness >= .45 else (244, 240, 232)
    return base, inset


def hex_color(rgb):
    return '#' + ''.join(f'{channel:02x}' for channel in rgb)
