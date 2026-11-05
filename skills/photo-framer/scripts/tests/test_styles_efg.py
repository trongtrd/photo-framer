"""Styles E (Color Echo), F (Film Edge) and G (Deckled Paper)."""
import random
import unittest
import unittest.mock

from PIL import Image

from photoframer import color
from photoframer.components import paper, spec_band
from photoframer.styles import f_film_edge, g_deckled_paper
from .support import FramerCase, RENDERER, png16, render, save_with_xmp, xmp_packet


class ColorEchoFilmEdgeDeckledPaper(FramerCase):
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
