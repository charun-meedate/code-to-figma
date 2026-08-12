#!/usr/bin/env python3
"""Generate the three PNG pairs selftest.sh compares.

Regenerate with:  python3 make_image_fixtures.py

Each pair is a stand-in for a real outcome seen on the proven run:

  identical/   the frame matches                      -> no bands
  text-band/   one row of text differs                -> one narrow band, PASS shape
  structural/  an element sits in the wrong place     -> a band on an element edge
  scrim/       a structural error under a translucent -> low % but a wide band;
               overlay                                   the warning must fire

The reference images are written at @2x so the scale-inference path is
exercised as well.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).parent
W, H = 120, 240  # 1x figma-export size; references are 2x


def canvas(w: int, h: int) -> np.ndarray:
    return np.full((h, w, 3), 250, dtype=np.uint8)


def box(a: np.ndarray, x0: int, y0: int, x1: int, y1: int, colour: tuple[int, int, int]) -> None:
    a[y0:y1, x0:x1] = colour


def base(w: int, h: int, s: int) -> np.ndarray:
    """A card with a header bar, two text rows and a button."""
    a = canvas(w, h)
    box(a, 8 * s, 16 * s, 112 * s, 120 * s, (255, 255, 255))   # card
    box(a, 8 * s, 16 * s, 112 * s, 20 * s, (40, 90, 200))      # header bar
    box(a, 16 * s, 40 * s, 90 * s, 46 * s, (30, 30, 30))       # text row 1
    box(a, 16 * s, 56 * s, 70 * s, 62 * s, (30, 30, 30))       # text row 2
    box(a, 16 * s, 90 * s, 104 * s, 110 * s, (255, 90, 0))     # button
    return a


def save(a: np.ndarray, name: str) -> None:
    Image.fromarray(a).save(HERE / name)
    print(f"  wrote {name}  {a.shape[1]}x{a.shape[0]}")


def main() -> None:
    # 1. identical — reference @2x, export @1x, same content
    save(base(W * 2, H * 2, 2), "identical__ref.png")
    save(base(W, H, 1), "identical__fig.png")

    # 2. text band — text row 2 is a different length, everything else exact
    save(base(W * 2, H * 2, 2), "textband__ref.png")
    a = base(W, H, 1)
    box(a, 16, 56, 70, 62, (250, 250, 250))
    box(a, 16, 56, 84, 62, (30, 30, 30))
    save(a, "textband__fig.png")

    # 3. structural — the button is 40px lower than it should be
    save(base(W * 2, H * 2, 2), "structural__ref.png")
    a = base(W, H, 1)
    box(a, 16, 90, 104, 110, (250, 250, 250))
    box(a, 16, 130, 104, 150, (255, 90, 0))
    save(a, "structural__fig.png")

    # 4. scrim — same structural error, but both images are behind a heavy
    #    translucent white overlay. The error is still there; the score is not.
    def scrim(a: np.ndarray) -> np.ndarray:
        return (a * 0.08 + 255 * 0.92).astype(np.uint8)

    save(scrim(base(W * 2, H * 2, 2)), "scrim__ref.png")
    a = base(W, H, 1)
    box(a, 16, 90, 104, 110, (250, 250, 250))
    box(a, 16, 130, 104, 150, (255, 90, 0))
    save(scrim(a), "scrim__fig.png")


if __name__ == "__main__":
    main()
