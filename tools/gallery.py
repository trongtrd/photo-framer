#!/usr/bin/env python3
"""Render the representative README gallery, or check its committed assets.

Each preset row changes one menu setting from the default. Named options have
separate examples; this is coverage of visible controls, not every combination.
Run `python tools/gallery.py`, then `python tools/gen_docs.py`.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'skills/photo-framer/scripts'
sys.path.insert(0, str(SCRIPTS))
from photoframer.constants import SRGB, VERSION  # noqa: E402
from photoframer.registry import STYLES  # noqa: E402

ASSETS = ROOT / 'docs/images/gallery'
THUMBS = ASSETS / 'thumbs'
MANIFEST = ASSETS / 'manifest.json'
SOURCES = {'landscape': 'docs/images/demo-source-final.jpg',
           'portrait': 'docs/images/demo-portrait-source.jpg',
           'scan': 'docs/examples/scan.png'}
SIGNATURE = 'docs/images/gallery/signature.png'
RIGHT_TEXT = 'Berlin, Germany | October 2022'
RECIPE = {'version': 1, 'preview_edge': 1280, 'thumb_edge': 400, 'quality': 88}
THUMBNAIL = {'version': 1, 'edge': 432, 'image_edge': RECIPE['thumb_edge'],
             'background': '#000000'}
DISPLAY_NAMES = {'A': ('Shadow', 'Ảnh nổi'), 'B': ('Gallery', 'Khung gallery'),
                 'C': ('Specs', 'Thông số'), 'D': ('Specs + Text', 'Thông số + chữ riêng'),
                 'E': ('Color', 'Viền màu'), 'F': ('Film', 'Viền phim'),
                 'G': ('Paper', 'Giấy xé'), 'H': ('Canvas', 'Khung tỷ lệ')}
RATIO_LABELS = {'4:5': 'Portrait · 4:5', '1:1': 'Square · 1:1', '3:4': 'Portrait · 3:4',
                '9:16': 'Story · 9:16', '16:9': 'Landscape · 16:9', 'original': 'Thin border'}


def display_title(code):
    return f'{DISPLAY_NAMES[code][0]} / {DISPLAY_NAMES[code][1]} ({code})'


def preset_label(code, index, option):
    if code in 'CD' and index == 2:
        return 'Camera + lens' if option.startswith('Camera') else option
    if code == 'E' and index == 2 and option == 'None':
        return 'No inner edge'
    nouns = {'A': ('margin', 'shadow', 'background'), 'B': ('frame', 'mat', 'surround'),
             'C': ('margin', 'background', ''), 'D': ('margin', 'background', ''),
             'E': ('border', 'color', 'inner edge'), 'F': ('border', 'film', 'sprockets'),
             'G': ('margin', 'paper', 'torn edges')}
    return f'{option} {nouns[code][index]}'


@dataclass
class Example:
    key: str
    style: str
    label: str
    code: str | None = None
    source: str = 'landscape'
    options: dict = field(default_factory=dict)
    hint: str = ''

    def settings(self):
        required = ({'right_text': RIGHT_TEXT} if self.style == 'D' else
                    {'left_text': 'Berlin, Germany', 'right_text': 'October 2022'}
                    if self.style == 'F' else {})
        return {'style': self.style, 'choices': self.code or STYLES[self.style].default,
                **required, **self.options}


def preset_examples(code):
    style = STYLES[code]
    examples = [Example(f'{code.lower()}-default', code, 'Default', style.default)]
    for index, row in enumerate(style.rows):
        for number, option in enumerate(row.options, 1):
            if number == style.default_choices[index]:
                continue
            choices = list(style.default_choices)
            choices[index] = number
            examples.append(Example(f'{code.lower()}-row{index+1}-{number}', code,
                                     preset_label(code, index, option[0]), '-'.join(map(str, choices))))
    return examples


def gallery_rows():
    """Eight style groups; large groups have two or three independent rows."""
    result = {}
    for code in 'ABCDEFG':
        appearance = preset_examples(code)
        extra = []
        if code in 'ABCDEG':
            extra.append(Example(f'{code.lower()}-caption', code, 'Caption',
                                  options={'caption': RIGHT_TEXT}, hint='--caption'))
        if code in 'ABG':
            extra.append(Example(f'{code.lower()}-label', code, 'Label', source='portrait',
                                  options={'title': 'Praha', 'subtitle': 'Prague · Czech Republic'},
                                  hint='--title / --subtitle'))
        if code in 'ABEG':
            extra.append(Example(f'{code.lower()}-signature', code, 'Signature',
                                  options={'signature': SIGNATURE, 'signature_width': .12},
                                  hint='--signature'))
        if code == 'E':
            appearance.append(Example('e-fixed-color', code, 'Shared color',
                                      options={'frame_color': '#ad896c'}, hint='--frame-color'))
        if code == 'F':
            for name, left, right in (('blank', '', ''), ('left', 'Berlin, Germany', ''),
                                       ('right', '', 'October 2022')):
                extra.append(Example(f'f-text-{name}', code,
                                      {'blank': 'No text', 'left': 'Left text only',
                                       'right': 'Right text only'}[name],
                                      options={'left_text': left, 'right_text': right},
                                      hint='--left-text / --right-text'))
        result[code] = [('Appearance / Hình thức', appearance), ('Text / Chữ', extra)]

    canvas = [Example('h-default', 'H', 'Portrait · 4:5 · Default')]
    for ratio in ('1:1', '3:4', '9:16', '16:9', 'original'):
        canvas.append(Example(f'h-ratio-{ratio.replace(":", "x")}', 'H',
                               RATIO_LABELS[ratio],
                               options={'ratio': ratio}, hint=f'--ratio {ratio}'))
    blur = [Example(f'h-blur-{ratio.replace(":", "x")}', 'H',
                     RATIO_LABELS[ratio],
                     options={'ratio': ratio, 'background': 'blur'}, hint=f'--ratio {ratio}')
            for ratio in ('4:5', '1:1', '3:4', '9:16', '16:9', 'original')]
    for tone in ('neutral', 'light'):
        blur.append(Example(f'h-blur-tone-{tone}', 'H', f'Landscape · {tone.title()}',
                             options={'ratio': '16:9', 'background': 'blur', 'blur_tone': tone},
                             hint=f'--blur-tone {tone}'))
    details = [Example('h-gray', 'H', 'Warm gray mat', '1-2-1'),
               Example('h-ivory', 'H', 'Ivory mat', '1-3-1'),
               Example('h-no-keyline', 'H', 'No keyline', '1-1-2'),
               Example('h-thick-keyline', 'H', 'Thick keyline', '1-1-3'),
               Example('h-caption', 'H', 'Caption', options={'caption': RIGHT_TEXT}, hint='--caption'),
               Example('h-portrait', 'H', 'Portrait photo · 4:5', source='portrait'),
               Example('h-label', 'H', 'Label · Square', source='portrait',
                       options={'ratio': '1:1', 'title': 'Praha', 'subtitle': 'Prague · Czech Republic'},
                       hint='--title / --subtitle')]
    result['H'] = [('Ratios / Tỷ lệ', canvas), ('Blur / Nền mờ', blur),
                   ('Details / Chi tiết', details)]
    return result


def technical_examples():
    return [item for code in 'CD' for item in (
        Example(f'{code.lower()}-raw-model', code, 'Raw camera code',
                options={'raw_model': True}, hint='--raw-model'),
        Example(f'{code.lower()}-sidecar', code, 'Supplied capture details', source='scan',
                options={'capture_sidecar': True}, hint='--capture-sidecar'))]


def examples():
    return [item for rows in gallery_rows().values() for _, row in rows for item in row] + technical_examples()


def example_table(row, *, context='', technical=False):
    labels, pictures = [], []
    for item in row:
        name = DISPLAY_NAMES[item.style][0]
        label = f'{name} · {item.label}' if technical else item.label
        if technical:
            label = (html.escape(label) + '<br><code>'
                     + html.escape(item.hint or item.code or STYLES[item.style].default) + '</code>')
        else:
            label = html.escape(label)
        labels.append(label)
        alt = ' · '.join(part for part in (name, context, item.label) if part)
        pictures.append(f'<a href="docs/images/gallery/{item.key}.jpg">'
                        f'<img src="docs/images/gallery/thumbs/{item.key}.png" width="240" '
                        f'alt="{html.escape(alt, quote=True)}"></a>')
    # GitHub shrinks explicit widths; this hidden intrinsic minimum keeps
    # thumbnails readable in its native horizontally scrolling tables.
    spacer = '<span aria-hidden="true">' + '&#160;'*60 + '</span>'
    return '\n'.join(['<table>', '<thead><tr>',
                      *[f'<th width="240" align="center">{label}</th>' for label in labels],
                      '</tr></thead>', '<tbody><tr>',
                      *[f'<td width="240" align="center">{picture}<br>{spacer}</td>' for picture in pictures],
                      '</tr></tbody>', '</table>'])


def technical_block():
    return ('These examples explain input and metadata handling for Specs (C) and Specs + Text (D). '
            'The supplied-details chart is synthetic test artwork, not a camera photograph.\n\n'
            + example_table(technical_examples(), technical=True))


def gallery_block():
    lines = ['Choose a style by name, then compare its appearance and text options. '
             'Canvas has three rows: ratios, blur and details. '
             'Scroll a wide row horizontally and click any preview to enlarge it.', '',
             'These are reduced previews, not full-resolution outputs. The originals stay untouched. '
             'The display surrounds are white for Film and black for the other styles; '
             'they belong only to the thumbnail display, not to the frame. '
             'Click through to see the framed image without that surround. '
             'The sample text is supplied wording, never inferred metadata.', '',
             '| Original landscape | Original portrait |', '| :---: | :---: |']
    cells = [f'<a href="{SOURCES[source]}"><img src="docs/images/gallery/thumbs/source-{source}.png" '
             f'height="140" alt="Original {source} photograph"></a>'
             for source in ('landscape', 'portrait')]
    lines += ['| ' + ' | '.join(cells) + ' |', '']
    for code, rows in gallery_rows().items():
        lines += [f'<a id="style-{code.lower()}"></a>', '', f'### {display_title(code)}', '']
        if code == 'H':
            lines += ['Plain or blurred backgrounds work with every ratio. '
                       '`16:9` is the landscape canvas; `1:1` is square. '
                       'Neither crops or scales the photo. Blur uses the dark tone unless labeled '
                       'Neutral or Light. Canvas takes no signature.', '']
        for heading, row in rows:
            lines += [f'**{heading}**', '']
            context = 'Blur' if code == 'H' and heading.startswith('Blur') else ''
            lines += [example_table(row, context=context), '']
    lines += ['[All settings and choice codes](skills/photo-framer/references/menus.md) · '
               '[Reproduce the gallery](docs/gallery.md)', '']
    return '\n'.join(lines).rstrip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def renderer_digest():
    paths = [SCRIPTS/'frame_photo.py', *sorted((SCRIPTS/'photoframer').rglob('*.py'))]
    value = hashlib.sha256()
    for path in paths:
        value.update(path.relative_to(ROOT).as_posix().encode())
        value.update(path.read_text(encoding='utf-8').encode('utf-8'))  # normalize CRLF
    for path in sorted((ROOT/'skills/photo-framer/assets').rglob('*')):
        if path.is_file() and path.suffix.lower() in ('.ttf', '.png', '.icc', '.json'):
            value.update(path.relative_to(ROOT).as_posix().encode())
            value.update(path.read_text(encoding='utf-8').encode('utf-8')
                         if path.suffix.lower() == '.json' else path.read_bytes())
    return value.hexdigest()


def recipe(item):
    data = {'source': SOURCES[item.source], 'source_sha256': digest(ROOT/SOURCES[item.source]),
            'settings': item.settings(), 'recipe': RECIPE}
    if item.options.get('signature'):
        data['signature_sha256'] = digest(ROOT/SIGNATURE)
    if item.options.get('capture_sidecar'):
        data['sidecar_sha256'] = hashlib.sha256(
            (ROOT/(SOURCES[item.source]+'.json')).read_text(encoding='utf-8').encode('utf-8')).hexdigest()
    return data


def save_preview(image, path, edge):
    reduced = image.copy()
    reduced.thumbnail((edge, edge), Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    reduced.save(path, quality=RECIPE['quality'], subsampling=0, icc_profile=SRGB)


def thumbnail_recipe(style=None):
    return {**THUMBNAIL, 'background': '#ffffff' if style == 'F' else THUMBNAIL['background']}


def save_thumbnail(image, path, presentation):
    reduced = image.convert('RGB')
    reduced.thumbnail((presentation['image_edge'], presentation['image_edge']), Image.Resampling.LANCZOS)
    edge = presentation['edge']
    stage = Image.new('RGB', (edge, edge), presentation['background'])
    stage.paste(reduced, ((edge-reduced.width)//2, (edge-reduced.height)//2))
    path.parent.mkdir(parents=True, exist_ok=True)
    stage.save(path, icc_profile=SRGB)


def file_matches(path, files):
    return path.is_file() and files.get(path.relative_to(ROOT).as_posix()) == digest(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='check recipes, assets and their hashes; write nothing')
    args = parser.parse_args(argv)
    old = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    fingerprint = renderer_digest()
    stale = []
    records = {}
    for item in examples():
        expected = recipe(item)
        presentation = thumbnail_recipe(item.style)
        saved = old.get('examples', {}).get(item.key, {})
        preview, thumbnail = ASSETS/f'{item.key}.jpg', THUMBS/f'{item.key}.png'
        preview_valid = (old.get('renderer_sha256') == fingerprint and saved.get('recipe') == expected
                         and file_matches(preview, saved.get('files', {})))
        thumbnail_valid = (preview_valid and saved.get('thumbnail_recipe', old.get('thumbnail_recipe')) == presentation
                           and file_matches(thumbnail, saved.get('files', {})))
        if preview_valid and thumbnail_valid:
            records[item.key] = {**saved, 'thumbnail_recipe': presentation}
            continue
        stale.append(item.key)
        if args.check:
            continue
        if not preview_valid:
            render_root = (ROOT/'output/gallery-renders').resolve()
            render_root.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=item.key+'-', dir=render_root) as temporary:
                Path(temporary).resolve().relative_to(render_root)  # bound automatic cleanup to our workspace
                command = [sys.executable, str(SCRIPTS/'frame_photo.py'), str(ROOT/SOURCES[item.source]),
                           '--share', '--metadata', 'strip', '--out-dir', temporary]
                for name, value in item.settings().items():
                    flag = '--'+name.replace('_', '-')
                    if value is True:
                        command.append(flag)
                    elif name == 'signature':
                        command += [flag, str(ROOT/value)]
                    else:
                        command.append(f'{flag}={value}')
                process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
                row = json.loads(process.stdout)['results'][0]
                if row['status'] != 'ok':
                    raise ValueError(row)
                with Image.open(row['outputs'][1]) as source:
                    save_preview(source.convert('RGB'), preview, RECIPE['preview_edge'])
            print('Rendered '+item.key, flush=True)
        with Image.open(preview) as image:
            save_thumbnail(image, thumbnail, presentation)
        records[item.key] = {'recipe': expected, 'thumbnail_recipe': presentation, 'files': {
            path.relative_to(ROOT).as_posix(): digest(path) for path in (preview, thumbnail)}}
        print('Updated thumbnail '+item.key, flush=True)
    source_records = {}
    for name in ('landscape', 'portrait'):
        path = THUMBS/f'source-{name}.png'
        expected = {'source_sha256': digest(ROOT/SOURCES[name]), 'recipe': RECIPE,
                    'thumbnail_recipe': THUMBNAIL}
        saved = old.get('sources', {}).get(name, {})
        if not (saved.get('recipe') == expected and path.is_file() and saved.get('sha256') == digest(path)):
            stale.append('source-'+name)
            if not args.check:
                from photoframer.io import load_photo
                from photoframer.color import convert_profile
                photo, profile, _ = load_photo(ROOT/SOURCES[name])
                save_thumbnail(convert_profile(photo, profile, SRGB), path, thumbnail_recipe())
        if path.exists():
            source_records[name] = {'recipe': expected, 'sha256': digest(path)}
    if args.check:
        if stale or set(old.get('examples', {})) != {item.key for item in examples()}:
            print('Stale gallery assets: '+', '.join(stale)+'. Run python tools/gallery.py')
            return 1
        print(f'Gallery is up to date: {len(records)} examples in eight style groups.')
        return 0
    MANIFEST.write_text(json.dumps({'renderer_version': VERSION, 'pillow': PILLOW_VERSION,
                                   'renderer_sha256': fingerprint, 'recipe': RECIPE,
                                   'thumbnail_recipe': THUMBNAIL,
                                   'sources': source_records, 'examples': records},
                                  ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Gallery ready: {len(records)} examples. Run python tools/gen_docs.py.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
