"""render(): validate settings for one photo, lay out the canvas and paint it."""
from __future__ import annotations

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


def render(photo, settings, *, profile=None, meta=None, echo_colors=None):
    """Frame one prepared RGB photo; returns (canvas, photo position).

    The photo is pasted unscaled; every decoration stays outside it.
    """
    style = get_style(settings.style)
    check_options(settings, style)
    validate_signature(settings)
    style.validate(settings)
    w, h = photo.size
    if min(w, h) < MIN_SHORT_EDGE:
        raise ValueError(f'The shorter image edge must be at least {MIN_SHORT_EDGE} pixels.')
    caption = settings.caption
    if caption:
        if not settings.font_path:
            raise ValueError('A Unicode-capable --font file is required for captions.')
        if '\n' in caption or len(caption) > MAX_TEXT_LENGTH:
            raise ValueError(f'Use a single-line caption up to {MAX_TEXT_LENGTH} characters.')
    plan = style.layout((w, h), settings)
    limit = style.max_output_pixels
    if plan.size[0]*plan.size[1] > limit:
        raise ValueError(f'Framed output exceeds {limit // 1_000_000} megapixels; '
                         'provide a smaller copy.')
    return style.paint(photo, plan, settings, Context(profile, meta or {}, echo_colors))
