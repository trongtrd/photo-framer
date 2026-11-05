"""render(): validate settings for one photo, lay out the canvas and paint it."""
from __future__ import annotations

from .constants import MAX_TEXT_LENGTH, MIN_SHORT_EDGE
from .registry import get_style
from .settings import check_options
from .styles.base import Context


def render(photo, settings, *, profile=None, meta=None, echo_colors=None):
    """Frame one prepared RGB photo; returns (canvas, photo position).

    The photo is pasted unscaled; every decoration stays outside it.
    """
    style = get_style(settings.style)
    check_options(settings, style)
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
