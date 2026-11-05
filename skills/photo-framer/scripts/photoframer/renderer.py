"""render(): validate settings for one photo, lay out the canvas and paint it."""
from __future__ import annotations

import math

from .constants import MAX_TEXT_LENGTH, MIN_SHORT_EDGE
from .registry import get_style
from .components.signature import OPACITY_RANGE, POSITIONS, WIDTH_RANGE
from .settings import check_options
from .styles.base import Context


def validate_signature(settings):
    extras = (settings.signature_position, settings.signature_width, settings.signature_opacity)
    if settings.signature is None:
        if any(value is not None for value in extras):
            raise ValueError('--signature-position, --signature-width and --signature-opacity '
                             'require --signature.')
        return
    if settings.signature_position is not None and settings.signature_position not in POSITIONS:
        raise ValueError('--signature-position must be ' + ', '.join(POSITIONS) + '.')
    for value, (low, high), flag in ((settings.signature_width, WIDTH_RANGE, '--signature-width'),
                                     (settings.signature_opacity, OPACITY_RANGE, '--signature-opacity')):
        if value is not None and not low <= value <= high:
            raise ValueError(f'{flag} must be between {low:g} and {high:g}.')


def suggested_photo_size(photo_size, settings, style):
    """Largest proportionate integer size that fits the selected output layout."""
    w, h = photo_size
    edge = max(photo_size)
    low = math.ceil(edge*MIN_SHORT_EDGE/min(photo_size))
    high, best = edge-1, None
    while low <= high:
        target = (low+high)//2
        size = (w*target//edge, h*target//edge)
        plan = style.layout(size, settings)
        if plan.size[0]*plan.size[1] <= style.max_output_pixels:
            best, low = size, target+1
        else:
            high = target-1
    return best


def plan_render(photo_size, settings):
    """Validate and check total output pixels before allocating a canvas."""
    style = get_style(settings.style)
    check_options(settings, style)
    validate_signature(settings)
    style.validate(settings)
    w, h = photo_size
    if min(w, h) < MIN_SHORT_EDGE:
        raise ValueError(f'The shorter image edge must be at least {MIN_SHORT_EDGE} pixels.')
    caption = settings.caption
    if caption:
        if '\n' in caption or len(caption) > MAX_TEXT_LENGTH:
            raise ValueError(f'Use a single-line caption up to {MAX_TEXT_LENGTH} characters.')
    plan = style.layout((w, h), settings)
    limit = style.max_output_pixels
    if plan.size[0]*plan.size[1] > limit:
        suggested = suggested_photo_size(photo_size, settings, style)
        hint = (f'export a copy no larger than {suggested[0]}x{suggested[1]} '
                'for these settings' if suggested else
                'choose another canvas ratio or provide a smaller copy')
        raise ValueError(f'Framed output would be {plan.size[0]}x{plan.size[1]} '
                         f'({plan.size[0]*plan.size[1]/1_000_000:.2f} MP), above '
                         f'{limit // 1_000_000} megapixels; {hint}. '
                         'Resizing a copy requires explicit permission; the source is unchanged.')
    return plan


def render(photo, settings, *, profile=None, meta=None, echo_colors=None):
    """Frame one prepared RGB photo; the photo is pasted unscaled."""
    style = get_style(settings.style)
    plan = plan_render(photo.size, settings)
    return style.paint(photo, plan, settings, Context(profile, meta or {}, echo_colors))
