"""Render settings and the named-flag compatibility matrix.

Three-digit choice codes are a frozen contract: an existing code never changes
meaning. New features arrive as named options declared here; each style lists
the options it accepts in its `accepts` set, and render() rejects the rest.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Option:
    field: str   # Settings attribute
    flag: str    # CLI flag
    # Generic options are rejected by render() for styles that do not accept
    # them. A non-generic option is rejected by the style's own validator,
    # which needs to report other problems first (F checks its two corner
    # fields before telling the user to drop --caption).
    generic: bool = True


OPTIONS = (
    Option('left_text', '--left-text'),
    Option('frame_color', '--frame-color'),
    Option('right_text', '--right-text'),
    Option('caption', '--caption', generic=False),
    Option('font_path', '--font'),
    # Capture details typed by the user (film scans, files without EXIF).
    Option('camera', '--camera'),
    Option('lens', '--lens'),
    Option('iso', '--iso'),
    Option('aperture', '--aperture'),
    Option('shutter', '--shutter'),
    Option('focal', '--focal'),
    Option('raw_model', '--raw-model'),
    Option('ratio', '--ratio'),
    Option('background', '--background'),
    Option('blur_tone', '--blur-tone'),
    # Gallery label (H) and a PNG signature/logo in the margin below the photo.
    Option('title', '--title'),
    Option('subtitle', '--subtitle'),
    Option('signature', '--signature'),
    Option('signature_position', '--signature-position'),
    Option('signature_width', '--signature-width'),
    Option('signature_opacity', '--signature-opacity'),
)
SIGNATURE_OPTIONS = frozenset({'signature', 'signature_position', 'signature_width',
                               'signature_opacity'})
SPEC_OPTIONS = frozenset({'camera', 'lens', 'iso', 'aperture', 'shutter', 'focal', 'raw_model'})
# Flags handled by the CLI for every style; listed in the generated matrix.
GLOBAL_FLAGS = ('--share', '--crop', '--metadata')


def parse_choices(style, code=None):
    """Style-specific three-row menu answer, e.g. '2-2-1' -> (2, 2, 1)."""
    from .registry import STYLES
    if style not in STYLES:
        codes = list(STYLES)
        raise ValueError(f"Style must be {', '.join(codes[:-1])} or {codes[-1]}.")
    code = code or STYLES[style].default
    parts = code.split('-')
    if len(parts) != 3 or any(x not in ('1', '2', '3') for x in parts):
        raise ValueError('Choices must be three numbers from 1 to 3, e.g. 2-2-1.')
    return tuple(map(int, parts))


@dataclass(frozen=True)
class Settings:
    """One style, its choice code and the named options for a batch."""
    style: str = 'A'
    code: str | None = None
    caption: str | None = None
    font_path: str | Path | None = None
    left_text: str | None = None
    right_text: str | None = None
    frame_color: str | None = None
    camera: str | None = None
    lens: str | None = None
    iso: float | None = None
    aperture: float | None = None
    shutter: float | None = None      # seconds
    focal: float | None = None        # millimetres
    raw_model: bool | None = None     # True: EXIF model code instead of the display name
    ratio: str | None = None          # H canvas ratio, overrides menu row 1
    background: str | None = None     # H: 'blur' replaces the plain mat
    blur_tone: str | None = None      # H blur: 'dark' (default), 'neutral', 'light'
    title: str | None = None          # H gallery label, Inter SemiBold line below the photo
    subtitle: str | None = None       # H gallery label, second line (needs a title)
    signature: str | Path | None = None   # PNG placed in the margin below the photo
    signature_position: str | None = None  # bottom-right (default), bottom-center, bottom-left
    signature_width: float | None = None   # fraction of canvas width, default 0.15
    signature_opacity: float | None = None  # 0.05-1, default 1
    choices: tuple[int, int, int] = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'choices', parse_choices(self.style, self.code))


def check_options(settings, style):
    """Reject generic named options the style does not accept, in OPTIONS order."""
    from .registry import STYLES
    for option in OPTIONS:
        if not option.generic or option.field in style.accepts:
            continue
        if getattr(settings, option.field) is not None:
            allowed = ' or '.join(code for code, other in STYLES.items()
                                  if option.field in other.accepts)
            raise ValueError(f'{option.flag} is supported only with style {allowed} (or --preview).')
