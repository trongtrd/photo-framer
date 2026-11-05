"""Command-line interface: one JSON result per input, never overwrite outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from .color import convert_profile
from .constants import LOGO_DIR, SHARE_MAX_EDGE, SRGB, VERSION
from .io import load_photo, save_verified
from .metadata import brand_slug, brand_wordmark, display_model, read_capture_metadata
from .preview import preview, preview_styles
from .registry import DEFAULT_STYLE, STYLES
from .renderer import render
from .settings import Settings
from .styles.e_color_echo import resolve_colors

DESCRIPTION = 'Deterministic photo framing. Python 3.10+, Pillow; no network or AI APIs.'


def build_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('inputs', type=Path, nargs='+')
    parser.add_argument('--version', action='version', version=f'Photo Framer {VERSION}')
    parser.add_argument('--style', choices=list(STYLES), default=DEFAULT_STYLE)
    parser.add_argument('--choices', help='; '.join(f'{code}: {style.choices_hint}'
                                                    for code, style in STYLES.items()))
    shown = '/'.join(code for code in STYLES if code != 'D')
    parser.add_argument('--preview', action='store_true',
                        help=f'Preview {shown}; include D when nonempty --right-text is supplied, first input only')
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--share', action='store_true',
                        help=f'Also export an sRGB JPEG, max {SHARE_MAX_EDGE} px; '
                             'H 4:5/1:1 use exact 1080x1350/1080x1080')
    parser.add_argument('--crop', type=int, nargs=4, metavar=('LEFT', 'TOP', 'RIGHT', 'BOTTOM'))
    parser.add_argument('--caption')
    parser.add_argument('--left-text', help='Style F: exact lower-left text; empty string means intentionally blank')
    parser.add_argument('--right-text', help='Style D or F: exact lower-right text; F allows an intentionally empty string')
    parser.add_argument('--frame-color', help='Style E: one fixed sRGB hex/name for the entire batch, skips auto analysis')
    parser.add_argument('--font', type=Path)
    return parser


def metadata_notes(meta, shown):
    """Notes about displayed capture details for the styles in `shown`."""
    notes = []
    model = meta.get('model')
    if model and display_model(model) != model:
        notes.append(f"Model display formatted: '{model}' -> '{display_model(model)}'.")
    if 'C' in shown:
        slug = brand_slug(meta)
        if slug and (LOGO_DIR / f'{slug}.png').is_file():
            notes.append(f'Brand mark: {slug}.')
        elif brand_wordmark(meta):
            notes.append('Brand wordmark drawn; no logo file for this brand.')
    if 'D' in shown:
        notes.append('Style D: user text replaces the brand mark; '
                     'same font, size and weight as the gear line.')
    return notes


def share_copy(image, profile, style, choices):
    exact = style.share_size(choices)
    if exact:
        # The canvas ratio is exact, so this resize never distorts.
        image = image.resize(exact, Image.Resampling.LANCZOS)
    else:
        image.thumbnail((SHARE_MAX_EDGE, SHARE_MAX_EDGE), Image.Resampling.LANCZOS)
    return convert_profile(image, profile, SRGB)


def process(path, args, settings):
    style = STYLES[settings.style]
    if style.uses_metadata or args.preview:
        meta, sources = read_capture_metadata(path)
    else:
        meta, sources = {}, set()
    photo, profile, notes = load_photo(path, args.crop)
    stem = path.stem
    if args.preview:
        image = preview(photo, profile, meta, args.right_text, args.frame_color, args.left_text)
        shown = preview_styles(args.right_text, args.left_text)
        outputs = [save_verified(image, args.out_dir/f'{stem}_{shown}_preview.jpg', SRGB)]
    else:
        shown = settings.style
        echo_colors = resolve_colors(photo, profile, settings) if settings.style == 'E' else None
        image, pos = render(photo, settings, profile=profile, meta=meta, echo_colors=echo_colors)
        outputs = [save_verified(image, args.out_dir/f'{stem}_{settings.style}.png',
                                 profile, photo, pos)]
        if args.share:
            image = share_copy(image, profile, style, settings.choices)
            outputs.append(save_verified(image, args.out_dir/f'{stem}_{settings.style}_share.jpg', SRGB))
        notes += style.notes(settings, share=args.share, sources=sources, echo_colors=echo_colors)
    if any(STYLES[code].uses_metadata for code in shown):
        notes += metadata_notes(meta, shown)
    return {'input': str(path), 'status': 'ok', 'outputs': list(map(str, outputs)), 'notes': notes}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings(args.style, args.choices, caption=args.caption, font_path=args.font,
                        left_text=args.left_text, right_text=args.right_text,
                        frame_color=args.frame_color)
    if args.crop and len(args.inputs) != 1:
        parser.error('--crop accepts exactly one input to avoid unintended batch cropping.')
    results = []
    for path in (args.inputs[:1] if args.preview else args.inputs):
        try:
            results.append(process(path, args, settings))
        except Exception as error:
            results.append({'input': str(path), 'status': 'error', 'error': str(error)})
    # ASCII JSON escapes preserve Unicode paths even on legacy Windows stdout.
    print(json.dumps({'results': results}, ensure_ascii=True, indent=2))
    return int(any(r['status'] == 'error' for r in results))
