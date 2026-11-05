"""The style registry and the named-option matrix."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

import photoframer
from photoframer import Settings, text
from photoframer.registry import STYLES
from photoframer.settings import OPTIONS
from .support import RENDERER, render, signature_png


class RegistryAndSettings(unittest.TestCase):
    """The style registry and the named-option matrix that the CLI and docs use."""

    def test_registry_order_menus_and_defaults(self):
        self.assertEqual(''.join(STYLES), 'ABCDEFGH')
        fields = {option.field for option in OPTIONS}
        for code, style in STYLES.items():
            with self.subTest(style=code):
                self.assertEqual(style.code, code)
                self.assertEqual(len(style.rows), 3)
                self.assertTrue(all(len(row.options) == 3 for row in style.rows))
                self.assertEqual(Settings(code).choices, style.default_choices)
                self.assertLessEqual(style.accepts, fields)

    def test_settings_parse_and_reject_codes(self):
        self.assertEqual(Settings('B', '1-3-1').choices, (1, 3, 1))
        self.assertEqual(Settings('H').choices, (1, 1, 1))
        for code in ('4-1-1', '1-1', '1-1-1-1', 'a-b-c', '0-1-1'):
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, 'three numbers'):
                Settings('A', code)
        with self.assertRaisesRegex(ValueError, 'A, B, C, D, E, F, G or H'):
            Settings('Z')

    def test_option_matrix_matches_enforcement(self):
        """Every style rejects exactly the named options it does not accept."""
        photo = Image.new('RGB', (900, 600), 'red')
        font = str(text.FONTS_DIR / 'Inter-Regular.ttf')
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        signature = Path(temp.name) / 'signature.png'
        signature_png(signature)
        values = {'left_text': 'x', 'right_text': 'x', 'frame_color': '#ad896c',
                  'caption': 'x', 'font_path': font, 'camera': 'Pentax 67', 'lens': '105mm',
                  'iso': 400.0, 'aperture': 2.4, 'shutter': 1/125, 'focal': 105.0,
                  'raw_model': True, 'capture_sidecar': True,
                  'ratio': '9:16', 'background': 'blur', 'blur_tone': 'light',
                  'title': 'Hà Nội', 'subtitle': 'Mùa thu 2022', 'signature': signature,
                  'signature_position': 'bottom-left', 'signature_width': .1, 'signature_opacity': .8}
        required = {'D': {'right_text': 'Berlin'}, 'F': {'left_text': '', 'right_text': ''}}
        for code, style in STYLES.items():
            for option in OPTIONS:
                with self.subTest(style=code, option=option.flag):
                    options = dict(required.get(code, {}))
                    options[option.field] = values[option.field]
                    if option.field == 'caption':
                        options['font_path'] = font
                    if option.field == 'blur_tone':
                        options['background'] = 'blur'
                    if option.field == 'subtitle':
                        options['title'] = 'Hà Nội'
                    if option.field.startswith('signature_'):
                        options['signature'] = signature
                    if option.field in style.accepts:
                        render(photo, code, **options)
                    else:
                        with self.assertRaises(ValueError):
                            render(photo, code, **options)

    def test_required_options_are_enforced(self):
        photo = Image.new('RGB', (900, 600), 'red')
        full = {'left_text': 'Berlin', 'right_text': 'October'}
        for code, style in STYLES.items():
            self.assertLessEqual(style.requires, style.accepts)
            for field in style.requires:
                with self.subTest(style=code, missing=field):
                    options = {key: full[key] for key in style.requires if key != field}
                    with self.assertRaisesRegex(ValueError, 'requires'):
                        render(photo, code, **options)

    def test_cli_version(self):
        process = subprocess.run([sys.executable, str(RENDERER), '--version'],
                                 capture_output=True, text=True)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout.strip(), f'Photo Framer {photoframer.VERSION}')
