"""Style H (Minimal Mat): ratios, thin border, blurred background, limits."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

from PIL import Image

from photoframer import Settings
from photoframer.styles import h_minimal_mat
from .support import FramerCase, RENDERER, png16, render


class MinimalMatBasics(FramerCase):
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
        # Every style now shares the owner-approved 24 MP total output cap.
        # Mode '1' stand-ins: the limit is checked before any canvas is allocated.
        with self.assertRaisesRegex(ValueError, '24 megapixels'):
            render(Image.new('1', (9486, 3162)), 'H', ratio='9:16')
        with self.assertRaisesRegex(ValueError, '24 megapixels'):
            render(Image.new('1', (6000, 5000)), 'B', '1-3-1')
        # Geometry stays unchanged; large H layouts are rejected before painting.
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


class MinimalMatExtensions(unittest.TestCase):
    """Named ratios and blurred backgrounds; total output cap is now 24 MP."""

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
        """Verification restores Pillow's limit even when a custom limit is smaller."""
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
