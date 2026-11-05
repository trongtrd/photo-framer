"""Opt-in per-image capture details: exact siblings, precedence and batch errors."""
import json
from pathlib import Path

from PIL import Image

from photoframer import Settings
from photoframer.capture import MAX_SIDECAR_BYTES, load_capture_sidecar
from .support import FramerCase, sony_exif


class CaptureSidecars(FramerCase):
    def write_sidecar(self, path, values):
        sibling = path.with_name(path.name + '.json')
        sibling.write_text(json.dumps(values, ensure_ascii=False), encoding='utf-8')
        return sibling

    def test_each_image_uses_its_own_details_and_explicit_flags_win(self):
        first, second = self.root/'ảnh một.png', self.root/'ảnh hai.png'
        for path in (first, second):
            Image.new('RGB', (900, 600), 'white').save(path)
        self.write_sidecar(first, {'camera': 'Pentax 67', 'lens': '105mm', 'iso': 400,
                                   'aperture': 'f/2.4', 'shutter': '1/125s', 'focal': '105mm'})
        self.write_sidecar(second, {'camera': 'Hasselblad 500C', 'iso': 100})
        process, rows = self.cli([first, second], '--style', 'C', '--capture-sidecar',
                                  '--iso', '800', '--share')
        self.assertEqual(process.returncode, 0, rows)
        for path, row, camera, extra in ((first, rows[0], 'Pentax 67',
                                          ('--lens', '105mm', '--aperture', '2.4',
                                           '--shutter', '1/125', '--focal', '105')),
                                         (second, rows[1], 'Hasselblad 500C', ())):
            expected_process, expected = self.cli([path], '--style', 'C', '--camera', camera,
                                                   '--iso', '800', '--share', *extra)
            self.assertEqual(expected_process.returncode, 0, expected)
            for actual_path, expected_path in zip(row['outputs'], expected[0]['outputs']):
                self.assertEqual(Path(actual_path).read_bytes(), Path(expected_path).read_bytes())
            self.assertTrue(any('Capture sidecar loaded:' in note for note in row['notes']))
            self.assertFalse(any('Brand mark:' in note for note in row['notes']))

    def test_sidecars_override_exif_for_display_without_rewriting_it(self):
        path = self.root/'digital.png'
        Image.new('RGB', (900, 600), 'white').save(path, exif=sony_exif(orientation=1))
        self.write_sidecar(path, {'camera': 'Exact owner text', 'iso': 800})
        process, rows = self.cli([path], '--style', 'D', '--right-text', 'Berlin',
                                  '--capture-sidecar')
        self.assertEqual(process.returncode, 0, rows)
        expected_process, expected = self.cli([path], '--style', 'D', '--right-text', 'Berlin',
                                               '--camera', 'Exact owner text', '--iso', '800')
        self.assertEqual(expected_process.returncode, 0, expected)
        with Image.open(rows[0]['outputs'][0]) as actual, \
                Image.open(expected[0]['outputs'][0]) as explicit:
            self.assertEqual(actual.tobytes(), explicit.tobytes())
            self.assertEqual(actual.getexif()[272], 'ILCE-7C')
            self.assertEqual(actual.getexif().get_ifd(0x8769)[34855], 250)

    def test_loading_is_opt_in_missing_is_explicit_and_bad_files_are_per_image(self):
        bad, good = self.root/'bad.png', self.root/'good.png'
        for path in (bad, good):
            Image.new('RGB', (400, 300), 'white').save(path)
        self.write_sidecar(bad, {'camrea': 'typo'})
        process, rows = self.cli([bad, good], '--style', 'C')
        self.assertEqual(process.returncode, 0, rows)  # Never read JSON without the flag.
        process, rows = self.cli([bad, good], '--style', 'C', '--capture-sidecar')
        self.assertEqual(process.returncode, 1)
        self.assertEqual([row['status'] for row in rows], ['error', 'ok'])
        self.assertIn('unknown capture fields: camrea', rows[0]['error'])
        self.assertTrue(any('No capture sidecar: good.png.json' in n for n in rows[1]['notes']))
        process, rows = self.cli([good], '--style', 'A', '--capture-sidecar')
        self.assertEqual(process.returncode, 1)
        self.assertIn('only with style C or D', rows[0]['error'])

    def test_preview_uses_the_first_images_sidecar(self):
        path = self.root/'scan.png'
        Image.new('RGB', (900, 600), 'white').save(path)
        self.write_sidecar(path, {'camera': 'Pentax 67', 'iso': 400})
        process, rows = self.cli([path], '--preview', '--capture-sidecar')
        expected_process, expected = self.cli([path], '--preview', '--camera', 'Pentax 67', '--iso', '400')
        self.assertEqual(process.returncode, 0, rows)
        self.assertEqual(expected_process.returncode, 0, expected)
        with Image.open(rows[0]['outputs'][0]) as actual, Image.open(expected[0]['outputs'][0]) as explicit:
            self.assertEqual(actual.tobytes(), explicit.tobytes())

    def test_strict_json_values_exact_sibling_and_bom(self):
        path = self.root/'scan.jpg'
        sibling = path.with_name(path.name + '.json')
        for content in ('[]', '{"iso":true}', '{"iso":null}', '{"camera":12}',
                        '{"iso":0}', '{"iso":-1}', '{"iso":"NaN"}', '{"iso":Infinity}',
                        '{"shutter":"1/0"}', '{"shutter":"1e10000"}',
                        '{"camera":" "}', '{"lens":"a\\nb"}',
                        '{"camera":"a","camera":"b"}', '{"title":"not capture data"}',
                        '{"iso":[]}', '{', 'x'*(MAX_SIDECAR_BYTES+1)):
            with self.subTest(content=content[:50]):
                sibling.write_text(content, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Invalid capture sidecar scan.jpg.json'):
                    load_capture_sidecar(path, Settings('C'))
        sibling.write_text('{"camera":"Máy của tôi","iso":400}', encoding='utf-8-sig')
        settings, _ = load_capture_sidecar(path, Settings('C', iso=800))
        self.assertEqual(settings.camera, 'Máy của tôi')
        self.assertEqual(settings.iso, 800)
        sibling.unlink()
        (self.root/'scan.json').write_text('{"camera":"Wrong sibling"}', encoding='utf-8')
        settings, notes = load_capture_sidecar(path, Settings('C'))
        self.assertIsNone(settings.camera)
        self.assertIn('No capture sidecar:', notes[0])
