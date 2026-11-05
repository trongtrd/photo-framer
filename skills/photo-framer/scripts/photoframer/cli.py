"""Command-line interface: one JSON result per input, never overwrite outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from .capture import load_capture_sidecar, number as _number, text_value as _text_value
from .color import convert_profile
from .constants import LOGO_DIR, SHARE_MAX_EDGE, SRGB, VERSION
from .io import load_photo, save_verified
from .metadata import (brand_slug, brand_wordmark, exif_for_output, gear_name,
                       read_capture_metadata, read_source_exif)
from .preview import H_OPTIONS as H_PREVIEW_OPTIONS, OVERLAY_OPTIONS, preview, preview_styles
from .registry import DEFAULT_STYLE, STYLES
from .renderer import render
from .settings import SPEC_OPTIONS, Settings, check_options
from .components.signature import POSITIONS as SIGNATURE_POSITIONS
from .styles.e_color_echo import resolve_colors
from .styles.h_minimal_mat import (BACKGROUND_MODES as H_BACKGROUND_MODES, BLUR_TONES as H_BLUR_TONES,
                                   DEFAULT_BLUR_TONE as H_DEFAULT_BLUR_TONE, RATIOS as H_RATIOS)

JPEG_EXIF_LIMIT = 65_000  # A JPEG APP1 segment holds at most 65,533 bytes.
DESCRIPTION = 'Deterministic photo framing. Python 3.10+, Pillow; no network or AI APIs.'


def _fraction(flag, low, high):
    def parse(value):
        try:
            number = float(value)
        except ValueError:
            number = None
        if number is None or not low <= number <= high:
            raise argparse.ArgumentTypeError(f'{flag} must be a number from {low:g} to {high:g}')
        return number
    return parse


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
                             'H 4:5/1:1/3:4/9:16/16:9 use exact '
                             '1080x1350/1080x1080/1080x1440/1080x1920/1920x1080')
    parser.add_argument('--crop', type=int, nargs=4, metavar=('LEFT', 'TOP', 'RIGHT', 'BOTTOM'))
    parser.add_argument('--caption')
    parser.add_argument('--left-text', help='Style F: exact lower-left text; empty string means intentionally blank')
    parser.add_argument('--right-text', help='Style D or F: exact lower-right text; F allows an intentionally empty string')
    parser.add_argument('--frame-color', help='Style E: one fixed sRGB hex/name for the entire batch, skips auto analysis')
    parser.add_argument('--font', type=Path)
    parser.add_argument('--metadata', choices=('keep', 'strip'), default='keep',
                        help='keep (default): copy the source EXIF, including GPS, into the final PNG '
                             'and share JPEG, with orientation reset and thumbnail/maker notes removed; '
                             'strip: write no EXIF. Previews never carry metadata')
    mat = parser.add_argument_group('style H options')
    mat.add_argument('--ratio', choices=list(H_RATIOS),
                     help='canvas ratio, overrides the first menu row (1=4:5, 2=1:1, 3=original)')
    mat.add_argument('--background', choices=list(H_BACKGROUND_MODES),
                     help='blur: fill the canvas with a blurred copy of the photo instead of the mat color')
    mat.add_argument('--blur-tone', choices=list(H_BLUR_TONES),
                     help=f'with --background blur: {H_DEFAULT_BLUR_TONE} (default), neutral or light')
    label = parser.add_argument_group('gallery label (A, B, G, H)',
                                       'Centered text below the photo; separate from captions and signatures.')
    label.add_argument('--title', type=_text_value('--title'),
                     help='gallery label: exact title in Inter SemiBold (as style D), centered below the photo')
    label.add_argument('--subtitle', type=_text_value('--subtitle'),
                     help='gallery label: exact second line in smaller gray Inter Regular (needs --title)')
    overlay = parser.add_argument_group('signature or logo (A, B, E, G)',
                                        'A PNG placed in the margin below the photo, never over it.')
    overlay.add_argument('--signature', type=Path, help='transparent PNG signature or logo')
    overlay.add_argument('--signature-position', choices=SIGNATURE_POSITIONS,
                         help='default bottom-right; aligned to the photo edges')
    overlay.add_argument('--signature-width', type=_fraction('--signature-width', .02, .5),
                         help='width as a fraction of the canvas width, default 0.15')
    overlay.add_argument('--signature-opacity', type=_fraction('--signature-opacity', .05, 1),
                         help='0.05-1, default 1')
    specs = parser.add_argument_group('capture details for C/D', 'Typed values win over EXIF/XMP, '
                                      'field by field; nothing is filled in that was not supplied.')
    specs.add_argument('--camera', type=_text_value('--camera'), help='exact camera text, shown verbatim')
    specs.add_argument('--lens', type=_text_value('--lens'), help='exact lens text')
    specs.add_argument('--iso', type=_number('--iso', prefix='iso'), help='e.g. 400')
    specs.add_argument('--aperture', type=_number('--aperture', prefix='f/'), help='e.g. 2.8 or f/2.8')
    specs.add_argument('--shutter', type=_number('--shutter', suffix='s', fraction=True),
                       help='seconds, e.g. 1/125 or 2')
    specs.add_argument('--focal', type=_number('--focal', suffix='mm'), help='millimetres, e.g. 50')
    specs.add_argument('--raw-model', action='store_true',
                       help='show the EXIF model code (e.g. ILCE-7C) instead of the display name (Sony α7C)')
    specs.add_argument('--capture-sidecar', action='store_true',
                       help='read exact sibling <input filename>.json for each C/D image; '
                            'explicit capture flags override JSON, which overrides EXIF/XMP')
    return parser


def metadata_notes(meta, shown, settings):
    """Notes about displayed capture details for the styles in `shown`."""
    notes = []
    model = meta.get('model')
    if model and settings.camera is None:
        raw = bool(settings.raw_model)
        names = {code: gear_name(meta, with_brand=code == 'D', raw_model=raw)
                 for code in shown if code in ('C', 'D')}
        changed = {code: name for code, name in names.items() if name != model}
        if changed:
            values = list(dict.fromkeys(changed.values()))
            shown_as = (f"'{values[0]}'" if len(values) == 1 else
                        ', '.join(f"'{name}' ({code})" for code, name in changed.items()))
            notes.append(f"Model display formatted: '{model}' -> {shown_as}.")
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


def share_copy(image, profile, style, settings):
    exact = style.share_size(settings)
    if exact:
        # The canvas ratio is exact, so this resize never distorts.
        image = image.resize(exact, Image.Resampling.LANCZOS)
    else:
        image.thumbnail((SHARE_MAX_EDGE, SHARE_MAX_EDGE), Image.Resampling.LANCZOS)
    return convert_profile(image, profile, SRGB)


def output_exif(exif, image, args):
    if args.metadata != 'keep' or exif is None:
        return None
    return exif_for_output(exif, image.size)


def process(path, args, settings):
    style = STYLES[settings.style]
    sidecar_notes = []
    if settings.capture_sidecar:
        if not args.preview:
            check_options(settings, style)
        settings, sidecar_notes = load_capture_sidecar(path, settings)
    if style.uses_metadata or args.preview:
        meta, origins = read_capture_metadata(path)
    else:
        meta, origins = {}, {}
    photo, profile, notes = load_photo(path, args.crop, None if args.preview else settings)
    notes += sidecar_notes
    stem = path.stem
    if args.preview:
        specs = {field: getattr(settings, field) for field in SPEC_OPTIONS
                 if getattr(settings, field) is not None}
        h_options = {field: getattr(settings, field) for field in H_PREVIEW_OPTIONS
                     if getattr(settings, field) is not None}
        image = preview(photo, profile, meta, settings.right_text, settings.frame_color, settings.left_text,
                        specs, h_options,
                        {field: getattr(settings, field) for field in OVERLAY_OPTIONS
                         if getattr(settings, field) is not None})
        shown = preview_styles(args.right_text, args.left_text)
        outputs = [save_verified(image, args.out_dir/f'{stem}_{shown}_preview.jpg', SRGB)]
    else:
        shown = settings.style
        echo_colors = resolve_colors(photo, profile, settings) if settings.style == 'E' else None
        image, pos = render(photo, settings, profile=profile, meta=meta, echo_colors=echo_colors)
        exif = read_source_exif(path) if args.metadata == 'keep' else None
        try:
            final_exif = output_exif(exif, image, args)
        except Exception:  # Malformed source EXIF must not cost the framed photo.
            exif = final_exif = None
            notes.append('Source EXIF could not be read for copying; outputs carry no EXIF.')
        if args.share and final_exif and len(final_exif) > JPEG_EXIF_LIMIT:
            raise ValueError('Source EXIF is too large for a JPEG share copy; '
                             'use --metadata strip or omit --share.')
        outputs = [save_verified(image, args.out_dir/f'{stem}_{settings.style}.png',
                                 profile, photo, pos, exif=final_exif)]
        if args.share:
            image = share_copy(image, profile, style, settings)
            outputs.append(save_verified(image, args.out_dir/f'{stem}_{settings.style}_share.jpg', SRGB,
                                         exif=output_exif(exif, image, args)))
        notes += style.notes(settings, share=args.share, origins=origins, echo_colors=echo_colors)
        if settings.signature is not None:
            opacity = settings.signature_opacity if settings.signature_opacity is not None else 1
            notes.append(f'Signature PNG placed {settings.signature_position or "bottom-right"} '
                         f'below the photo at {round(opacity*100)}% opacity; the photo is untouched.')
        if final_exif:
            notes.append('Source EXIF copied into the outputs; orientation reset to 1, '
                         'embedded thumbnail and maker notes removed.')
    if any(STYLES[code].uses_metadata for code in shown):
        notes += metadata_notes(meta, shown, settings)
    return {'input': str(path), 'status': 'ok', 'outputs': list(map(str, outputs)), 'notes': notes}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings(args.style, args.choices, caption=args.caption, font_path=args.font,
                        left_text=args.left_text, right_text=args.right_text,
                        frame_color=args.frame_color, camera=args.camera, lens=args.lens,
                        iso=args.iso, aperture=args.aperture, shutter=args.shutter, focal=args.focal,
                        raw_model=True if args.raw_model else None, ratio=args.ratio,
                        capture_sidecar=True if args.capture_sidecar else None,
                        background=args.background, blur_tone=args.blur_tone, title=args.title,
                        subtitle=args.subtitle, signature=args.signature,
                        signature_position=args.signature_position,
                        signature_width=args.signature_width,
                        signature_opacity=args.signature_opacity)
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
