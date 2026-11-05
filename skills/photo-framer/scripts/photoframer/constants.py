"""Global limits, asset paths and the sRGB profile; style constants live in styles/."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

VERSION = '0.13.0'

MAX_INPUT_PIXELS = 30_000_000
MAX_OUTPUT_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS
MAX_TEXT_LENGTH = 200
SHARE_MAX_EDGE = 2048
MIN_SHORT_EDGE = 16

SKILL_DIR = Path(__file__).resolve().parent.parent.parent
LOGO_DIR = SKILL_DIR / 'assets' / 'logos'
FONTS_DIR = SKILL_DIR / 'assets' / 'fonts'
PROFILES_DIR = SKILL_DIR / 'assets' / 'profiles'
SPECS_FONT_FILES = ('Inter-Regular.ttf', 'Inter-SemiBold.ttf')

# LittleCMS's built-in sRGB with its creation date fixed (assets/profiles/README.md), so outputs
# that embed it are identical from one run to the next.
SRGB = (PROFILES_DIR / 'srgb.icc').read_bytes()
