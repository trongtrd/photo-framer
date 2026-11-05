"""Reject oversized layouts before decoding JPEGs or allocating a canvas."""
from types import SimpleNamespace
import unittest.mock

from PIL import Image, JpegImagePlugin

from photoframer import MAX_OUTPUT_PIXELS, Settings
from photoframer.io import load_photo
from photoframer.registry import STYLES
from photoframer.renderer import plan_render, render, suggested_photo_size
from .support import FramerCase


class OutputLimits(FramerCase):
    def test_all_styles_share_the_24mp_cap_before_painting(self):
        self.assertEqual(MAX_OUTPUT_PIXELS, 24_000_000)
        required = {'D': {'right_text': 'Berlin'}, 'F': {'left_text': '', 'right_text': ''}}
        for code, style in STYLES.items():
            with self.subTest(style=code):
                self.assertEqual(style.max_output_pixels, 24_000_000)
                settings = Settings(code, **required.get(code, {}))
                # No image buffer: a broken limit would enter paint and fail.
                with self.assertRaisesRegex(ValueError, 'above 24 megapixels; export a copy'):
                    render(SimpleNamespace(size=(6000, 4000)), settings)

    def test_suggested_sizes_fit_ratios_labels_and_each_style(self):
        required = {'D': {'right_text': 'Berlin'}, 'F': {'left_text': '', 'right_text': ''}}
        for code, style in STYLES.items():
            options = [required.get(code, {})]
            if code == 'H':
                options = [{'ratio': ratio, 'title': 'Praha', 'subtitle': 'Prague'}
                           for ratio in ('4:5', '1:1', '3:4', '9:16', '16:9', 'original')]
            elif code in 'ABG':
                options += [{'title': 'Praha', 'subtitle': 'Prague'}]
            for values in options:
                for source in ((6000, 4000), (4000, 6000)):
                    with self.subTest(style=code, values=values, source=source):
                        settings = Settings(code, **values)
                        size = suggested_photo_size(source, settings, style)
                        self.assertIsNotNone(size)
                        plan = plan_render(size, settings)
                        self.assertLessEqual(plan.size[0]*plan.size[1], MAX_OUTPUT_PIXELS)
                        self.assertLessEqual(abs(size[0]/size[1]-source[0]/source[1]), .001)
                        # The very next integer long edge exceeds the cap.
                        edge = max(size)+1
                        larger = tuple(value*edge//max(source) for value in source)
                        with self.assertRaisesRegex(ValueError, '24 megapixels'):
                            plan_render(larger, settings)

    def test_large_jpeg_is_rejected_before_decode_and_source_is_unchanged(self):
        path = self.root/'large.jpg'
        source = Image.new('L', (6000, 4000), 128)
        source.save(path)
        source.close()
        before = path.read_bytes()
        with unittest.mock.patch.object(JpegImagePlugin.JpegImageFile, 'load',
                                          side_effect=AssertionError('JPEG was decoded')):
            with self.assertRaisesRegex(ValueError, '24 megapixels'):
                load_photo(path, settings=Settings('H', ratio='9:16'))
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.root/'output').exists())

    def test_preflight_accounts_for_exif_orientation_and_approved_crop(self):
        path = self.root/'rotated.jpg'
        source = Image.new('RGB', (300, 200), 'red')
        exif = Image.Exif()
        exif[274] = 6
        source.save(path, exif=exif)
        observed = []
        from photoframer import renderer
        original_plan = renderer.plan_render
        def plan(size, settings):
            observed.append(size)
            return original_plan(size, settings)
        with unittest.mock.patch.object(renderer, 'plan_render', side_effect=plan):
            photo, _, _ = load_photo(path, (10, 20, 190, 280), Settings('H'))
        self.assertEqual(observed, [(180, 260)])
        self.assertEqual(photo.size, (180, 260))
