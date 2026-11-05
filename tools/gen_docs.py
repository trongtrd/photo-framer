#!/usr/bin/env python3
"""Regenerate the style tables in the docs from the renderer's style registry.

Generated blocks sit between marker comments; everything else is hand-written:

    <!-- generated:NAME -->
    ...
    <!-- /generated:NAME -->

    python tools/gen_docs.py          # rewrite the blocks
    python tools/gen_docs.py --check  # exit 1 if any block is stale (CI)
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'skills' / 'photo-framer' / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from photoframer.registry import STYLES  # noqa: E402
from photoframer.settings import GLOBAL_FLAGS, OPTIONS  # noqa: E402
from gallery import gallery_block  # noqa: E402

README = ROOT / 'README.md'
MENUS = ROOT / 'skills' / 'photo-framer' / 'references' / 'menus.md'
BLOCK = re.compile(r'(<!-- generated:(?P<name>[\w-]+) -->\n)(?P<body>.*?)(<!-- /generated:(?P=name) -->)',
                   re.S)
LANGUAGES = {'en': (0, 'Setting', 'default'), 'vi': (1, 'Tùy chỉnh', 'mặc định')}


def menu_table(style, language):
    index, header, default_word = LANGUAGES[language]
    lines = [f'| {header} | 1 | 2 | 3 |', '|---|---|---|---|']
    for row, default in zip(style.rows, style.default_choices):
        cells = [f'**{option[index]} — {default_word}**' if number == default else option[index]
                 for number, option in enumerate(row.options, 1)]
        lines.append(f'| {row.label[index]} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def readme_styles():
    lines = ['| Style / Phong cách | Look / Hình thức | Default / Mặc định |',
             '| --- | --- | :---: |']
    for code, style in STYLES.items():
        lines.append(f'| [**{style.readme_title}**](#style-{code.lower()}) | '
                     f'{style.look[0]}<br>{style.look[1]} | `{style.default}` |')
    return '\n'.join(lines)


def option_matrix():
    """Which named flags each style accepts (✓) or requires (required)."""
    codes = list(STYLES)
    lines = ['| Flag | ' + ' | '.join(codes) + ' |', '|---|' + ':---:|' * len(codes)]
    for option in OPTIONS:
        cells = []
        for style in STYLES.values():
            if option.field in style.requires:
                cells.append('required')
            elif option.field in style.accepts:
                cells.append('✓')
            else:
                cells.append('—')
        lines.append(f'| `{option.flag}` | ' + ' | '.join(cells) + ' |')
    for flag in GLOBAL_FLAGS:
        lines.append(f'| `{flag}` | ' + ' | '.join('✓' for _ in codes) + ' |')
    return '\n'.join(lines)


def blocks():
    generated = {'styles': readme_styles(), 'option-matrix': option_matrix(), 'gallery': gallery_block()}
    for code, style in STYLES.items():
        for language in LANGUAGES:
            generated[f'menu-{language}-{code}'] = menu_table(style, language)
    return generated


def regenerate(text, generated, seen):
    def replace(match):
        name = match['name']
        if name not in generated:
            raise SystemExit(f'Unknown generated block: {name}')
        seen.add(name)
        return match[1] + generated[name] + '\n' + match[4]
    return BLOCK.sub(replace, text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='report stale blocks, write nothing')
    args = parser.parse_args(argv)
    generated, seen, stale = blocks(), set(), []
    for path in (README, MENUS):
        text = path.read_text(encoding='utf-8')
        updated = regenerate(text, generated, seen)
        if updated != text:
            stale.append(path.relative_to(ROOT).as_posix())
            if not args.check:
                path.write_text(updated, encoding='utf-8', newline='\n')
    missing = sorted(set(generated) - seen)
    if missing:
        print('Missing generated blocks: ' + ', '.join(missing))
        return 1
    if args.check and stale:
        print('Stale generated docs: ' + ', '.join(stale) + '. Run python tools/gen_docs.py')
        return 1
    print(('Updated: ' + ', '.join(stale)) if stale and not args.check else 'Docs are up to date.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
