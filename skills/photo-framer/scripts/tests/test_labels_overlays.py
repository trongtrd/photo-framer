"""Slots, the H gallery label, captions and PNG signatures."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageChops

from photoframer import text
from photoframer.components import spec_band
from photoframer.styles import h_minimal_mat
from .support import RENDERER, render, signature_png


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
