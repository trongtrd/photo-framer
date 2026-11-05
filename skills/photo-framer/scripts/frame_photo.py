#!/usr/bin/env python3
"""Deterministic photo framing. Python 3.10+, Pillow; no network or AI APIs.

Thin entry point: the renderer lives in the photoframer package next to this
file. Run `python frame_photo.py --help` for usage.
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from photoframer.cli import main  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(main())
