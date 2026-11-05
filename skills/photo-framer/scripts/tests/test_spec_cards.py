"""Styles C and D: capture details, brand marks and custom text."""
import unittest
import unittest.mock

from PIL import Image, ImageFont

from photoframer import metadata, text
from photoframer.components import spec_band
from .support import FramerCase, render, save_with_xmp, xmp_packet


class SpecCards(FramerCase):
    def test_style_c_xmp_specs_and_logo(self):
        path = self.root / 'spec xmp.png'
        save_with_xmp(Image.new('RGB', (300, 200), 'red'), path, xmp_packet())
        process, rows = self.cli([path], '--style', 'C')
        self.assertEqual(process.returncode, 0, process.stderr)
        row = rows[0]
        self.assertEqual(self.region(row, (300, 200), 'C').tobytes(),
                         Image.new('RGB', (300, 200), 'red').tobytes())
        self.assertTrue(self.has_ink(self.band_crop(row, 0, 150, (300, 200))),
                        'spec text missing from caption band')
        self.assertTrue(self.has_ink(self.band_crop(row, 225, 300, (300, 200))),
                        'brand logo missing from caption band')
        self.assertTrue(any('XMP' in note for note in row['notes']), row['notes'])
        self.assertTrue(any('om-system' in note for note in row['notes']), row['notes'])
        self.assertTrue(any("Model display formatted: 'E-M10MarkIV' -> 'E-M10 Mark IV'"
                            in note for note in row['notes']), row['notes'])

    def test_style_c_exif_specs(self):
        path = self.root / 'spec exif.png'
        photo = Image.new('RGB', (220, 160), (1, 160, 99))
        exif = Image.Exif()
        exif[271] = 'Panasonic'
        exif[272] = 'DC-S1RM2'
        sub = exif.get_ifd(0x8769)
        sub[42036] = '28-105mm F2.8 DG DN | Art 024'
        sub[34855] = 250
        sub[33437] = (28, 10)
        sub[33434] = (1, 125)
        sub[37386] = (105, 1)
        photo.save(path, exif=exif)  # PNG carries an eXIf chunk; pixels stay exact.
        process, rows = self.cli([path], '--style', 'C')
        self.assertEqual(process.returncode, 0, process.stderr)
        row = rows[0]
        self.assertEqual(self.region(row, (220, 160), 'C').tobytes(), photo.tobytes())
        self.assertTrue(self.has_ink(self.band_crop(row, 0, 110, (220, 160))))
        self.assertTrue(any('EXIF' in note for note in row['notes']), row['notes'])
        self.assertTrue(any('lumix' in note for note in row['notes']), row['notes'])

    def test_style_c_no_metadata_leaves_band_blank(self):
        path = self.root / 'no meta.png'
        Image.new('RGB', (200, 150), 'blue').save(path)
        process, rows = self.cli([path], '--style', 'C')
        self.assertEqual(process.returncode, 0, process.stderr)
        row = rows[0]
        self.assertEqual(self.region(row, (200, 150), 'C').tobytes(),
                         Image.new('RGB', (200, 150), 'blue').tobytes())
        self.assertTrue(self.is_blank(self.band_crop(row, 0, 200, (200, 150))))
        self.assertTrue(any('No capture metadata' in n for n in row['notes']), row['notes'])

    def test_style_c_text_mode_options(self):
        path = self.root / 'text modes.png'
        save_with_xmp(Image.new('RGB', (300, 200), 'red'), path, xmp_packet())
        for mode, expect_text in (('2-1-2', True), ('2-1-3', False)):
            with self.subTest(mode=mode):
                process, rows = self.cli([path], '--style', 'C', '--choices', mode)
                self.assertEqual(process.returncode, 0, process.stderr)
                row = rows[0]
                text_zone = self.band_crop(row, 0, 130, (300, 200))
                if expect_text:
                    self.assertTrue(self.has_ink(text_zone), 'gear line missing')
                else:
                    self.assertTrue(self.is_blank(text_zone))
                self.assertTrue(self.has_ink(self.band_crop(row, 230, 300, (300, 200))),
                                'brand logo must persist in every text mode')

    def test_style_c_wordmark_fallback(self):
        path = self.root / 'sigma.png'
        save_with_xmp(Image.new('RGB', (240, 180), 'green'), path,
                      xmp_packet(**{'tiff:Make': 'SIGMA', 'tiff:Model': 'fp L'}))
        process, rows = self.cli([path], '--style', 'C')
        self.assertEqual(process.returncode, 0, process.stderr)
        row = rows[0]
        self.assertTrue(self.has_ink(self.band_crop(row, 168, 240, (240, 180))),
                        'brand wordmark missing')
        self.assertTrue(any('wordmark' in note for note in row['notes']), row['notes'])

    def test_bundled_spec_fonts_and_fallback(self):
        regular = ImageFont.truetype(str(text.FONTS_DIR / 'Inter-Regular.ttf'), 24)
        semibold = ImageFont.truetype(str(text.FONTS_DIR / 'Inter-SemiBold.ttf'), 24)
        self.assertEqual(regular.getname(), ('Inter', 'Regular'))
        self.assertEqual(semibold.getname(), ('Inter', 'SemiBold'))
        face, emphasis, stroke = text.specs_fonts(24)
        self.assertEqual(face.getname(), ('Inter', 'Regular'))
        self.assertEqual(emphasis.getname(), ('Inter', 'SemiBold'))
        self.assertEqual(stroke, 0)
        missing = text.FONTS_DIR.with_name('fonts-missing')
        with unittest.mock.patch.object(text, 'FONTS_DIR', missing):
            face, emphasis, stroke = text.specs_fonts(24)
            self.assertIs(face, emphasis)
            self.assertGreater(stroke, 0)

    def test_style_d_custom_text_and_capture_details(self):
        path = self.root / 'custom spec.png'
        save_with_xmp(Image.new('RGB', (900, 600), 'red'), path, xmp_packet())
        text = 'Berlin, Germany | October 2022'
        process, rows = self.cli([path], '--style', 'D', '--right-text', text, '--share')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(self.region(rows[0], (900, 600), 'D').tobytes(),
                         Image.new('RGB', (900, 600), 'red').tobytes())
        self.assertTrue(self.has_ink(self.band_crop(rows[0], 0, 400, (900, 600))))
        self.assertTrue(self.has_ink(self.band_crop(rows[0], 500, 900, (900, 600))))
        self.assertTrue(any('XMP' in note for note in rows[0]['notes']))
        self.assertTrue(any('user text replaces' in note for note in rows[0]['notes']))
        self.assertFalse(any('Brand mark:' in note for note in rows[0]['notes']))
        with Image.open(rows[0]['outputs'][0]) as im:
            self.assertFalse(im.getexif())
            self.assertFalse(im.getxmp())
        with Image.open(rows[0]['outputs'][1]) as im:
            im.load()
            self.assertLessEqual(max(im.size), 2048)

    def test_style_d_uses_gear_font_and_never_loads_logo(self):
        photo = Image.new('RGB', (1200, 800), 'red')
        # Identical strings must produce identical glyphs on both sides.
        for font_path in (None, text.FONTS_DIR / 'Inter-Regular.ttf'):
            with self.subTest(font_path=font_path), unittest.mock.patch.object(
                    spec_band, 'load_logo', side_effect=AssertionError('D must not load logos')):
                result, _ = render(
                    photo, 'D', meta={'make': 'SONY', 'model': 'ILCE-7C'},
                    right_text='Sony α7C', font_path=font_path)
            left = result.crop((0, 828, 600, result.height)).convert('L')
            right = result.crop((600, 828, result.width, result.height)).convert('L')
            # Extract ink independently, comparing shape, size, weight and color.
            left_box = left.point(lambda value: 255 if value < 200 else 0).getbbox()
            right_box = right.point(lambda value: 255 if value < 200 else 0).getbbox()
            self.assertIsNotNone(left_box)
            self.assertIsNotNone(right_box)
            self.assertEqual(left.crop(left_box).size, right.crop(right_box).size)
            self.assertEqual(left.crop(left_box).tobytes(), right.crop(right_box).tobytes())

    def test_style_d_vietnamese_without_metadata_and_spec_modes(self):
        path = self.root / 'custom vietnamese.png'
        save_with_xmp(Image.new('RGB', (1200, 800), 'blue'), path, xmp_packet())
        text = 'Hồ Hoàn Kiếm | Tháng 10, 2022'
        for mode in ('2-1-1', '2-1-2', '2-1-3'):
            with self.subTest(mode=mode):
                process, rows = self.cli([path], '--style', 'D', '--right-text', text,
                                         '--choices', mode)
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertTrue(self.has_ink(self.band_crop(rows[0], 600, 1200, (1200, 800))))
                left = self.band_crop(rows[0], 0, 500, (1200, 800))
                self.assertEqual(self.has_ink(left), mode != '2-1-3')
        plain = self.root / 'no metadata.png'
        Image.new('RGB', (1200, 800), 'blue').save(plain)
        process, rows = self.cli([plain], '--style', 'D', '--right-text', text)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(self.is_blank(self.band_crop(rows[0], 0, 500, (1200, 800))))
        self.assertTrue(self.has_ink(self.band_crop(rows[0], 600, 1200, (1200, 800))))

    def test_style_d_rejects_missing_invalid_and_overlapping_text(self):
        path = self.root / 'text validation.png'
        save_with_xmp(Image.new('RGB', (900, 600), 'green'), path, xmp_packet())
        for text in (None, '', '   ', 'one\ntwo', 'one\rtwo', 'one\ttwo', 'x'*201, 'W'*200):
            with self.subTest(text=text):
                flags = ('--right-text', text) if text is not None else ()
                process, rows = self.cli([path], '--style', 'D', *flags)
                self.assertEqual(process.returncode, 1)
                self.assertEqual(rows[0]['status'], 'error')
                self.assertNotIn('outputs', rows[0])
        self.assertFalse((self.root / 'output').exists())
        for style in 'ABC':
            process, rows = self.cli([path], '--style', style, '--right-text', 'Berlin')
            self.assertEqual(process.returncode, 1)
            self.assertIn('only with style D', rows[0]['error'])

    def test_style_d_fit_errors_continue_batch_and_preview_needs_supplied_text(self):
        small, large = self.root / 'small.png', self.root / 'large.png'
        Image.new('RGB', (40, 32), 'red').save(small)
        Image.new('RGB', (900, 600), 'red').save(large)
        text = 'Berlin, Germany | October 2022'
        process, rows = self.cli([small, large], '--style', 'D', '--right-text', text)
        self.assertEqual(process.returncode, 1)
        self.assertEqual([row['status'] for row in rows], ['error', 'ok'])
        for right_text, expected in ((None, '_ABCEFGH_preview.jpg'), (text, '_ABCDEFGH_preview.jpg')):
            flags = ('--right-text', right_text) if right_text is not None else ()
            process, rows = self.cli([large], '--preview', *flags)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(rows[0]['outputs'][0].endswith(expected))
            with Image.open(rows[0]['outputs'][0]) as im:
                im.load()
                self.assertEqual(im.width, 2400)

    def test_spec_formatting_and_brand_mapping(self):
        line1, line2 = metadata.format_specs(
            {'model': 'E-M10MarkIV', 'lens': 'OM 12-45mm F4.0',
             'iso': 800, 'fnumber': 4.0, 'exposure': 1/200, 'focal': 12.0})
        self.assertEqual(line1, 'E-M10 Mark IV | OM 12-45mm F4.0')
        self.assertEqual(line2, 'ISO 800  f/4  1/200s  12mm')
        _, line2 = metadata.format_specs(
            {'model': 'X', 'lens': 'Y', 'iso': 100, 'fnumber': 2.8,
             'exposure': 2.0, 'focal': 35.0})
        self.assertEqual(line2, 'ISO 100  f/2.8  2s  35mm')
        self.assertIsNone(metadata.format_specs({'model': 'X'})[1])
        for raw, shown in (('E-M10MarkIV', 'E-M10 Mark IV'),
                           ('E-M1MarkIII', 'E-M1 Mark III'),
                           ('R6Mark2', 'R6 Mark 2'),
                           ('E-M1X', 'E-M1X'),
                           ('DC-S1RM2', 'DC-S1RM2'),
                           ('EOS 5D Mark IV', 'EOS 5D Mark IV'),
                           ('', ''),
                           (None, None)):
            with self.subTest(model=raw):
                self.assertEqual(metadata.display_model(raw), shown)
        self.assertEqual(metadata.brand_slug({'make': 'OLYMPUS CORPORATION'}),
                         'om-system')
        self.assertEqual(metadata.brand_slug({'make': 'NIKON CORPORATION'}), 'nikon')
        self.assertEqual(metadata.brand_slug({'model': 'iPhone 15 Pro'}), 'apple')
        self.assertEqual(metadata.brand_slug({'make': 'RICOH IMAGING'}), 'ricoh')
        self.assertIsNone(metadata.brand_slug({'make': 'SIGMA'}))
        self.assertEqual(metadata.brand_wordmark({'make': 'SIGMA'}), 'SIGMA')
        self.assertEqual(metadata.brand_wordmark({'make': 'OLYMPUS CORPORATION'}),
                         'OLYMPUS')
