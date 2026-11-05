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
                                     f'{row.label[0]}: {option[0]}', '-'.join(map(str, choices))))
    return examples


def gallery_rows():
    """Eight style groups; large groups have two or three independent rows."""
    result = {}
    for code in 'ABCDEFG':
        extra = []
        if code in 'ABCDEG':
            extra.append(Example(f'{code.lower()}-caption', code, 'Caption',
                                  options={'caption': RIGHT_TEXT}, hint='--caption'))
        if code in 'ABG':
            extra.append(Example(f'{code.lower()}-label', code, 'Gallery label', source='portrait',
                                  options={'title': 'Praha', 'subtitle': 'Prague · Czech Republic'},
                                  hint='--title / --subtitle'))
        if code in 'ABEG':
            extra.append(Example(f'{code.lower()}-signature', code, 'Your PNG signature',
                                  options={'signature': SIGNATURE, 'signature_width': .12},
                                  hint='--signature'))
        if code in 'CD':
            extra += [Example(f'{code.lower()}-raw-model', code, 'Raw camera code',
                               options={'raw_model': True}, hint='--raw-model'),
                      Example(f'{code.lower()}-sidecar', code, 'Typed details · synthetic chart',
                               source='scan', options={'capture_sidecar': True}, hint='--capture-sidecar')]
        if code == 'E':
            extra.insert(0, Example('e-fixed-color', code, 'One shared color',
                                    options={'frame_color': '#ad896c'}, hint='--frame-color'))
        if code == 'F':
            for name, left, right in (('blank', '', ''), ('left', 'Berlin, Germany', ''),
                                       ('right', '', 'October 2022')):
                extra.append(Example(f'f-text-{name}', code,
                                      {'blank': 'No corner text', 'left': 'Left text only',
                                       'right': 'Right text only'}[name],
                                      options={'left_text': left, 'right_text': right},
                                      hint='--left-text / --right-text'))
        result[code] = [('Preset settings', preset_examples(code)), ('Text and input options', extra)]

    canvas = [Example('h-default', 'H', '4:5 · default')]
    for ratio in ('1:1', 'original', '3:4', '9:16', '16:9'):
        canvas.append(Example(f'h-ratio-{ratio.replace(":", "x")}', 'H',
                               'Thin border' if ratio == 'original' else ratio,
                               options={'ratio': ratio}, hint=f'--ratio {ratio}'))
    blur = [Example(f'h-blur-{ratio.replace(":", "x")}', 'H',
                     ('Thin border' if ratio == 'original' else ratio) + ' · blur',
                     options={'ratio': ratio, 'background': 'blur'}, hint=f'--ratio {ratio}')
            for ratio in ('16:9', '1:1', '9:16', '4:5', '3:4', 'original')]
    for tone in ('neutral', 'light'):
        blur.append(Example(f'h-blur-tone-{tone}', 'H', f'16:9 · {tone} blur',
                             options={'ratio': '16:9', 'background': 'blur', 'blur_tone': tone},
                             hint=f'--blur-tone {tone}'))
    details = [Example('h-gray', 'H', 'Warm gray mat', '1-2-1'),
               Example('h-ivory', 'H', 'Ivory mat', '1-3-1'),
               Example('h-no-keyline', 'H', 'No keyline', '1-1-2'),
               Example('h-thick-keyline', 'H', 'Thick keyline', '1-1-3'),
               Example('h-caption', 'H', 'Caption', options={'caption': RIGHT_TEXT}, hint='--caption'),
               Example('h-portrait', 'H', 'Portrait photo · 4:5', source='portrait'),
               Example('h-label', 'H', 'Gallery label · 1:1', source='portrait',
                       options={'ratio': '1:1', 'title': 'Praha', 'subtitle': 'Prague · Czech Republic'},
                       hint='--title / --subtitle')]
    result['H'] = [('Canvas ratios · plain background', canvas),
                   ('Blurred backgrounds · dark by default', blur),
                   ('Mats, keylines and text', details)]
    return result


def examples():
    return [item for rows in gallery_rows().values() for _, row in rows for item in row]


def gallery_block():
    lines = ['Each style has its own gallery. Preset examples change one setting from the default; '
             'text, signatures and other named options have a separate row. H has three rows. '
             'Scroll a wide row horizontally and click any preview to enlarge it.', '',
             'These are reduced JPEG previews, not full-resolution PNGs. The originals stay untouched. '
             'The sample text is supplied wording, never inferred metadata.', '',
             '| Original landscape | Original portrait |', '| :---: | :---: |']
    cells = [f'<a href="{SOURCES[source]}"><img src="docs/images/gallery/thumbs/source-{source}.jpg" '
             f'height="140" alt="Original {source} photograph"></a>'
             for source in ('landscape', 'portrait')]
    lines += ['| ' + ' | '.join(cells) + ' |', '']
    for code, rows in gallery_rows().items():
        lines += [f'<a id="style-{code.lower()}"></a>', '', f'### {STYLES[code].readme_title}', '']
        if code == 'H':
            lines += ['Plain or blurred backgrounds work with every ratio. '
                       '`16:9` is the landscape canvas; `1:1` is square. '
                       'Neither crops or scales the photo. H takes no signature.', '']
        for heading, row in rows:
            lines += [f'**{heading}**', '']
            labels = [f'{html.escape(item.label)}<br><code>'
                      f'{html.escape(item.hint or item.code or STYLES[code].default)}</code>'
                      for item in row]
            pictures = [f'<a href="docs/images/gallery/{item.key}.jpg">'
                        f'<img src="docs/images/gallery/thumbs/{item.key}.jpg" width="240" '
                        f'alt="{html.escape(code + ": " + item.label, quote=True)}"></a>' for item in row]
            lines += ['| ' + ' | '.join(labels) + ' |', '| ' + ' | '.join(':---:' for _ in row) + ' |',
                       '| ' + ' | '.join(pictures) + ' |', '']
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
        saved = old.get('examples', {}).get(item.key, {})
        paths = [ASSETS/f'{item.key}.jpg', THUMBS/f'{item.key}.jpg']
        valid = (old.get('renderer_sha256') == fingerprint and saved.get('recipe') == expected
                 and all(path.is_file() and saved.get('files', {}).get(path.relative_to(ROOT).as_posix())
                         == digest(path) for path in paths))
        if valid:
            records[item.key] = saved
            continue
        stale.append(item.key)
        if args.check:
            continue
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
                image = source.convert('RGB')
                save_preview(image, paths[0], RECIPE['preview_edge'])
                save_preview(image, paths[1], RECIPE['thumb_edge'])
        records[item.key] = {'recipe': expected, 'files': {
            path.relative_to(ROOT).as_posix(): digest(path) for path in paths}}
        print('Rendered '+item.key, flush=True)
    source_records = {}
    for name in ('landscape', 'portrait'):
        path = THUMBS/f'source-{name}.jpg'
        expected = {'source_sha256': digest(ROOT/SOURCES[name]), 'recipe': RECIPE}
        saved = old.get('sources', {}).get(name, {})
        if not (saved.get('recipe') == expected and path.is_file() and saved.get('sha256') == digest(path)):
            stale.append('source-'+name)
            if not args.check:
                from photoframer.io import load_photo
                from photoframer.color import convert_profile
                photo, profile, _ = load_photo(ROOT/SOURCES[name])
                save_preview(convert_profile(photo, profile, SRGB), path, RECIPE['thumb_edge'])
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
                                   'sources': source_records, 'examples': records},
                                  ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Gallery ready: {len(records)} examples. Run python tools/gen_docs.py.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
