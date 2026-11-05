"""Fonts and the shared single-line text rules for user-supplied wording."""
from __future__ import annotations

from PIL import ImageFont

from . import constants
from .constants import MAX_TEXT_LENGTH, SPECS_FONT_FILES

# Read through the module at call time so tests can point it elsewhere.
FONTS_DIR = constants.FONTS_DIR


def specs_fonts(font_px, font_path=None):
    """Caption-band pair: (regular, emphasis, stroke).

    Bundled Inter gives true Regular + SemiBold faces. A user-supplied --font
    replaces both faces and loses the weight step. Without either, Pillow's
    default face is used and a thin stroke imitates the heavier weight.
    """
    if font_path:
        face = ImageFont.truetype(str(font_path), font_px)
        return face, face, 0
    try:
        regular = ImageFont.truetype(str(FONTS_DIR / SPECS_FONT_FILES[0]), font_px)
        emphasis = ImageFont.truetype(str(FONTS_DIR / SPECS_FONT_FILES[1]), font_px)
        return regular, emphasis, 0
    except OSError:
        face = ImageFont.load_default(size=font_px)
        return face, face, max(1, round(font_px * .028))


def wordmark_font(font_px, font_path=None):
    """Face for the text wordmark fallback, mirroring the emphasis weight."""
    size = round(font_px * 1.6)
    if font_path:
        return ImageFont.truetype(str(font_path), size), 0
    try:
        return ImageFont.truetype(str(FONTS_DIR / SPECS_FONT_FILES[1]), size), 0
    except OSError:
        return ImageFont.load_default(size=size), max(1, round(font_px * .028))


def title_fonts(title_px, subtitle_px, font_path=None):
    """Gallery label faces, matching the spec cards for one typeface across styles.

    Title: Inter SemiBold, like D's gear line and right-side text. Subtitle:
    Inter Regular, like the exposure line. --font replaces both.
    """
    _, title, _ = specs_fonts(title_px, font_path)
    subtitle, _, _ = specs_fonts(subtitle_px, font_path)
    return title, subtitle


def is_single_line(text, forbidden='\r\n\t'):
    """User wording: one line, at most MAX_TEXT_LENGTH characters."""
    return len(text) <= MAX_TEXT_LENGTH and not any(char in text for char in forbidden)
