"""CLI regression tests; synthetic images/profiles only. Install requirements.txt first."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
import zlib

from PIL import Image, ImageCms, ImageFont
from PIL.PngImagePlugin import PngInfo

RENDERER = Path(__file__).with_name('frame_photo.py')
_spec = importlib.util.spec_from_file_location('frame_photo', RENDERER)
frame_photo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(frame_photo)


def xmp_packet(**overrides):
    """Lightroom-style XMP packet carrying capture metadata attributes."""
    fields = {'tiff:Make': 'OLYMPUS CORPORATION', 'tiff:Model': 'E-M10MarkIV',
              'exif:LensModel': 'OM 12-45mm F4.0', 'exif:ISOSpeedRatings': '800',
              'exif:FNumber': '4/1', 'exif:ExposureTime': '1/200',
              'exif:FocalLength': '12/1'}
    fields.update(overrides)
    attrs = ' '.join(f'{key}="{value}"' for key, value in fields.items())
    return ('<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description rdf:about="" xmlns:tiff="http://ns.adobe.com/tiff/1.0/" '
            f'xmlns:exif="http://ns.adobe.com/exif/1.0/" {attrs}/>'
            '</rdf:RDF></x:xmpmeta>').encode('utf-8')


def save_with_xmp(image, path, packet):
    """PNG saves need an iTXt chunk; the JPEG-style xmp= kwarg is not stored."""
    info = PngInfo()
    info.add_itxt('XML:com.adobe.xmp', packet.decode('utf-8'))
    image.save(path, pnginfo=info)


def chunk(kind, data):
    return (struct.pack('>I', len(data)) + kind + data
            + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))


def png16(path, color_type):
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    row = b'\0' + struct.pack('>' + 'H' * channels, *([0x1234] * channels)) * 32
    path.write_bytes(b'\x89PNG\r\n\x1a\n'
                     + chunk(b'IHDR', struct.pack('>IIBBBBB', 32, 24, 16, color_type, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(row * 24)) + chunk(b'IEND', b''))


def gray_profile():
    """Build an original minimal ICC v2 grayscale gamma-2.2 profile.

    No OS-specific paths, external profile files or ctypes dependencies.
    """
    u32 = lambda n: struct.pack('>I', n)
    xyz = lambda values: b'XYZ ' + bytes(4) + b''.join(
        struct.pack('>i', round(value * 65536)) for value in values)
    name = b'Photo Framer synthetic gray\0'
    desc = b'desc' + bytes(4) + u32(len(name)) + name + bytes(8 + 2 + 1 + 67)
    tags = [(b'desc', desc),
            (b'wtpt', xyz((0.9642, 1.0, 0.8249))),
            (b'kTRC', b'curv' + bytes(4) + u32(1) + struct.pack('>H', round(2.2 * 256))),
            (b'cprt', b'text' + bytes(4) + b'Synthetic test data\0')]
    header = bytearray(128)
    header[8:12] = u32(0x02100000)
    header[12:24] = b'mntrGRAYXYZ '
    header[24:36] = struct.pack('>6H', 2026, 1, 1, 0, 0, 0)
    header[36:40] = b'acsp'
    header[68:80] = xyz((0.9642, 1.0, 0.8249))[8:]
    offset = 128 + 4 + 12 * len(tags)
    directory, payload = bytearray(u32(len(tags))), bytearray()
    for signature, value in tags:
        directory += signature + u32(offset) + u32(len(value))
        padded = value + bytes((-len(value)) % 4)
        payload += padded
        offset += len(padded)
    header[:4] = u32(offset)
    return bytes(header + directory + payload)


class FramerRegression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        self.gray = gray_profile()

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, paths, *flags, env=None):
        before = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
        output = self.root / 'output'
        process = subprocess.run(
            [sys.executable, str(RENDERER), *map(str, paths), '--out-dir', str(output), *flags],
            capture_output=True, text=True, encoding='utf-8', env=env)
        self.assertTrue(process.stdout.strip(), process.stderr)
        data = json.loads(process.stdout)
        for p, digest in before.items():
            self.assertEqual(digest, hashlib.sha256(p.read_bytes()).digest())
        return process, data['results']

    def test_unicode_paths_with_legacy_stdout_encoding(self):
        path = self.root / 'Ảnh mùa thu.png'
        Image.new('RGB', (32, 24), 'red').save(path)
        env = dict(os.environ, PYTHONIOENCODING='cp1252')
        process, rows = self.cli([path], '--style', 'A', env=env)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(rows[0]['input'], str(path))
        self.assertTrue(Path(rows[0]['outputs'][0]).is_file())
        self.region(rows[0], (32, 24))

    def region(self, row, size, style='A'):
        self.assertEqual(row['status'], 'ok', row)
        with Image.open(row['outputs'][0]) as saved:
            saved.verify()
        with Image.open(row['outputs'][0]) as saved:
            saved.load()
            s = min(size)
            if style == 'F':
                side = max(12, round(s*.075))
                top = max(8, round(s*.04))
                bottom = max(44, round(s*.09), 3*max(9, round(s*.018)))
                self.assertEqual(saved.size, (size[0]+2*side, size[1]+top+bottom))
                return saved.crop((side, top, side+size[0], top+size[1]))
            if style == 'A':
                off = max(4, round(s * .165))
            elif style == 'E':
                off = max(6, round(s * .08)) + max(1, round(s * .004))
            elif style == 'G':
                off = max(12, round(s * .085)) + max(10, round(s * .025))
            elif style in ('C', 'D'):
                off = max(6, round(s * .035))
            else:
                off = (max(4, round(s * .16)) + max(2, round(s * .035))
                       + max(4, round(s * .18)))
            if style in ('C', 'D'):
                band = max(round(s * .12), round(max(9, round(s * .018)) * 3.6), 44)
                self.assertEqual(saved.size,
                                 (size[0] + off * 2, size[1] + off + band))
            else:
                self.assertEqual(saved.size, (size[0] + off * 2, size[1] + off * 2))
            return saved.crop((off, off, off + size[0], off + size[1]))

    def band_crop(self, row, x0, x1, size):
        """Crop a horizontal slice of the style-C caption band for pixel checks."""
        s = min(size)
        side = max(6, round(s * .035))
        band = max(round(s * .12), round(max(9, round(s * .018)) * 3.6), 44)
        with Image.open(row['outputs'][0]) as saved:
            saved.load()
            return saved.crop((side + x0, size[1] + side, side + x1,
                               size[1] + side + band))

    def has_ink(self, crop):
        return min(crop.convert('L').tobytes()) < 128

    def is_blank(self, crop):
        return set(crop.tobytes()) == {255}

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
        regular = ImageFont.truetype(str(frame_photo.FONTS_DIR / 'Inter-Regular.ttf'), 24)
        semibold = ImageFont.truetype(str(frame_photo.FONTS_DIR / 'Inter-SemiBold.ttf'), 24)
        self.assertEqual(regular.getname(), ('Inter', 'Regular'))
        self.assertEqual(semibold.getname(), ('Inter', 'SemiBold'))
        face, emphasis, stroke = frame_photo.specs_fonts(24)
        self.assertEqual(face.getname(), ('Inter', 'Regular'))
        self.assertEqual(emphasis.getname(), ('Inter', 'SemiBold'))
        self.assertEqual(stroke, 0)
        missing = frame_photo.FONTS_DIR.with_name('fonts-missing')
        with unittest.mock.patch.object(frame_photo, 'FONTS_DIR', missing):
            face, emphasis, stroke = frame_photo.specs_fonts(24)
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
        for font_path in (None, frame_photo.FONTS_DIR / 'Inter-Regular.ttf'):
            with self.subTest(font_path=font_path), unittest.mock.patch.object(
                    frame_photo, 'load_logo', side_effect=AssertionError('D must not load logos')):
                result, _ = frame_photo.render(
                    photo, 'D', meta={'make': 'SONY', 'model': 'ILCE-7C'},
                    right_text='ILCE-7C', font_path=font_path)
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
        for right_text, expected in ((None, '_ABCEFG_preview.jpg'), (text, '_ABCDEFG_preview.jpg')):
            flags = ('--right-text', right_text) if right_text is not None else ()
            process, rows = self.cli([large], '--preview', *flags)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(rows[0]['outputs'][0].endswith(expected))
            with Image.open(rows[0]['outputs'][0]) as im:
                im.load()
                self.assertEqual(im.width, 2400)

    def test_style_e_auto_is_deterministic_and_prefers_edge_colors(self):
        photo = Image.new('RGB', (200, 200), 'blue')
        # Red covers only 40% of the picture, at the left/right edges.
        photo.paste('red', (0, 0, 40, 200))
        photo.paste('red', (160, 0, 200, 200))
        before = photo.tobytes()
        first, pos = frame_photo.render(photo, 'E')
        second, _ = frame_photo.render(photo, 'E')
        self.assertEqual(first.tobytes(), second.tobytes())
        red, green, blue = first.getpixel((0, 0))
        self.assertGreater(red, green)
        self.assertGreater(red, blue)
        x, y = pos
        self.assertEqual(first.crop((x, y, x+200, y+200)).tobytes(), before)
        self.assertEqual(photo.tobytes(), before)

    def test_style_e_sampling_is_bounded_and_fixed_colors_skip_analysis(self):
        photo = Image.new('RGB', (1600, 1000), 'orange')
        with unittest.mock.patch.object(photo, 'resize', wraps=photo.resize) as resize:
            frame_photo.color_echo_color(photo)
        sample_size = resize.call_args.args[0]
        self.assertLessEqual(max(sample_size), 96)
        # A supplied color can be resolved without touching any photo object.
        self.assertEqual(frame_photo.color_echo_color(None, frame_color='#123456'), (18, 52, 86))
        self.assertEqual(frame_photo.color_echo_color(None, frame_color='navy'), (0, 0, 128))
        for value in (0, 127, 255):
            self.assertEqual(frame_photo.color_echo_color(
                Image.new('RGB', (80, 60), (value, value, value))), (232, 228, 220))

    def test_style_e_batch_auto_fixed_color_and_mixed_errors(self):
        red, blue, bad = (self.root/name for name in ('red.png', 'blue.png', 'bad.png'))
        Image.new('RGB', (400, 300), 'red').save(red)
        Image.new('RGB', (400, 300), 'blue').save(blue)
        png16(bad, 2)
        for fixed in (None, '#ad896c'):
            flags = ('--frame-color', fixed) if fixed else ()
            process, rows = self.cli([red, bad, blue], '--style', 'E', '--share', *flags)
            self.assertEqual(process.returncode, 1)
            self.assertEqual([row['status'] for row in rows], ['ok', 'error', 'ok'])
            colors = []
            for row, source_color in ((rows[0], 'red'), (rows[2], 'blue')):
                self.assertEqual(len(row['outputs']), 2)
                self.assertEqual(self.region(row, (400, 300), 'E').tobytes(),
                                 Image.new('RGB', (400, 300), source_color).tobytes())
                with Image.open(row['outputs'][0]) as image:
                    colors.append(image.getpixel((0, 0)))
                    self.assertFalse(image.getexif())
                    self.assertFalse(image.getxmp())
                self.assertTrue(any(('fixed' if fixed else 'automatic') in note
                                    for note in row['notes']))
            if fixed:
                self.assertEqual(colors, [(173, 137, 108)]*2)
            else:
                self.assertNotEqual(colors[0], colors[1])

    def test_style_e_options_and_invalid_frame_colors(self):
        photo = Image.new('RGB', (400, 300), 'red')
        for edge in (1, 2, 3):
            with self.subTest(edge=edge):
                result, (x, y) = frame_photo.render(
                    photo, 'E', f'2-1-{edge}', frame_color='#ad896c')
                self.assertEqual(result.crop((x, y, x+400, y+300)).tobytes(), photo.tobytes())
                border_pixel = result.getpixel((x-1, y+100))
                self.assertEqual(border_pixel == (173, 137, 108), edge == 2)
        for invalid in ('', 'not-a-color', '#12345', '#11223344', 'rgba(1,2,3,4)', 'rgb(999,0,0)'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                frame_photo.render(photo, 'E', frame_color=invalid)
        with self.assertRaisesRegex(ValueError, 'only with style E'):
            frame_photo.render(photo, 'A', frame_color='red')
        tones = [frame_photo.render(photo, 'E', f'2-{tone}-1')[0].getpixel((0, 0))
                 for tone in (1, 2, 3)]
        self.assertEqual(len(set(tones)), 3)

    def test_style_f_corner_texts_sprockets_and_preservation(self):
        path = self.root / 'film photo.png'
        save_with_xmp(Image.new('RGB', (900, 600), 'red'), path, xmp_packet())
        process, rows = self.cli([path], '--style', 'F', '--left-text', 'Berlin, Germany',
                                 '--right-text', 'October 2022', '--share')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(self.region(rows[0], (900, 600), 'F').tobytes(),
                         Image.new('RGB', (900, 600), 'red').tobytes())
        with Image.open(rows[0]['outputs'][0]) as im:
            im.load()
            # Default source: side=45, top=24. Sprockets mirror each other.
            left = im.crop((0, 24, 45, 624))
            right = im.crop((945, 24, 990, 624))
            self.assertEqual(left.tobytes(), right.tobytes())
            self.assertGreater(left.convert('L').getextrema()[1], 200)
            self.assertGreater(im.crop((45, 624, 450, im.height)).convert('L').getextrema()[1], 200)
            self.assertGreater(im.crop((500, 624, 945, im.height)).convert('L').getextrema()[1], 200)
            self.assertFalse(im.getexif())
            self.assertFalse(im.getxmp())
        self.assertTrue(any('two user-supplied' in note for note in rows[0]['notes']))
        self.assertFalse(any('Brand mark' in note or 'Spec caption' in note for note in rows[0]['notes']))

    def test_style_f_blank_corners_and_vietnamese_typography(self):
        photo = Image.new('RGB', (1200, 800), 'red')
        for left, right in (('', ''), ('Hà Nội', ''), ('', 'Tháng 10, 2022')):
            with self.subTest(left=left, right=right):
                im, (side, top) = frame_photo.render(photo, 'F', left_text=left, right_text=right)
                band_top = top+800
                left_light = im.crop((side, band_top, 600, im.height)).convert('L').getextrema()[1]
                right_light = im.crop((600, band_top, side+1200, im.height)).convert('L').getextrema()[1]
                self.assertEqual(left_light > 200, bool(left))
                self.assertEqual(right_light > 200, bool(right))
        text = 'Trong Trương | Hà Nội'
        with unittest.mock.patch.object(frame_photo, 'load_logo', side_effect=AssertionError('No F logos')):
            im, (_, top) = frame_photo.render(photo, 'F', left_text=text, right_text=text,
                                             meta={'make': 'SONY', 'model': 'ILCE-7C'})
        left = im.crop((0, top+800, 600, im.height)).convert('L')
        right = im.crop((600, top+800, im.width, im.height)).convert('L')
        left_box = left.point(lambda value: 255 if value > 100 else 0).getbbox()
        right_box = right.point(lambda value: 255 if value > 100 else 0).getbbox()
        self.assertIsNotNone(left_box)
        self.assertEqual(left.crop(left_box).size, right.crop(right_box).size)
        self.assertEqual(left.crop(left_box).tobytes(), right.crop(right_box).tobytes())

    def test_style_f_missing_invalid_and_overlapping_texts(self):
        path = self.root / 'film validation.png'
        Image.new('RGB', (900, 600), 'red').save(path)
        cases = [(), ('--left-text', 'Berlin'), ('--right-text', 'October')]
        cases += [('--left-text', text, '--right-text', '')
                  for text in ('x'*201, 'one\ntwo', 'one\rtwo', 'one\ttwo')]
        cases += [('--left-text', 'W'*100, '--right-text', 'W'*100),
                  ('--left-text', '', '--right-text', '', '--caption', 'third caption')]
        for flags in cases:
            with self.subTest(flags=flags):
                process, rows = self.cli([path], '--style', 'F', *flags)
                self.assertEqual(process.returncode, 1)
                self.assertEqual(rows[0]['status'], 'error')
                self.assertNotIn('outputs', rows[0])
        self.assertFalse((self.root / 'output').exists())
        with self.assertRaisesRegex(ValueError, 'only with style F'):
            frame_photo.render(Image.new('RGB', (40, 32)), 'A', left_text='Berlin')

    def test_style_f_layout_variants_and_batch_errors(self):
        for size in ((400, 300), (300, 400), (40, 32)):
            photo = Image.new('RGB', size, 'red')
            for option in (1, 2, 3):
                with self.subTest(size=size, option=option):
                    im, (x, y) = frame_photo.render(photo, 'F', f'{option}-{option}-{option}',
                                                    left_text='', right_text='')
                    self.assertEqual(im.crop((x, y, x+size[0], y+size[1])).tobytes(), photo.tobytes())
                    self.assertEqual(im.getpixel((0, 0)), frame_photo.F_BACKGROUNDS[option])
                    self.assertGreater(im.crop((0, y, x, y+size[1])).convert('L').getextrema()[1], 200)
        small, large = self.root/'small film.png', self.root/'large film.png'
        Image.new('RGB', (40, 32), 'red').save(small)
        Image.new('RGB', (900, 600), 'red').save(large)
        process, rows = self.cli([small, large], '--style', 'F', '--left-text', 'Berlin',
                                 '--right-text', 'October 2022')
        self.assertEqual(process.returncode, 1)
        self.assertEqual([row['status'] for row in rows], ['error', 'ok'])

    def test_style_f_preview_explicit_fields_and_blanks(self):
        path = self.root/'film preview.png'
        Image.new('RGB', (900, 600), 'red').save(path)
        for right, styles in (('October 2022', 'ABCDEFG'), ('', 'ABCEFG')):
            process, rows = self.cli([path], '--preview', '--left-text', 'Berlin', '--right-text', right)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn(f'_{styles}_preview', rows[0]['outputs'][0])
        process, rows = self.cli([path], '--preview', '--left-text', 'Berlin')
        self.assertEqual(process.returncode, 1)
        self.assertIn('both --left-text and --right-text', rows[0]['error'])

    def test_style_g_deckled_edges_texture_shadow_and_repeatability(self):
        photo = Image.new('RGB', (900, 600), (200, 50, 80))
        state = random.getstate()
        first, pos = frame_photo.render(photo, 'G')
        second, second_pos = frame_photo.render(photo, 'G')
        self.assertEqual(pos, second_pos)
        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertEqual(random.getstate(), state)
        x, y = pos
        self.assertEqual(first.crop((x, y, x+900, y+600)).tobytes(), photo.tobytes())
        self.assertEqual(first.getpixel((0, 0)), frame_photo.G_BACKGROUND)
        pad = 15
        mask = frame_photo._deckle_mask(first.size, pad, (1002, 702), 600, 1)
        # The paper covers the entire photo opening, with irregular outer edges.
        self.assertEqual(mask.crop((x, y, x+900, y+600)).getextrema(), (255, 255))
        starts = [next(py for py in range(pad+12) if mask.getpixel((px, py)) > 128)
                  for px in range(x, x+900, 10)]
        self.assertGreater(max(starts), min(starts))
        grain = first.crop((x, pad+12, x+900, y-4))
        self.assertGreater(len(set(grain.getchannel('R').tobytes())), 3)
        # Contact shadow extends beyond the paper without reaching the canvas corner.
        outside = first.crop((x, first.height-pad+3, x+900, first.height-pad+7))
        self.assertLess(outside.convert('L').getextrema()[0],
                        Image.new('RGB', (1, 1), frame_photo.G_BACKGROUND).convert('L').getpixel((0, 0)))
        frame_photo._paper_texture.cache_clear()
        third, _ = frame_photo.render(photo, 'G')
        self.assertEqual(first.tobytes(), third.tobytes())
        self.assertEqual(frame_photo._paper_texture(frame_photo.G_PAPERS[1], None).size, (256, 256))

    def test_style_g_all_options_keep_rectangular_photo(self):
        for size in ((400, 300), (300, 400), (40, 32), (16, 16)):
            photo = Image.new('RGB', size, 'red')
            for width in (1, 2, 3):
                for paper in (1, 2, 3):
                    for roughness in (1, 2, 3):
                        with self.subTest(size=size, code=(width, paper, roughness)):
                            im, (x, y) = frame_photo.render(photo, 'G', f'{width}-{paper}-{roughness}')
                            self.assertEqual(im.crop((x, y, x+size[0], y+size[1])).tobytes(),
                                             photo.tobytes())
                            self.assertEqual(x, y)
                            self.assertEqual(im.size, (size[0]+2*x, size[1]+2*y))
                            self.assertEqual(im.getpixel((0, 0)), frame_photo.G_BACKGROUND)
                            # Interior paper has texture around the selected tone.
                            center = im.getpixel((x+size[0]//2, y-4))
                            self.assertTrue(all(abs(a-b) <= 4 for a, b in
                                                zip(center, frame_photo.G_PAPERS[paper])))

    def test_style_g_batch_errors_sharing_and_caption(self):
        bad, good = self.root/'16bit paper.png', self.root/'paper photo.png'
        png16(bad, 2)
        Image.new('RGB', (1200, 800), 'red').save(good, icc_profile=self.srgb)
        process, rows = self.cli([bad, good], '--style', 'G', '--share')
        self.assertEqual(process.returncode, 1)
        self.assertEqual([row['status'] for row in rows], ['error', 'ok'])
        self.assertEqual(self.region(rows[1], (1200, 800), 'G').tobytes(),
                         Image.new('RGB', (1200, 800), 'red').tobytes())
        self.assertTrue(any('Deckled Paper' in note for note in rows[1]['notes']))
        with Image.open(rows[1]['outputs'][1]) as shared:
            self.assertLessEqual(max(shared.size), 2048)
            self.assertFalse(shared.getexif())
        font = RENDERER.parent.parent/'assets/fonts/Inter-Regular.ttf'
        photo = Image.new('RGB', (1200, 800), 'red')
        plain, (x, y) = frame_photo.render(photo, 'G')
        captioned, _ = frame_photo.render(photo, 'G', caption='Hà Nội — mùa thu.', font_path=str(font))
        self.assertEqual(captioned.crop((x, y, x+1200, y+800)).tobytes(), photo.tobytes())
        self.assertNotEqual(plain.crop((x, y+800, x+1200, plain.height)).tobytes(),
                            captioned.crop((x, y+800, x+1200, plain.height)).tobytes())
        with self.assertRaisesRegex(ValueError, 'fit'):
            frame_photo.render(photo, 'G', caption='W'*200, font_path=str(font))
        with unittest.mock.patch.object(frame_photo, 'load_logo', side_effect=AssertionError('No G logos')):
            im, _ = frame_photo.render(photo, 'G', meta={'make': 'SONY', 'model': 'ILCE-7C'})
        self.assertEqual(im.tobytes(), plain.tobytes())

    def test_spec_formatting_and_brand_mapping(self):
        line1, line2 = frame_photo.format_specs(
            {'model': 'E-M10MarkIV', 'lens': 'OM 12-45mm F4.0',
             'iso': 800, 'fnumber': 4.0, 'exposure': 1/200, 'focal': 12.0})
        self.assertEqual(line1, 'E-M10 Mark IV | OM 12-45mm F4.0')
        self.assertEqual(line2, 'ISO 800  f/4  1/200s  12mm')
        _, line2 = frame_photo.format_specs(
            {'model': 'X', 'lens': 'Y', 'iso': 100, 'fnumber': 2.8,
             'exposure': 2.0, 'focal': 35.0})
        self.assertEqual(line2, 'ISO 100  f/2.8  2s  35mm')
        self.assertIsNone(frame_photo.format_specs({'model': 'X'})[1])
        for raw, shown in (('E-M10MarkIV', 'E-M10 Mark IV'),
                           ('E-M1MarkIII', 'E-M1 Mark III'),
                           ('R6Mark2', 'R6 Mark 2'),
                           ('E-M1X', 'E-M1X'),
                           ('DC-S1RM2', 'DC-S1RM2'),
                           ('EOS 5D Mark IV', 'EOS 5D Mark IV'),
                           ('', ''),
                           (None, None)):
            with self.subTest(model=raw):
                self.assertEqual(frame_photo.display_model(raw), shown)
        self.assertEqual(frame_photo.brand_slug({'make': 'OLYMPUS CORPORATION'}),
                         'om-system')
        self.assertEqual(frame_photo.brand_slug({'make': 'NIKON CORPORATION'}), 'nikon')
        self.assertEqual(frame_photo.brand_slug({'model': 'iPhone 15 Pro'}), 'apple')
        self.assertEqual(frame_photo.brand_slug({'make': 'RICOH IMAGING'}), 'ricoh')
        self.assertIsNone(frame_photo.brand_slug({'make': 'SIGMA'}))
        self.assertEqual(frame_photo.brand_wordmark({'make': 'SIGMA'}), 'SIGMA')
        self.assertEqual(frame_photo.brand_wordmark({'make': 'OLYMPUS CORPORATION'}),
                         'OLYMPUS')

    def test_reject_all_16bit_color_types_before_output(self):
        paths = []
        for kind in (0, 2, 4, 6):
            p = self.root / f'depth16_{kind}.png'
            png16(p, kind)
            self.assertEqual(p.read_bytes()[24], 16)
            paths.append(p)
        # Detection follows file bytes, even when the extension is misleading.
        disguised = self.root / 'disguised.jpg'
        disguised.write_bytes(paths[1].read_bytes())
        process, rows = self.cli(paths + [disguised])
        self.assertEqual(process.returncode, 1)
        for row in rows:
            with self.subTest(input=row['input']):
                self.assertEqual(row['status'], 'error')
                self.assertIn('High-bit-depth', row['error'])
                self.assertNotIn('outputs', row)
        self.assertFalse((self.root / 'output').exists())

    def test_reject_16bit_in_preview_and_continue_mixed_batch(self):
        bad, good = self.root / 'bad.png', self.root / 'valid.png'
        png16(bad, 2)
        Image.new('RGB', (40, 32), (20, 40, 60)).save(good)
        _, rows = self.cli([bad], '--preview')
        self.assertEqual(rows[0]['status'], 'error')
        process, rows = self.cli([bad, good], '--share')
        self.assertEqual(process.returncode, 1)
        self.assertEqual([r['status'] for r in rows], ['error', 'ok'])
        self.assertEqual(len(rows[1]['outputs']), 2)

    def test_profiled_grayscale_alpha_and_color_key(self):
        values = [0, 1, 64, 127, 128, 192, 254, 255]
        for mode in ('LA', 'L'):
            for style in ('A', 'B', 'C', 'D', 'E', 'F', 'G'):
                with self.subTest(mode=mode, style=style):
                    photo = Image.new(mode, (40, 32))
                    if mode == 'LA':
                        photo.putdata([(32, values[x % len(values)]) for y in range(32) for x in range(40)])
                    else:
                        photo.putdata([32 if x % 2 == 0 else 90 for y in range(32) for x in range(40)])
                        photo.info['transparency'] = 32
                    path = self.root / f'gray_{mode}_{style}.png'
                    photo.save(path, icc_profile=self.gray)
                    alpha = photo.convert('RGBA').getchannel('A').tobytes()
                    colors = ImageCms.profileToProfile(
                        photo.getchannel('L'), ImageCms.ImageCmsProfile(io.BytesIO(self.gray)),
                        ImageCms.ImageCmsProfile(io.BytesIO(self.srgb)), outputMode='RGB')
                    # Independent integer composite, rather than calling renderer helpers.
                    expected = bytes((c * alpha[i // 3] + 255 * (255 - alpha[i // 3]) + 127) // 255
                                     for i, c in enumerate(colors.tobytes()))
                    flags = (('--right-text', 'D') if style == 'D' else
                             ('--left-text', '', '--right-text', '') if style == 'F' else ())
                    process, rows = self.cli([path], '--style', style, '--share', *flags)
                    self.assertEqual(process.returncode, 0, process.stderr)
                    self.assertEqual(self.region(rows[0], photo.size, style).tobytes(), expected)
                    self.assertTrue(any('Transparency flattened' in n for n in rows[0]['notes']))
                    self.assertTrue(any('Converted profiled' in n for n in rows[0]['notes']))
                    with Image.open(rows[0]['outputs'][1]) as share:
                        share.load()
                        self.assertLessEqual(max(share.size), 2048)

    def test_regular_transparency_controls(self):
        rgba = Image.new('RGBA', (40, 32), (20, 80, 140, 128))
        la = Image.new('LA', (40, 32), (32, 128))
        keyed = Image.new('RGB', (40, 32), (20, 80, 140))
        keyed.info['transparency'] = (20, 80, 140)
        palette = Image.new('P', (40, 32), 0)
        palette.putpalette([20, 80, 140] + [0] * 765)
        palette.info['transparency'] = bytes([128] + [255] * 255)
        opaque = Image.new('RGBA', (40, 32), (20, 80, 140, 255))
        for i, photo in enumerate((rgba, la, keyed, palette, opaque)):
            with self.subTest(mode=photo.mode, index=i):
                path = self.root / f'alpha_{i}.png'
                photo.save(path)
                samples = photo.convert('RGBA').tobytes()
                expected = bytes((samples[i + channel] * samples[i + 3]
                                  + 255 * (255 - samples[i + 3]) + 127) // 255
                                 for i in range(0, len(samples), 4) for channel in (0, 1, 2))
                process, rows = self.cli([path])
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(self.region(rows[0], photo.size).tobytes(), expected)

    def test_rgb_pixels_icc_exif_and_no_overwrite(self):
        photo = Image.new('RGB', (40, 32))
        photo.putdata([((x * 11) % 256, (y * 13) % 256, (x + y) % 256)
                       for y in range(32) for x in range(40)])
        exif = Image.Exif()
        exif[274] = 6
        path = self.root / 'ảnh có dấu.png'
        photo.save(path, icc_profile=self.srgb, exif=exif)
        expected = photo.transpose(Image.Transpose.ROTATE_270)
        for style in ('A', 'B', 'C', 'D', 'E', 'F', 'G'):
            with self.subTest(style=style):
                flags = (('--right-text', 'D') if style == 'D' else
                         ('--left-text', '', '--right-text', '') if style == 'F' else ())
                process, rows = self.cli([path], '--style', style, *flags)
                self.assertEqual(process.returncode, 0)
                self.assertEqual(self.region(rows[0], expected.size, style).tobytes(), expected.tobytes())
                final = Path(rows[0]['outputs'][0])
                first_hash = hashlib.sha256(final.read_bytes()).digest()
                with Image.open(final) as im:
                    self.assertEqual(im.info['icc_profile'], self.srgb)
                    self.assertFalse(im.getexif())
                _, rerun = self.cli([path], '--style', style, *flags)
                self.assertNotEqual(rerun[0]['outputs'][0], str(final))
                self.assertEqual(hashlib.sha256(final.read_bytes()).digest(), first_hash)


if __name__ == '__main__':
    unittest.main(verbosity=2)
