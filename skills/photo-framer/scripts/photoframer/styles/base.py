"""Declarative description of a style: identity, menu, accepted options, hooks."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, NamedTuple

from ..constants import MAX_OUTPUT_PIXELS


class Row(NamedTuple):
    """One menu row: label and three options, each as (English, Vietnamese)."""
    label: tuple[str, str]
    options: tuple[tuple[str, str], tuple[str, str], tuple[str, str]]


class Context(NamedTuple):
    """Per-photo data that is not a user setting."""
    profile: bytes | None = None
    meta: dict = {}
    echo_colors: tuple | None = None


def _no_validation(settings):
    return None


def _no_share_size(choices):
    return None


def _no_notes(settings, *, share, sources, echo_colors):
    return []


@dataclass(frozen=True)
class Style:
    code: str
    name: tuple[str, str]            # menu name (English, Vietnamese)
    readme_title: str                # README style table link text
    look: tuple[str, str]            # README "Look" column (English, Vietnamese)
    preview_label: str
    default: str                     # default three-digit choice code
    rows: tuple[Row, Row, Row]
    choices_hint: str                # reply order for --choices help
    accepts: frozenset               # named options (Settings fields) this style takes
    layout: Callable                 # (photo_size, choices) -> layout with .size
    paint: Callable                  # (photo, layout, settings, ctx) -> (canvas, pos)
    requires: frozenset = frozenset()  # accepted options that must be supplied
    validate: Callable = _no_validation
    uses_metadata: bool = False
    share_size: Callable = _no_share_size  # exact share JPEG size or None
    notes: Callable = _no_notes
    max_output_pixels: int = MAX_OUTPUT_PIXELS

    @property
    def default_choices(self):
        return tuple(map(int, self.default.split('-')))


COMMON = frozenset({'caption', 'font_path'})
