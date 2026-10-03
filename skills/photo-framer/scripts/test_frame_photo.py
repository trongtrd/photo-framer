"""CLI regression tests; synthetic images/profiles only. Run with Python + Pillow."""
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from PIL import Image, ImageCms

RENDERER = Path(__file__).with_name('frame_photo.py')


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

    def cli(self, paths, *flags):
        before = {p: hashlib.sha256(p.read_bytes()).digest() for p in paths}
        output = self.root / 'output'
        process = subprocess.run(
            [sys.executable, str(RENDERER), *map(str, paths), '--out-dir', str(output), *flags],
            capture_output=True, text=True, encoding='utf-8')
        data = json.loads(process.stdout)
        for p, digest in before.items():
            self.assertEqual(digest, hashlib.sha256(p.read_bytes()).digest())
        return process, data['results']

    def region(self, row, size, style='A'):
        self.assertEqual(row['status'], 'ok', row)
        with Image.open(row['outputs'][0]) as saved:
            saved.verify()
        with Image.open(row['outputs'][0]) as saved:
            saved.load()
            s = min(size)
            off = max(4, round(s * .165)) if style == 'A' else (
                max(4, round(s * .16)) + max(2, round(s * .035)) + max(4, round(s * .18)))
            self.assertEqual(saved.size, (size[0] + off * 2, size[1] + off * 2))
            return saved.crop((off, off, off + size[0], off + size[1]))

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
            for style in ('A', 'B'):
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
        for style in ('A', 'B'):
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
