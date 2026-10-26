"""CLI regression tests; synthetic images/profiles only. Run with Python + Pillow."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
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
            if style == 'A':
                off = max(4, round(s * .165))
            elif style == 'C':
                off = max(6, round(s * .035))
            else:
                off = (max(4, round(s * .16)) + max(2, round(s * .035))
                       + max(4, round(s * .18)))
            if style == 'C':
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
            for style in ('A', 'B', 'C'):
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
                    process, rows = self.cli([path], '--style', style, '--share')
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
        for style in ('A', 'B', 'C'):
            with self.subTest(style=style):
                process, rows = self.cli([path], '--style', style)
                self.assertEqual(process.returncode, 0)
                self.assertEqual(self.region(rows[0], expected.size, style).tobytes(), expected.tobytes())
                final = Path(rows[0]['outputs'][0])
                first_hash = hashlib.sha256(final.read_bytes()).digest()
                with Image.open(final) as im:
                    self.assertEqual(im.info['icc_profile'], self.srgb)
                    self.assertFalse(im.getexif())
                _, rerun = self.cli([path], '--style', style)
                self.assertNotEqual(rerun[0]['outputs'][0], str(final))
                self.assertEqual(hashlib.sha256(final.read_bytes()).digest(), first_hash)


if __name__ == '__main__':
    unittest.main(verbosity=2)
