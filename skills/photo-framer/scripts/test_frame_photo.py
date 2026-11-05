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

from PIL import Image, ImageChops, ImageCms, ImageFont
from PIL.PngImagePlugin import PngInfo

RENDERER = Path(__file__).with_name('frame_photo.py')
_spec = importlib.util.spec_from_file_location('frame_photo', RENDERER)
frame_photo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(frame_photo)  # Adds this folder to sys.path.

import photoframer  # noqa: E402
from photoframer import Settings, color, metadata, text  # noqa: E402
from photoframer.components import paper, spec_band  # noqa: E402
from photoframer.registry import STYLES  # noqa: E402
from photoframer.settings import OPTIONS  # noqa: E402
from photoframer.styles import f_film_edge, g_deckled_paper, h_minimal_mat  # noqa: E402


def render(photo, style='A', code=None, *, profile=None, meta=None, echo_colors=None, **options):
    """Shorthand for photoframer.render with a Settings built from keyword options."""
    return photoframer.render(photo, Settings(style, code, **options), profile=profile,
                              meta=meta, echo_colors=echo_colors)


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
            if style == 'H':
                # Default 1-1-1: exact 4:5 canvas, 3.6% minimum margin, thin keyline.
                k = max(1, round(s*.0055))
                bw, bh = size[0]+2*k, size[1]+2*k
                self.assertEqual(saved.width*5, saved.height*4)
                self.assertGreaterEqual(min(saved.width-bw, saved.height-bh),
                                        2*int(saved.width*.036))
                x, y = (saved.width-bw)//2+k, (saved.height-bh)//2+k
                return saved.crop((x, y, x+size[0], y+size[1]))
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

    def test_style_e_auto_is_deterministic_and_prefers_edge_colors(self):
        photo = Image.new('RGB', (200, 200), 'blue')
        # Red covers only 40% of the picture, at the left/right edges.
        photo.paste('red', (0, 0, 40, 200))
        photo.paste('red', (160, 0, 200, 200))
        before = photo.tobytes()
        first, pos = render(photo, 'E')
        second, _ = render(photo, 'E')
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
            color.color_echo_color(photo)
        sample_size = resize.call_args.args[0]
        self.assertLessEqual(max(sample_size), 96)
        # A supplied color can be resolved without touching any photo object.
        self.assertEqual(color.color_echo_color(None, frame_color='#123456'), (18, 52, 86))
        self.assertEqual(color.color_echo_color(None, frame_color='navy'), (0, 0, 128))
        for value in (0, 127, 255):
            self.assertEqual(color.color_echo_color(
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
                result, (x, y) = render(
                    photo, 'E', f'2-1-{edge}', frame_color='#ad896c')
                self.assertEqual(result.crop((x, y, x+400, y+300)).tobytes(), photo.tobytes())
                border_pixel = result.getpixel((x-1, y+100))
                self.assertEqual(border_pixel == (173, 137, 108), edge == 2)
        for invalid in ('', 'not-a-color', '#12345', '#11223344', 'rgba(1,2,3,4)', 'rgb(999,0,0)'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                render(photo, 'E', frame_color=invalid)
        with self.assertRaisesRegex(ValueError, 'only with style E'):
            render(photo, 'A', frame_color='red')
        tones = [render(photo, 'E', f'2-{tone}-1')[0].getpixel((0, 0))
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
                im, (side, top) = render(photo, 'F', left_text=left, right_text=right)
                band_top = top+800
                left_light = im.crop((side, band_top, 600, im.height)).convert('L').getextrema()[1]
                right_light = im.crop((600, band_top, side+1200, im.height)).convert('L').getextrema()[1]
                self.assertEqual(left_light > 200, bool(left))
                self.assertEqual(right_light > 200, bool(right))
        text = 'Trong Trương | Hà Nội'
        with unittest.mock.patch.object(spec_band, 'load_logo', side_effect=AssertionError('No F logos')):
            im, (_, top) = render(photo, 'F', left_text=text, right_text=text,
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
            render(Image.new('RGB', (40, 32)), 'A', left_text='Berlin')

    def test_style_f_layout_variants_and_batch_errors(self):
        for size in ((400, 300), (300, 400), (40, 32)):
            photo = Image.new('RGB', size, 'red')
            for option in (1, 2, 3):
                with self.subTest(size=size, option=option):
                    im, (x, y) = render(photo, 'F', f'{option}-{option}-{option}',
                                                    left_text='', right_text='')
                    self.assertEqual(im.crop((x, y, x+size[0], y+size[1])).tobytes(), photo.tobytes())
                    self.assertEqual(im.getpixel((0, 0)), f_film_edge.BACKGROUNDS[option])
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
        for right, styles in (('October 2022', 'ABCDEFGH'), ('', 'ABCEFGH')):
            process, rows = self.cli([path], '--preview', '--left-text', 'Berlin', '--right-text', right)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn(f'_{styles}_preview', rows[0]['outputs'][0])
        process, rows = self.cli([path], '--preview', '--left-text', 'Berlin')
        self.assertEqual(process.returncode, 1)
        self.assertIn('both --left-text and --right-text', rows[0]['error'])

    def test_style_g_deckled_edges_texture_shadow_and_repeatability(self):
        photo = Image.new('RGB', (900, 600), (200, 50, 80))
        state = random.getstate()
        first, pos = render(photo, 'G')
        second, second_pos = render(photo, 'G')
        self.assertEqual(pos, second_pos)
        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertEqual(random.getstate(), state)
        x, y = pos
        self.assertEqual(first.crop((x, y, x+900, y+600)).tobytes(), photo.tobytes())
        self.assertEqual(first.getpixel((0, 0)), g_deckled_paper.BACKGROUND)
        pad = 15
        mask = paper._deckle_mask(first.size, pad, (1002, 702), 600, 1)
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
                        Image.new('RGB', (1, 1), g_deckled_paper.BACKGROUND).convert('L').getpixel((0, 0)))
        paper._paper_texture.cache_clear()
        third, _ = render(photo, 'G')
        self.assertEqual(first.tobytes(), third.tobytes())
        self.assertEqual(paper._paper_texture(g_deckled_paper.PAPERS[1], None).size, (256, 256))

    def test_style_g_all_options_keep_rectangular_photo(self):
        for size in ((400, 300), (300, 400), (40, 32), (16, 16)):
            photo = Image.new('RGB', size, 'red')
            for width in (1, 2, 3):
                for paper in (1, 2, 3):
                    for roughness in (1, 2, 3):
                        with self.subTest(size=size, code=(width, paper, roughness)):
                            im, (x, y) = render(photo, 'G', f'{width}-{paper}-{roughness}')
                            self.assertEqual(im.crop((x, y, x+size[0], y+size[1])).tobytes(),
                                             photo.tobytes())
                            self.assertEqual(x, y)
                            self.assertEqual(im.size, (size[0]+2*x, size[1]+2*y))
                            self.assertEqual(im.getpixel((0, 0)), g_deckled_paper.BACKGROUND)
                            # Interior paper has texture around the selected tone.
                            center = im.getpixel((x+size[0]//2, y-4))
                            self.assertTrue(all(abs(a-b) <= 4 for a, b in
                                                zip(center, g_deckled_paper.PAPERS[paper])))

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
        plain, (x, y) = render(photo, 'G')
        captioned, _ = render(photo, 'G', caption='Hà Nội — mùa thu.', font_path=str(font))
        self.assertEqual(captioned.crop((x, y, x+1200, y+800)).tobytes(), photo.tobytes())
        self.assertNotEqual(plain.crop((x, y+800, x+1200, plain.height)).tobytes(),
                            captioned.crop((x, y+800, x+1200, plain.height)).tobytes())
        with self.assertRaisesRegex(ValueError, 'fit'):
            render(photo, 'G', caption='W'*200, font_path=str(font))
        with unittest.mock.patch.object(spec_band, 'load_logo', side_effect=AssertionError('No G logos')):
            im, _ = render(photo, 'G', meta={'make': 'SONY', 'model': 'ILCE-7C'})
        self.assertEqual(im.tobytes(), plain.tobytes())

    def test_style_h_fixed_ratios_center_photo_with_keyline(self):
        for size in ((1200, 800), (800, 1200), (1000, 1000), (37, 16)):
            photo = Image.new('RGB', size, (200, 50, 80))
            s = min(size)
            for ratio, keyline, background in ((1, 1, 1), (2, 2, 2), (1, 3, 3), (2, 1, 1)):
                with self.subTest(size=size, code=f'{ratio}-{background}-{keyline}'):
                    im, (x, y) = render(photo, 'H', f'{ratio}-{background}-{keyline}')
                    self.assertEqual(im.crop((x, y, x+size[0], y+size[1])).tobytes(), photo.tobytes())
                    num, den = (4, 5) if ratio == 1 else (1, 1)
                    self.assertEqual(im.width*den, im.height*num)
                    k = {1: max(1, round(s*.0055)), 2: 0, 3: max(1, round(s*.011))}[keyline]
                    left, top = x-k, y-k
                    right, bottom = im.width-(x+size[0]+k), im.height-(y+size[1]+k)
                    # Centered both ways; the binding side keeps the minimum margin.
                    self.assertLessEqual(abs(left-right), 1)
                    self.assertLessEqual(abs(top-bottom), 1)
                    fraction = .036 if ratio == 1 else .024
                    self.assertGreaterEqual(min(left, right, top, bottom), int(im.width*fraction))
                    self.assertLessEqual(min(left, top), round(im.width*fraction)+num)
                    bg = h_minimal_mat.BACKGROUNDS[background]
                    self.assertEqual(im.getpixel((0, 0)), bg)
                    if k:
                        self.assertEqual(im.getpixel((x-1, y+size[1]//2)), (10, 10, 10))
                        self.assertEqual(im.getpixel((x-k, y-k)), (10, 10, 10))
                        self.assertEqual(im.getpixel((x-k-1, y+size[1]//2)), bg)
                    else:
                        self.assertEqual(im.getpixel((x-1, y+size[1]//2)), bg)

    def test_style_h_thin_border_follows_photo_ratio(self):
        for size in ((1200, 800), (900, 1200)):
            photo = Image.new('RGB', size, 'red')
            im, (x, y) = render(photo, 'H', '3-1-2')
            margin = max(4, round(min(size)*.015))
            self.assertEqual((x, y), (margin, margin))
            self.assertEqual(im.size, (size[0]+2*margin, size[1]+2*margin))
            self.assertEqual(im.crop((x, y, x+size[0], y+size[1])).tobytes(), photo.tobytes())

    def test_style_h_share_sizes_batch_and_notes(self):
        bad, wide, tall = self.root/'16bit mat.png', self.root/'wide mat.png', self.root/'tall mat.jpg'
        png16(bad, 2)
        Image.new('RGB', (1500, 1000), 'red').save(wide, icc_profile=self.srgb)
        Image.new('RGB', (600, 900), 'blue').save(tall, quality=95)
        for code, share in (('1-1-1', (1080, 1350)), ('2-2-2', (1080, 1080)), ('3-3-1', None)):
            with self.subTest(code=code):
                process, rows = self.cli([bad, wide, tall], '--style', 'H', '--choices', code, '--share')
                self.assertEqual(process.returncode, 1)
                self.assertEqual([row['status'] for row in rows], ['error', 'ok', 'ok'])
                for row, size in ((rows[1], (1500, 1000)), (rows[2], (600, 900))):
                    self.assertTrue(any('Minimal Mat' in note for note in row['notes']))
                    with Image.open(row['outputs'][0]) as final, Image.open(row['outputs'][1]) as shared:
                        shared.load()
                        self.assertFalse(shared.getexif())
                        if share:
                            self.assertEqual(shared.size, share)
                        else:
                            self.assertEqual(shared.size, final.size)
                            self.assertLessEqual(max(shared.size), 2048)
        # H allows 100 MP (fixed canvases keep every pixel); other styles keep 60 MP.
        # Mode '1' stand-ins: the limit is checked before any canvas is allocated.
        with self.assertRaisesRegex(ValueError, '100 megapixels'):
            render(Image.new('1', (9486, 3162)), 'H', ratio='9:16')
        with self.assertRaisesRegex(ValueError, '60 megapixels'):
            render(Image.new('1', (6000, 5000)), 'B', '1-3-1')
        # A 29 MP landscape on 9:16 needs ~96 MP, which H now allows.
        width, height = h_minimal_mat.layout((6600, 4400), Settings('H', ratio='9:16')).size
        self.assertTrue(60_000_000 < width*height <= 100_000_000)
        font = RENDERER.parent.parent/'assets/fonts/Inter-Regular.ttf'
        photo = Image.new('RGB', (1200, 800), 'red')
        plain, (x, y) = render(photo, 'H')
        captioned, _ = render(photo, 'H', caption='Hà Nội — mùa thu.', font_path=str(font))
        self.assertEqual(captioned.crop((x, y, x+1200, y+800)).tobytes(), photo.tobytes())
        self.assertNotEqual(plain.tobytes(), captioned.tobytes())
        for flag in ({'right_text': 'x'}, {'left_text': 'x'}, {'frame_color': 'red'}):
            with self.assertRaises(ValueError):
                render(photo, 'H', **flag)

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
            for style in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'):
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
        for style in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'):
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
                    # EXIF is kept by default; pixels are already rotated.
                    self.assertEqual(dict(im.getexif()), {274: 1})
                _, rerun = self.cli([path], '--style', style, *flags)
                self.assertNotEqual(rerun[0]['outputs'][0], str(final))
                self.assertEqual(hashlib.sha256(final.read_bytes()).digest(), first_hash)


def signature_png(path, size=(300, 40), color=(20, 20, 160)):
    """A wide transparent PNG with an opaque bar, standing in for a signature."""
    mark = Image.new('RGBA', size, (0, 0, 0, 0))
    mark.paste(color + (255,), (size[0]//10, size[1]//4, size[0]*9//10, size[1]*3//4))
    mark.save(path)
    return path


def sony_exif(orientation=6):
    """Synthetic camera EXIF with GPS and a maker note (no personal data)."""
    from PIL.TiffImagePlugin import IFDRational as R
    exif = Image.Exif()
    exif[271], exif[272], exif[306] = 'SONY', 'ILCE-7C', '2024:05:01 10:00:00'
    if orientation:
        exif[274] = orientation
    exif[0x8769] = {0x927C: b'maker' * 40, 0xA002: 300, 0xA003: 200, 33434: R(1, 125),
                    33437: R(18, 10), 34855: 250, 37386: R(35, 1), 42036: 'FE 35mm F1.8',
                    36867: '2024:05:01 10:00:00'}
    exif[0x8825] = {1: 'N', 2: (R(21, 1), R(1, 1), R(30, 1)), 3: 'E', 4: (R(105, 1), R(51, 1), R(0, 1))}
    return exif


class MinimalMatExtensions(unittest.TestCase):
    """v0.10: --ratio 3:4/9:16, the 100 MP limit for H and --background blur."""

    @staticmethod
    def two_tone(size):
        photo = Image.new('RGB', size, (200, 40, 40))
        photo.paste((40, 60, 200), (size[0]//2, 0, size[0], size[1]))
        return photo

    def test_new_ratios_are_exact_centered_and_keep_margins(self):
        for ratio, (num, den), fraction in (('3:4', (3, 4), .040), ('9:16', (9, 16), .050)):
            for size in ((1200, 800), (800, 1200), (1000, 1000), (37, 16)):
                for keyline in (1, 2, 3):
                    with self.subTest(ratio=ratio, size=size, keyline=keyline):
                        photo = self.two_tone(size)
                        im, (x, y) = render(photo, 'H', f'1-1-{keyline}', ratio=ratio)
                        self.assertEqual(im.crop((x, y, x+size[0], y+size[1])).tobytes(), photo.tobytes())
                        self.assertEqual(im.width*den, im.height*num)
                        k = {1: max(1, round(min(size)*.0055)), 2: 0, 3: max(1, round(min(size)*.011))}[keyline]
                        left, top = x-k, y-k
                        right, bottom = im.width-(x+size[0]+k), im.height-(y+size[1]+k)
                        self.assertLessEqual(abs(left-right), 1)
                        self.assertLessEqual(abs(top-bottom), 1)
                        self.assertGreaterEqual(min(left, right, top, bottom), int(im.width*fraction))
                        self.assertLessEqual(min(left, top), round(im.width*fraction)+num)

    def test_ratio_flag_overrides_menu_row_without_changing_codes(self):
        photo = self.two_tone((900, 600))
        for code, ratio in (('1-2-3', '4:5'), ('2-2-3', '1:1'), ('3-2-3', 'original')):
            with self.subTest(ratio=ratio):
                by_code, _ = render(photo, 'H', code)
                by_flag, _ = render(photo, 'H', '1-2-3' if code != '1-2-3' else '2-2-3', ratio=ratio)
                self.assertEqual(by_code.tobytes(), by_flag.tobytes())
        for bad in ('2:3', '16:9', ''):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, '--ratio'):
                render(photo, 'H', ratio=bad)

    def test_blur_background_stays_outside_the_photo(self):
        photo = self.two_tone((600, 400))
        plain, _ = render(photo, 'H', ratio='9:16')
        blurred, (x, y) = render(photo, 'H', ratio='9:16', background='blur')
        again, _ = render(photo, 'H', ratio='9:16', background='blur')
        self.assertEqual(blurred.tobytes(), again.tobytes())
        self.assertEqual(plain.size, blurred.size)
        self.assertEqual(blurred.crop((x, y, x+600, y+400)).tobytes(), photo.tobytes())
        # The keyline is still drawn just outside the photo.
        self.assertEqual(blurred.getpixel((x-1, y+200)), (10, 10, 10))
        # Background follows the photo: reddish on the left, bluish on the right, no white mat.
        left, right = blurred.getpixel((5, 5)), blurred.getpixel((blurred.width-6, 5))
        self.assertGreater(left[0], left[2])
        self.assertGreater(right[2], right[0])
        self.assertNotIn((255, 255, 255), (left, right))
        tones = {}
        for tone in ('dark', 'neutral', 'light'):
            image, _ = render(photo, 'H', ratio='9:16', background='blur', blur_tone=tone)
            tones[tone] = sum(image.crop((0, 0, 40, 40)).convert('L').getdata())
            self.assertEqual(image.crop((x, y, x+600, y+400)).tobytes(), photo.tobytes())
        self.assertLess(tones['dark'], tones['neutral'])
        self.assertLess(tones['neutral'], tones['light'])
        default, _ = render(photo, 'H', ratio='9:16', background='blur', blur_tone='dark')
        self.assertEqual(default.tobytes(), blurred.tobytes())
        with self.assertRaisesRegex(ValueError, 'requires --background blur'):
            render(photo, 'H', blur_tone='dark')
        with self.assertRaisesRegex(ValueError, '--background must be blur'):
            render(photo, 'H', background='stars')
        with self.assertRaisesRegex(ValueError, 'only with style H'):
            render(photo, 'A', background='blur')

    def test_verification_reopens_outputs_beyond_the_input_limit(self):
        """Outputs may exceed Pillow's bomb limit (2x the 30 MP input cap) up to 100 MP."""
        from photoframer import io as photo_io
        image = Image.new('RGB', (60, 50), 'red')
        with tempfile.TemporaryDirectory() as temp, \
                unittest.mock.patch.object(Image, 'MAX_IMAGE_PIXELS', 1000):
            saved = photo_io.save_verified(image, Path(temp) / 'big.png', None, image, (0, 0))
            self.assertTrue(saved.is_file())
            self.assertEqual(Image.MAX_IMAGE_PIXELS, 1000)
            with self.assertRaises(Image.DecompressionBombError):
                Image.open(saved)

    def test_cli_share_sizes_notes_and_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wide, tall = root / 'wide.png', root / 'tall.jpg'
            self.two_tone((1500, 1000)).save(wide)
            self.two_tone((600, 900)).save(tall, quality=95)
            for ratio, share in (('3:4', (1080, 1440)), ('9:16', (1080, 1920))):
                with self.subTest(ratio=ratio):
                    process = subprocess.run(
                        [sys.executable, str(RENDERER), str(wide), str(tall), '--style', 'H', '--ratio', ratio,
                         '--background', 'blur', '--share', '--out-dir', str(root / ratio.replace(':', 'x'))],
                        capture_output=True, text=True, encoding='utf-8')
                    self.assertEqual(process.returncode, 0, process.stderr)
                    for row in json.loads(process.stdout)['results']:
                        self.assertIn(f'fixed {ratio} canvas', row['notes'][0])
                        self.assertIn(f'exactly {share[0]}x{share[1]}', row['notes'][0])
                        self.assertTrue(any('Blurred background (dark tone)' in n for n in row['notes']))
                        with Image.open(row['outputs'][1]) as shared:
                            self.assertEqual(shared.size, share)
            process = subprocess.run(
                [sys.executable, str(RENDERER), str(wide), '--preview', '--ratio', '9:16', '--background', 'blur',
                 '--out-dir', str(root / 'preview')], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(process.stdout)['results'][0]['status'], 'ok')
            for flags in (('--ratio', '2:3'), ('--background', 'stars'), ('--blur-tone', 'sepia')):
                with self.subTest(flags=flags):
                    process = subprocess.run([sys.executable, str(RENDERER), str(wide), '--style', 'H', *flags,
                                              '--out-dir', str(root / 'bad')], capture_output=True, text=True)
                    self.assertEqual(process.returncode, 2)


class LabelsAndOverlays(unittest.TestCase):
    """v0.11: slots below the photo, the H gallery label and PNG signatures."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.signature = signature_png(self.root / 'signature.png')
        self.photo = Image.new('RGB', (900, 600), (90, 120, 150))

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def ink_rows(image, box, background):
        crop = image.crop(box)
        return [y for y in range(crop.height)
                if any(crop.getpixel((x, y)) != background for x in range(0, crop.width, 2))]

    def test_title_moves_the_photo_up_and_keeps_it_intact(self):
        plain, (px, py) = render(self.photo, 'H', '2-1-1')
        labeled, (lx, ly) = render(self.photo, 'H', '2-1-1', title='Hồ Hoàn Kiếm',
                                   subtitle='Hà Nội · Tháng 10, 2022')
        self.assertEqual(labeled.width, labeled.height)
        self.assertEqual(labeled.crop((lx, ly, lx+900, ly+600)).tobytes(), self.photo.tobytes())
        self.assertLess(ly - (labeled.height-600)//2, 0)  # Above the plain centered position.
        k = max(1, round(600*.0055))
        rows = self.ink_rows(labeled, (0, ly+600+k, labeled.width, labeled.height), (255, 255, 255))
        self.assertTrue(rows, 'label missing')
        # Title is near-black and subtitle gray; nothing is drawn on the photo.
        band = labeled.crop((0, ly+600+k, labeled.width, labeled.height)).convert('L')
        self.assertLess(band.getextrema()[0], 60)
        # Centered under the photo.
        ink = labeled.crop((0, ly+600+k, labeled.width, labeled.height)).convert('L').point(
            lambda v: 255 if v < 200 else 0).getbbox()
        self.assertLessEqual(abs((ink[0]+ink[2])//2 - (lx+450)), 3)
        for ratio in ('4:5', '9:16', 'original'):
            with self.subTest(ratio=ratio):
                im, (x, y) = render(self.photo, 'H', ratio=ratio, title='Praha')
                self.assertEqual(im.crop((x, y, x+900, y+600)).tobytes(), self.photo.tobytes())
                bare, _ = render(self.photo, 'H', ratio=ratio)
                if ratio == 'original':
                    self.assertGreater(im.height, bare.height)
                    self.assertEqual(im.width, bare.width)

    def test_label_uses_the_spec_card_typeface(self):
        """One typeface across styles: the label matches D's gear line and exposure line."""
        title, subtitle = text.title_fonts(30, 16)
        _, gear, _ = text.specs_fonts(30)
        exposure, _, _ = text.specs_fonts(16)
        self.assertEqual(title.getname(), gear.getname())
        self.assertEqual(title.getname(), ('Inter', 'SemiBold'))
        self.assertEqual(subtitle.getname(), exposure.getname())
        self.assertEqual(subtitle.getname(), ('Inter', 'Regular'))
        self.assertEqual(h_minimal_mat.LABEL_INKS['dark'], (spec_band.GEAR_INK, spec_band.EXPOSURE_INK))
        self.assertEqual(sorted(p.name for p in text.FONTS_DIR.glob('*.ttf')),
                         ['Inter-Regular.ttf', 'Inter-SemiBold.ttf'])

    def test_caption_defaults_to_bundled_inter_regular(self):
        """Without --font, captions use the bundled Inter, exactly as if it were passed.

        C's caption replaces the gear line, so it takes that line's SemiBold face.
        """
        for style in 'ABCEGH':
            with self.subTest(style=style):
                face = text.FONTS_DIR / ('Inter-SemiBold.ttf' if style == 'C' else 'Inter-Regular.ttf')
                default, pos = render(self.photo, style, caption='Hà Nội — mùa thu.')
                explicit, _ = render(self.photo, style, caption='Hà Nội — mùa thu.', font_path=str(face))
                self.assertEqual(default.tobytes(), explicit.tobytes())
                x, y = pos
                self.assertEqual(default.crop((x, y, x+900, y+600)).tobytes(), self.photo.tobytes())
        # Caption gray is the exposure line's and the H subtitle's gray (E keeps its contrast edge color).
        from photoframer.components import caption
        self.assertEqual(caption.CAPTION_INK, spec_band.EXPOSURE_INK)
        self.assertEqual(caption.CAPTION_INK, h_minimal_mat.LABEL_INKS['dark'][1])
        im, (x, y) = render(Image.new('RGB', (900, 600), 'white'), 'A', caption='Hà Nội')
        darkest = min(im.crop((0, y+600, im.width, im.height)).getdata())
        self.assertEqual(darkest, (115, 115, 115))

    def test_label_contrast_on_blur_and_validation(self):
        dark_photo = Image.new('RGB', (900, 600), (20, 20, 25))
        im, (x, y) = render(dark_photo, 'H', ratio='9:16', background='blur', title='Đêm')
        band = im.crop((0, y+605, im.width, im.height)).convert('L')
        self.assertGreater(band.getextrema()[1], 200)  # Light ink on the dark blur.
        for options, message in (({'subtitle': 'x'}, 'requires --title'),
                                 ({'title': ' '}, 'single-line'), ({'title': 'a\nb'}, 'single-line'),
                                 ({'title': 'W'*120}, 'too wide'),
                                 ({'title': 'x', 'caption': 'y', 'font_path': str(text.FONTS_DIR /
                                   'Inter-Regular.ttf')}, 'not both')):
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, message):
                render(self.photo, 'H', **options)
        with self.assertRaisesRegex(ValueError, 'only with style H'):
            render(self.photo, 'A', title='x')

    def test_signature_placement_opacity_and_slots(self):
        for style, code in (('A', None), ('B', None), ('E', '2-1-2'), ('G', None)):
            for position in ('bottom-left', 'bottom-center', 'bottom-right'):
                with self.subTest(style=style, position=position):
                    plain, pos = render(self.photo, style, code)
                    signed, spos = render(self.photo, style, code, signature=self.signature,
                                          signature_position=position, signature_width=.1)
                    self.assertEqual(pos, spos)
                    x, y = pos
                    self.assertEqual(signed.crop((x, y, x+900, y+600)).tobytes(), self.photo.tobytes())
                    self.assertNotEqual(plain.tobytes(), signed.tobytes())
                    diff = ImageChops.difference(plain, signed).getbbox()
                    self.assertGreaterEqual(diff[1], y+600)  # Only below the photo.
                    center = (diff[0]+diff[2])/2
                    expected = {'bottom-left': x, 'bottom-center': x+450, 'bottom-right': x+900}[position]
                    if position == 'bottom-center':
                        self.assertLessEqual(abs(center-expected), 3)
                    elif position == 'bottom-left':
                        self.assertLessEqual(abs(diff[0]-expected-signed.width*.1*.1), 3)
                    else:
                        self.assertLessEqual(abs(diff[2]-expected+signed.width*.1*.1), 3)
        faint, (x, y) = render(self.photo, 'A', signature=self.signature, signature_opacity=.3)
        strong, _ = render(self.photo, 'A', signature=self.signature)
        bar = ImageChops.difference(faint, strong).getbbox()
        self.assertIsNotNone(bar)
        self.assertGreater(min(faint.crop(bar).convert('L').getdata()),
                           min(strong.crop(bar).convert('L').getdata()))

    def test_signature_errors_and_collisions(self):
        font = str(text.FONTS_DIR / 'Inter-Regular.ttf')
        square = signature_png(self.root / 'square.png', size=(100, 100))
        cases = [({'signature': square, 'signature_width': .3}, 'A', 'does not fit'),
                 ({'signature_width': .1}, 'A', 'require --signature'),
                 ({'signature': self.root / 'missing.png'}, 'A', 'not found'),
                 ({'signature': self.signature, 'caption': 'Hà Nội — mùa thu.', 'font_path': font},
                  'A', 'overlap the caption'),
                 ({'signature': self.signature}, 'C', 'only with style'),
                 ({'signature': self.signature}, 'F', 'only with style')]
        jpeg = self.root / 'signature.jpg'
        Image.new('RGB', (300, 40)).save(jpeg)
        cases.append(({'signature': jpeg}, 'A', 'PNG'))
        for options, style, message in cases:
            with self.subTest(options=options, style=style), self.assertRaisesRegex(ValueError, message):
                extra = {'left_text': '', 'right_text': ''} if style == 'F' else {}
                render(self.photo, style, **options, **extra)
        # A caption at the right leaves room for a signature on the left.
        im, _ = render(self.photo, 'A', caption='Hà Nội', font_path=font, signature=self.signature,
                       signature_position='bottom-left', signature_width=.1)
        # H takes no signature (unbalanced beside its centered label), with or without one.
        for options in ({}, {'title': 'Praha'}):
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, 'only with style A, B, E or G'):
                render(self.photo, 'H', signature=self.signature, **options)

    def test_preview_shows_label_and_signature(self):
        path = self.root / 'photo.png'
        self.photo.save(path)
        def sheet(*flags):
            process = subprocess.run([sys.executable, str(RENDERER), str(path), '--preview', *flags,
                                      '--out-dir', str(self.root / f'p{len(flags)}')],
                                     capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(process.returncode, 0, process.stderr)
            row = json.loads(process.stdout)['results'][0]
            self.assertEqual(row['status'], 'ok', row)
            with Image.open(row['outputs'][0]) as im:
                return im.convert('RGB').copy()
        plain = sheet()
        labeled = sheet('--title', 'Praha', '--signature', str(self.signature), '--signature-width', '0.1')
        self.assertEqual(plain.size, labeled.size)
        # Panels differ: A, B, E, G gain the signature; H gains the label.
        self.assertNotEqual(plain.crop((0, 0, 800, plain.height//2)).tobytes(),
                            labeled.crop((0, 0, 800, labeled.height//2)).tobytes())
        # A signature too large for some margins keeps the sheet and marks those panels.
        square = signature_png(self.root / 'square.png', size=(100, 100))
        sheet('--signature', str(square), '--signature-width', '0.3')

    def test_cli_label_signature_notes_and_flag_errors(self):
        path = self.root / 'photo.png'
        self.photo.save(path)
        process = subprocess.run(
            [sys.executable, str(RENDERER), str(path), '--style', 'H', '--choices', '2-1-1',
             '--title', 'Hồ Hoàn Kiếm', '--subtitle', 'Hà Nội',
             '--out-dir', str(self.root / 'out')], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stderr)
        notes = json.loads(process.stdout)['results'][0]['notes']
        self.assertTrue(any('Gallery label: title and subtitle' in n for n in notes), notes)
        process = subprocess.run(
            [sys.executable, str(RENDERER), str(path), '--style', 'G', '--signature', str(self.signature),
             '--signature-position', 'bottom-left', '--signature-width', '0.08',
             '--out-dir', str(self.root / 'out')], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(process.returncode, 0, process.stderr)
        notes = json.loads(process.stdout)['results'][0]['notes']
        self.assertTrue(any('Signature PNG placed bottom-left' in n for n in notes), notes)
        for flags in (('--signature-width', '0.9'), ('--signature-opacity', '0'),
                      ('--signature-position', 'top-left'), ('--title', '')):
            with self.subTest(flags=flags):
                process = subprocess.run([sys.executable, str(RENDERER), str(path), '--style', 'G',
                                          '--signature', str(self.signature), *flags,
                                          '--out-dir', str(self.root / 'bad')], capture_output=True)
                self.assertEqual(process.returncode, 2)


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
                  'raw_model': True, 'ratio': '9:16', 'background': 'blur', 'blur_tone': 'light',
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
