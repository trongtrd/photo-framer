"""Photo Framer renderer package. The CLI entry point is scripts/frame_photo.py."""
from .constants import MAX_INPUT_PIXELS, MAX_OUTPUT_PIXELS, SRGB, VERSION
from .registry import STYLES
from .renderer import render
from .settings import OPTIONS, Settings, parse_choices

__all__ = ['MAX_INPUT_PIXELS', 'MAX_OUTPUT_PIXELS', 'OPTIONS', 'SRGB', 'STYLES', 'Settings',
           'VERSION', 'parse_choices', 'render']
