"""Global limits, asset paths and the sRGB profile; style constants live in styles/."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageCms

VERSION = '0.10.0'

MAX_INPUT_PIXELS = 30_000_000
MAX_OUTPUT_PIXELS = 60_000_000
Image.MAX_IMAGE_PIXELS = MAX_INPUT_PIXELS
MAX_TEXT_LENGTH = 200
SHARE_MAX_EDGE = 2048
MIN_SHORT_EDGE = 16

SKILL_DIR = Path(__file__).resolve().parent.parent.parent
LOGO_DIR = SKILL_DIR / 'assets' / 'logos'
FONTS_DIR = SKILL_DIR / 'assets' / 'fonts'
SPECS_FONT_FILES = ('Inter-Regular.ttf', 'Inter-SemiBold.ttf')

SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
