"""Ordered style registry used by the CLI, the preview and the docs generator."""
from __future__ import annotations

from .styles import (a_floating, b_gallery, c_spec_card, d_custom_spec, e_color_echo,
                     f_film_edge, g_deckled_paper, h_minimal_mat)

STYLES = {module.STYLE.code: module.STYLE for module in (
    a_floating, b_gallery, c_spec_card, d_custom_spec, e_color_echo,
    f_film_edge, g_deckled_paper, h_minimal_mat)}
DEFAULT_STYLE = 'A'


def get_style(code):
    return STYLES[code]
