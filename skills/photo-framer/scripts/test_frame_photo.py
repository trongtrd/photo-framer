"""Runs every regression test in tests/ (synthetic images and profiles only).

Install requirements.txt first. Examples, from this folder:

    python test_frame_photo.py                      # all tests, verbose
    python test_frame_photo.py -k metadata          # tests whose name matches
    python -m unittest tests.test_metadata          # one module

Modules: test_cli_and_input, test_color_profile, test_spec_cards (C, D), test_styles_efg,
test_style_h, test_labels_overlays, test_metadata, test_registry; shared helpers live in tests/support.py.
"""
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent

if __name__ == '__main__':
    sys.path.insert(0, str(HERE))
    unittest.main(module=None, argv=[sys.argv[0], 'discover', '-v', '-s', str(HERE / 'tests'),
                                     '-t', str(HERE), *sys.argv[1:]])
