"""Output EXIF, camera display names and typed capture details."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from photoframer import Settings, metadata
from photoframer.components import spec_band
from .support import RENDERER, sony_exif


class MetadataLayer(unittest.TestCase):
    """v0.9: output EXIF, camera display names and user-supplied capture details."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, paths, *flags):
        process = subprocess.run(
            [sys.executable, str(RENDERER), *map(str, paths), '--out-dir', str(self.root / 'out'), *flags],
            capture_output=True, text=True, encoding='utf-8')
        rows = json.loads(process.stdout)['results'] if process.stdout.strip() else None
        return process, rows

    def sony_jpeg(self, name='sony.jpg', orientation=6):
        path = self.root / name
        Image.new('RGB', (300, 200), (120, 60, 30)).save(path, quality=95, exif=sony_exif(orientation))
        return path

    def test_keep_copies_exif_with_gps_and_cleans_it(self):
        path = self.sony_jpeg()
        process, rows = self.run_cli([path], '--style', 'H', '--share')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(any('Source EXIF copied' in note for note in rows[0]['notes']))
        self.assertFalse(any('GPS' in note or 'location' in note.lower() for note in rows[0]['notes']))
        for output in rows[0]['outputs']:
            with self.subTest(output=Path(output).name), Image.open(output) as im:
                im.load()
                exif = im.getexif()
                self.assertEqual(exif[274], 1)
                self.assertEqual((exif[271], exif[272]), ('SONY', 'ILCE-7C'))
                sub = exif.get_ifd(0x8769)
                self.assertNotIn(0x927C, sub)
                self.assertEqual((sub[0xA002], sub[0xA003]), im.size)
                self.assertEqual(sub[34855], 250)
                gps = exif.get_ifd(0x8825)
                self.assertEqual((gps[1], gps[3]), ('N', 'E'))
                self.assertEqual(tuple(map(float, gps[2])), (21.0, 1.0, 30.0))
                self.assertNotIn(0xA005, sub)
                self.assertFalse(im.getxmp())
        with Image.open(rows[0]['outputs'][1]) as shared:
            self.assertEqual(shared.size, (1080, 1350))

    def test_strip_and_previews_write_no_exif(self):
        path = self.sony_jpeg()
        process, rows = self.run_cli([path], '--style', 'C', '--share', '--metadata', 'strip')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse(any('Source EXIF' in note for note in rows[0]['notes']))
        for output in rows[0]['outputs']:
            with Image.open(output) as im:
                self.assertFalse(im.getexif())
        process, rows = self.run_cli([path], '--preview')
        self.assertEqual(process.returncode, 0, process.stderr)
        with Image.open(rows[0]['outputs'][0]) as im:
            self.assertFalse(im.getexif())
        process, rows = self.run_cli([path], '--metadata', 'everything')
        self.assertEqual(process.returncode, 2)

    def test_exif_without_orientation_and_unrotated_dimensions(self):
        exif = metadata.exif_for_output(sony_exif(orientation=None), (640, 480))
        im = Image.new('RGB', (640, 480))
        buffer = io.BytesIO()
        im.save(buffer, 'PNG', exif=exif)
        with Image.open(buffer) as saved:
            kept = saved.getexif()
            self.assertNotIn(274, kept)
            self.assertEqual(kept.get_ifd(0x8769)[0xA002], 640)
        self.assertIsNone(metadata.exif_for_output(Image.Exif(), (10, 10)))
        self.assertIsNone(metadata.exif_for_output(None, (10, 10)))

    def test_camera_display_names(self):
        meta = {'make': 'SONY', 'model': 'ILCE-7C', 'lens': 'FE 35mm F1.8'}
        self.assertEqual(metadata.format_specs(meta, with_brand=False)[0], 'α7C | FE 35mm F1.8')
        self.assertEqual(metadata.format_specs(meta)[0], 'Sony α7C | FE 35mm F1.8')
        self.assertEqual(metadata.format_specs(meta, raw_model=True)[0], 'ILCE-7C | FE 35mm F1.8')
        self.assertEqual(metadata.gear_name({'make': 'Panasonic', 'model': 'DC-S1RM2'}), 'LUMIX S1RII')
        self.assertEqual(metadata.gear_name({'make': 'NIKON CORPORATION', 'model': 'NIKON Z 6_2'},
                                            with_brand=False), 'Z6II')
        # Unlisted models keep their EXIF text (plus the existing Mark spacing).
        self.assertEqual(metadata.gear_name({'make': 'SONY', 'model': 'ZV-E10'}), 'ZV-E10')
        self.assertEqual(metadata.gear_name({'make': 'OLYMPUS', 'model': 'E-M10MarkIV'}), 'E-M10 Mark IV')
        self.assertEqual(metadata.gear_name({'make': 'Canon', 'model': 'ILCE-7C'}), 'ILCE-7C')

    def test_c_drops_the_brand_already_shown_by_its_mark(self):
        cases = (({'make': 'Canon', 'model': 'Canon EOS R5'}, 'EOS R5'),
                 ({'make': 'NIKON CORPORATION', 'model': 'NIKON D850'}, 'D850'),
                 ({'make': 'LEICA CAMERA AG', 'model': 'LEICA Q2'}, 'Q2'),
                 ({'make': 'Canon', 'model': 'Canon'}, 'Canon'),
                 ({'make': 'SIGMA', 'model': 'fp L'}, 'fp L'),
                 ({'make': 'RICOH IMAGING COMPANY, LTD.', 'model': 'PENTAX K-3 Mark III'},
                  'PENTAX K-3 Mark III'),
                 ({'make': 'OLYMPUS CORPORATION', 'model': 'E-M10MarkIV'}, 'E-M10 Mark IV'))
        for meta, short in cases:
            with self.subTest(meta=meta):
                self.assertEqual(metadata.gear_name(meta, with_brand=False), short)
                full = metadata.gear_name(meta)
                self.assertEqual(full, metadata.display_model(meta['model']))
                self.assertEqual(metadata.gear_name(meta, with_brand=False, raw_model=True), full)
        exif = Image.Exif()
        exif[271], exif[272] = 'Canon', 'Canon EOS R5'
        path = self.root / 'canon.png'
        Image.new('RGB', (900, 600), 'gray').save(path, exif=exif)
        process, rows = self.run_cli([path], '--style', 'C')
        self.assertIn("Model display formatted: 'Canon EOS R5' -> 'EOS R5'.", rows[0]['notes'])
        process, rows = self.run_cli([path], '--style', 'D', '--right-text', 'Hà Nội')
        self.assertFalse(any(n.startswith('Model display') for n in rows[0]['notes']))

    def test_camera_list_is_well_formed(self):
        with open(metadata.CAMERAS_FILE, encoding='utf-8') as stream:
            brands = json.load(stream)['brands']
        for slug, models in brands.items():
            self.assertTrue((spec_band.LOGO_DIR / f'{slug}.png').is_file(), slug)
            for model, entry in models.items():
                with self.subTest(model=model):
                    self.assertEqual(set(entry), {'name', 'short'})
                    self.assertTrue(entry['name'].endswith(entry['short']))
                    self.assertEqual(metadata.brand_slug({'model': model}) or slug, slug)

    def test_display_name_notes_per_style(self):
        path = self.sony_jpeg()
        expected = {('C',): "'ILCE-7C' -> 'α7C'.", ('D', '--right-text', 'Hà Nội'): "'ILCE-7C' -> 'Sony α7C'.",
                    ('C', '--raw-model'): None}
        for flags, note in expected.items():
            with self.subTest(flags=flags):
                process, rows = self.run_cli([path], '--style', *flags)
                self.assertEqual(process.returncode, 0, process.stderr)
                notes = [n for n in rows[0]['notes'] if n.startswith('Model display')]
                self.assertEqual(notes, [f'Model display formatted: {note}'] if note else [])
        process, rows = self.run_cli([path], '--preview', '--right-text', 'Hà Nội')
        self.assertIn("Model display formatted: 'ILCE-7C' -> 'α7C' (C), 'Sony α7C' (D).", rows[0]['notes'])

    def test_user_supplied_capture_details(self):
        scan = self.root / 'film scan.png'
        Image.new('RGB', (900, 600), (90, 90, 90)).save(scan)
        flags = ('--camera', 'Pentax 67', '--lens', 'SMC 105mm F2.4', '--iso', '400',
                 '--aperture', 'f/2.4', '--shutter', '1/125', '--focal', '105mm')
        process, rows = self.run_cli([scan], '--style', 'C', *flags)
        self.assertEqual(process.returncode, 0, process.stderr)
        notes = rows[0]['notes']
        self.assertIn('Capture details supplied by the user: --camera, --lens, --iso, '
                      '--aperture, --shutter, --focal.', notes)
        self.assertFalse(any('No capture metadata' in n or 'Brand' in n or 'Spec caption' in n
                             for n in notes), notes)
        with Image.open(rows[0]['outputs'][0]) as im:
            band = im.crop((0, 600 + 32, 450, im.height)).convert('L')
            self.assertLess(band.getextrema()[0], 128)
        settings = Settings('C', camera='Pentax 67', lens='SMC 105mm F2.4', iso=400.0,
                            aperture=2.4, shutter=1/125, focal=105.0)
        merged, _ = metadata.apply_user_specs({}, {}, settings)
        self.assertEqual(metadata.format_specs(merged),
                         ('Pentax 67 | SMC 105mm F2.4', 'ISO 400  f/2.4  1/125s  105mm'))
        # User values win field by field; the brand mark still follows the file.
        meta = {'make': 'SONY', 'model': 'ILCE-7C', 'iso': 250.0, 'fnumber': 1.8,
                'exposure': 1/125, 'focal': 35.0}
        merged, origins = metadata.apply_user_specs(meta, {'iso': 'EXIF', 'model': 'EXIF'},
                                                    Settings('C', iso=800.0, camera='α7C (IR)'))
        self.assertEqual(metadata.format_specs(merged)[1], 'ISO 800  f/1.8  1/125s  35mm')
        self.assertEqual(metadata.format_specs(merged)[0], 'α7C (IR)')
        self.assertEqual(origins, {'iso': 'user', 'model': 'user'})
        self.assertEqual(metadata.brand_slug(meta), 'sony')
        process, rows = self.run_cli([self.sony_jpeg()], '--style', 'D', '--right-text', 'x', '--iso', '800')
        self.assertIn('Spec caption from EXIF metadata.', rows[0]['notes'])
        self.assertIn('Capture details supplied by the user: --iso.', rows[0]['notes'])

    def test_invalid_capture_details_and_styles(self):
        scan = self.root / 'scan.png'
        Image.new('RGB', (400, 300)).save(scan)
        for flags in (('--iso', 'abc'), ('--iso', '0'), ('--aperture', 'f/'), ('--shutter', '1/0'),
                      ('--focal', '-5'), ('--camera', ''), ('--lens', 'a\nb'), ('--camera', 'x' * 201)):
            with self.subTest(flags=flags):
                process, rows = self.run_cli([scan], '--style', 'C', *flags)
                self.assertEqual(process.returncode, 2)
                self.assertIsNone(rows)
        for flag in (('--iso', '400'), ('--camera', 'Pentax 67'), ('--raw-model',)):
            with self.subTest(flag=flag):
                process, rows = self.run_cli([scan], '--style', 'A', *flag)
                self.assertEqual(process.returncode, 1)
                self.assertIn('only with style C or D', rows[0]['error'])
