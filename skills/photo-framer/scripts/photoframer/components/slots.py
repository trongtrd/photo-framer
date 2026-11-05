"""Free regions outside the photo that text and overlays claim.

A style exposes its slots (for now one: the margin below the photo). Each
item drawn there claims its exact box; an item that leaves the slot or
overlaps an earlier one is rejected with a clear error instead of being
shrunk, moved or drawn over the photo.
"""
from __future__ import annotations


def _overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


class Slot:
    def __init__(self, box, align=None):
        self.box = tuple(box)                  # (x0, y0, x1, y1), outside the photo
        self.align = align or (box[0], box[2])  # x-range items align to (photo edges)
        self.taken = []

    @property
    def height(self):
        return max(0, self.box[3]-self.box[1])

    def claim(self, box, what, check=True):
        """Reserve box for `what`; check=False records an item placed by older rules."""
        if check:
            x0, y0, x1, y1 = self.box
            if not (x0 <= box[0] and y0 <= box[1] and box[2] <= x1 and box[3] <= y1):
                raise ValueError(f'{what} does not fit in the margin below the photo.')
            for other, name in self.taken:
                if _overlaps(box, other):
                    raise ValueError(f'{what} would overlap the {name.lower()}; '
                                     'choose another position or shorten the text.')
        self.taken.append((tuple(box), what))
        return box
