"""Shared helpers for the regression tests: synthetic images, profiles and the CLI runner."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from PIL import Image, ImageCms
from PIL.PngImagePlugin import PngInfo

RENDERER = Path(__file__).resolve().parent.parent / 'frame_photo.py'
_spec = importlib.util.spec_from_file_location('frame_photo', RENDERER)
frame_photo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(frame_photo)  # Adds the scripts folder to sys.path.

import photoframer  # noqa: E402
from photoframer import Settings  # noqa: E402


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


class FramerCase(unittest.TestCase):
    """Temp directory, CLI runner and pixel helpers shared by the style tests."""

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
