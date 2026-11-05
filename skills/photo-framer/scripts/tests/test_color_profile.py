"""The bundled sRGB profile and byte-for-byte reproducible outputs."""
import io
import json
import struct
import subprocess
import sys
import time

from PIL import Image, ImageCms

import photoframer
from photoframer import constants
from .support import RENDERER, FramerCase

PROFILE = constants.SKILL_DIR / 'assets' / 'profiles' / 'srgb.icc'
FIXED_DATE = (2026, 11, 5, 0, 0, 0)


class BundledSrgbProfile(FramerCase):
    """v0.11.1: the renderer's sRGB profile is a committed file, not built at run time."""

    @staticmethod
    def without_date(profile):
        return profile[:24] + profile[36:]

    def test_bundled_file_is_littlecms_srgb_with_a_fixed_date(self):
        built = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        bundled = PROFILE.read_bytes()
        # Whatever LittleCMS build is installed, it makes this profile apart from the stamp.
        self.assertEqual(self.without_date(bundled), self.without_date(built))
        self.assertEqual(struct.unpack('>6H', bundled[24:36]), FIXED_DATE)
        profile = ImageCms.ImageCmsProfile(io.BytesIO(bundled))
        self.assertEqual(ImageCms.getProfileDescription(profile).strip(), 'sRGB built-in')
        self.assertEqual(bundled[16:20], b'RGB ')

    def test_renderer_uses_exactly_the_bundled_bytes(self):
        self.assertEqual(photoframer.SRGB, PROFILE.read_bytes())
        photo = self.root / 'plain.png'
        Image.new('RGB', (160, 100), (90, 120, 150)).save(photo)
        process = subprocess.run([sys.executable, str(RENDERER), str(photo), '--style', 'A',
                                  '--out-dir', str(self.root / 'out')],
                                 capture_output=True, text=True, encoding='utf-8')
        row = json.loads(process.stdout)['results'][0]
        self.assertEqual(row['status'], 'ok', process.stdout)
        final = next(path for path in row['outputs'] if path.endswith('.png'))
        with Image.open(final) as image:
            self.assertEqual(image.info['icc_profile'], PROFILE.read_bytes())

    def test_outputs_do_not_depend_on_the_second_they_were_made(self):
        photo = self.root / 'plain.png'
        gradient = Image.new('RGB', (200, 130))
        gradient.putdata([(x, y, (x + y) % 256) for y in range(130) for x in range(200)])
        gradient.save(photo)

        def render(folder):
            out = self.root / folder
            for flags in (('--style', 'A', '--share'), ('--style', 'G', '--share'), ('--preview',)):
                process = subprocess.run(
                    [sys.executable, str(RENDERER), str(photo), '--out-dir', str(out), *flags],
                    capture_output=True, text=True, encoding='utf-8')
                self.assertTrue(all(row['status'] == 'ok' for row in json.loads(process.stdout)['results']),
                                process.stdout)
            return {path.name: path.read_bytes() for path in sorted(out.iterdir())}

        first = render('first')
        time.sleep(1.2)  # LittleCMS stamps whole seconds, so a run built at run time would differ
        second = render('second')
        self.assertEqual(sorted(first), sorted(second))
        self.assertGreaterEqual(len(first), 5)  # two finals, two share copies, one preview
        for name in first:
            self.assertEqual(first[name], second[name], f'{name} differs between runs')
