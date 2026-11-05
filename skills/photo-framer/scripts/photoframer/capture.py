"""Typed capture values and opt-in per-image JSON sidecars (display only)."""
from __future__ import annotations

import argparse
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path

from .text import is_single_line

MAX_SIDECAR_BYTES = 16_384


def text_value(flag):
    def parse(value):
        if not value.strip() or not is_single_line(value):
            raise argparse.ArgumentTypeError(f'{flag} must be one non-empty line up to 200 characters')
        return value
    return parse


def number(flag, prefix='', suffix='', fraction=False):
    """Positive number with the same spelling accepted by the CLI and JSON."""
    def parse(value):
        text = value.strip()
        if prefix and text.lower().startswith(prefix):
            text = text[len(prefix):]
        if suffix and text.lower().endswith(suffix):
            text = text[:-len(suffix)]
        try:
            result = float(Fraction(text.strip())) if fraction else float(text)
        except (ValueError, ZeroDivisionError, OverflowError):
            result = None
        if result is None or not result > 0 or result == float('inf'):
            raise argparse.ArgumentTypeError(f'{flag} must be a positive number, got {value!r}')
        return result
    return parse


PARSERS = {
    'camera': text_value('--camera'), 'lens': text_value('--lens'),
    'iso': number('--iso', prefix='iso'), 'aperture': number('--aperture', prefix='f/'),
    'shutter': number('--shutter', suffix='s', fraction=True),
    'focal': number('--focal', suffix='mm'),
}


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate field {key!r}')
        result[key] = value
    return result


def load_capture_sidecar(path, settings):
    """Exact sibling name, e.g. scan.jpg.json. Explicit flags win field by field.

    Missing siblings retain the existing EXIF/XMP and explicit-flag behavior;
    malformed siblings fail only that image in the batch. Never modify EXIF.
    """
    sidecar = Path(path).with_name(Path(path).name + '.json')
    if not sidecar.exists():
        return settings, [f'No capture sidecar: {sidecar.name}; existing capture values used.']
    try:
        with sidecar.open('rb') as stream:
            content = stream.read(MAX_SIDECAR_BYTES + 1)
        if len(content) > MAX_SIDECAR_BYTES:
            raise ValueError(f'file exceeds {MAX_SIDECAR_BYTES} bytes')
        values = json.loads(content.decode('utf-8-sig'), object_pairs_hook=_unique_keys)
        if not isinstance(values, dict):
            raise ValueError('use a JSON object containing capture fields')
        unknown = set(values) - PARSERS.keys()
        if unknown:
            raise ValueError('unknown capture fields: ' + ', '.join(sorted(unknown)))
        parsed = {}
        for field, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ValueError(f'{field} must be text or a positive number, not null or a collection')
            if field in ('camera', 'lens') and not isinstance(value, str):
                raise ValueError(f'{field} must be text')
            parsed[field] = PARSERS[field](str(value))
    except (OSError, UnicodeError, ValueError, argparse.ArgumentTypeError) as error:
        raise ValueError(f'Invalid capture sidecar {sidecar.name}: {error}') from error
    overrides = {field: value for field, value in parsed.items()
                 if getattr(settings, field) is None}
    fields = ', '.join(values) or 'no fields'
    return replace(settings, **overrides), [
        f'Capture sidecar loaded: {sidecar.name} ({fields}); explicit flags take priority. '
        'Display only; source EXIF is not changed.'
    ]
