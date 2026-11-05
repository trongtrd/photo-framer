"""Command line, input files, color profiles and transparency."""
import hashlib
import io
import os
from pathlib import Path

from PIL import Image, ImageCms

from .support import FramerCase, png16


class CliAndInputFiles(FramerCase):
    def test_unicode_paths_with_legacy_stdout_encoding(self):
        path = self.root / 'Ảnh mùa thu.png'
        Image.new('RGB', (32, 24), 'red').save(path)
        env = dict(os.environ, PYTHONIOENCODING='cp1252')
        process, rows = self.cli([path], '--style', 'A', env=env)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(rows[0]['input'], str(path))
        self.assertTrue(Path(rows[0]['outputs'][0]).is_file())
        self.region(rows[0], (32, 24))

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
