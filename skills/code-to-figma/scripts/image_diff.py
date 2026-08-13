#!/usr/bin/env python3
"""Compare a Figma frame export against a reference render — by WHERE it
differs, not by how much.

    python3 image_diff.py --ref gallery/screen__state.png --fig export.png
    python3 image_diff.py --ref a.png --fig b.png --scale 2 --out diff.png

The percentage is the least trustworthy number this prints. On the proven run
a frame scored 0.32% while a button sat 320px away from where it belonged: a
translucent scrim covered the whole frame and crushed the contrast of the
difference below the threshold. Any frame with an overlay, a barrier or a
modal will under-report, always.

What to read instead is the band list. A band is a run of consecutive rows
that differ. Then:

    PASS  when every band lies on a row of TEXT — different rasterizers and
          different line-break dictionaries make text rows differ, and that is
          pre-approved (see acceptance-criteria §B).
    FAIL  when a band lies on the edge of a card, a button, an input or an
          image — that is structural drift, at any percentage.

This script never prints PASS or FAIL and its exit code means only "it ran".
The judgement needs eyes on the composite it writes. Open it.

Scores from different versions of a diff script are not comparable. The
version string is printed with every report for exactly that reason: if a
number moves between sessions, check the version before concluding the work
got worse.

Provenance: the diff recipe used on the reference programme (screenshot → LANCZOS
downscale of the @2x reference → numpy per-row band analysis), made permanent.
"""
from __future__ import annotations

import argparse
import sys

VERSION = "image_diff/1.0"

# Where these numbers come from. Change one and every past score becomes
# incomparable, which is why the version string above is printed with them.
#
# THRESHOLD 24/255 — the per-channel difference that counts as a difference.
#   Carried from the proven run. Below roughly this, JPEG-ish artifacts and
#   the two rasterizers' anti-aliasing dominate and every frame looks broken.
# ROW 2% — how much of a row must differ before the row joins a band. Chosen so
#   a single glyph's worth of anti-aliasing does not open a band, while one
#   short differing text row does.
# CONTRAST 160/255 — below this spread, the reference is behind something
#   translucent and the fixed threshold stops meaning anything. A normal UI
#   frame spans far more; the scrim fixture spans 18.
# FLOOR 2 — the escalated threshold never goes below this, or sensor-level
#   noise in a flat colour field becomes a band.
DEFAULT_THRESHOLD = 24
DEFAULT_ROW_THRESHOLD = 2.0
LOW_CONTRAST_SPREAD = 160
MIN_ESCALATED_THRESHOLD = 2

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover - environment problem, not logic
    raise SystemExit("Needs Pillow and numpy:  pip install pillow numpy")


def load_rgb(path: str) -> "Image.Image":
    im = Image.open(path)
    # Flatten transparency onto white; a Figma export is often RGBA and an
    # alpha edge would otherwise read as a difference against an opaque render.
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


def resolve_scale(ref: "Image.Image", fig: "Image.Image", requested: str) -> float:
    if requested != "auto":
        return float(requested)
    if ref.size == fig.size:
        return 1.0
    rw, fw = ref.width, fig.width
    if rw % fw == 0 and ref.height % fig.height == 0 and rw // fw == ref.height // fig.height:
        return float(rw // fw)
    raise SystemExit(
        f"Cannot infer an integer scale: reference {ref.size} vs figma {fig.size}.\n"
        "Pass --scale explicitly, or crop the reference first. A screen whose story\n"
        "overrode the surface size is drawn inside a normal-sized canvas — build the\n"
        "frame at its real size and crop the reference to match, do not stretch either."
    )


def bands(row_pct: "np.ndarray", row_threshold: float) -> list[tuple[int, int, float]]:
    """Merge consecutive differing rows into (y0, y1, peak%) bands."""
    out: list[tuple[int, int, float]] = []
    start = None
    peak = 0.0
    for y, pct in enumerate(row_pct):
        if pct > row_threshold:
            if start is None:
                start, peak = y, pct
            peak = max(peak, pct)
        elif start is not None:
            out.append((start, y - 1, peak))
            start, peak = None, 0.0
    if start is not None:
        out.append((start, len(row_pct) - 1, peak))
    return out


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--ref", required=True, help="reference render (the evidence base image)")
    p.add_argument("--fig", required=True, help="Figma frame export")
    p.add_argument("--scale", default="auto", help="reference scale factor; 'auto' infers it")
    p.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD, help="per-channel difference that counts (0-255)")
    p.add_argument("--row-threshold", type=float, default=DEFAULT_ROW_THRESHOLD, help="%% of a row differing before it is a band")
    p.add_argument("--out", default=None, help="write a composite diff PNG here")
    args = p.parse_args()

    ref, fig = load_rgb(args.ref), load_rgb(args.fig)
    scale = resolve_scale(ref, fig, args.scale)

    if scale != 1.0:
        target = (round(ref.width / scale), round(ref.height / scale))
        ref = ref.resize(target, Image.LANCZOS)

    if ref.size != fig.size:
        raise SystemExit(
            f"Sizes still differ after scaling: reference {ref.size} vs figma {fig.size}.\n"
            "Do not resize one to match the other — find out why they disagree first."
        )

    a = np.asarray(ref, dtype=np.int16)
    b = np.asarray(fig, dtype=np.int16)
    delta = np.abs(a - b)

    def analyse(threshold: int):
        over = delta.max(axis=2) > threshold
        row_pct = over.mean(axis=1) * 100
        return over, bands(row_pct, args.row_threshold)

    over, band_list = analyse(args.threshold)
    mean_abs = float(delta.mean())
    pct_over = float(over.mean() * 100)
    widest = max((y1 - y0 + 1 for y0, y1, _ in band_list), default=0)

    print(f"{VERSION}  scale={scale:g}  size={fig.width}x{fig.height}  threshold={args.threshold}")
    print(f"  mean abs diff : {mean_abs:.2f} / 255")
    print(f"  pixels over   : {pct_over:.2f}%")
    print(f"  bands         : {len(band_list)}")
    for y0, y1, peak in band_list:
        print(f"      y {y0:>4}–{y1:<4}  ({y1 - y0 + 1:>3} rows, peak {peak:.1f}%)")

    # A frame behind a scrim, a barrier or a modal has a compressed dynamic
    # range, so a fixed threshold stops meaning anything: on the proven run a
    # button 320px out of place scored 0.32% for exactly this reason. Measure
    # the reference's own contrast and, when it is low, re-run proportionally.
    # This is the check that turns that failure from "found it by luck" into
    # "the tool says so".
    lum = np.asarray(ref.convert("L"), dtype=np.int16)
    contrast = int(np.percentile(lum, 99) - np.percentile(lum, 1))
    low_contrast = contrast < LOW_CONTRAST_SPREAD
    escalated = None
    if low_contrast:
        scaled = max(MIN_ESCALATED_THRESHOLD, round(args.threshold * contrast / 255))
        if scaled < args.threshold:
            escalated = (scaled,) + analyse(scaled)

    if not band_list:
        print("\n  No differing bands. Still open the images once — a frame that failed to\n"
              "  render at all also produces no bands.")
    else:
        print("\n  PASS only if every band above sits on a row of TEXT.")
        print("  A band on a card, button, input or image edge is structural drift,")
        print("  at any percentage.")

    if low_contrast:
        print(
            f"\n  ⚠ LOW CONTRAST FRAME — the reference spans only {contrast}/255 levels."
            "\n  Something translucent covers it (scrim, barrier, modal, disabled state)."
            "\n  A fixed threshold under-reports here, always."
        )
        if escalated:
            th2, over2, bands2 = escalated
            pct2 = float(over2.mean() * 100)
            print(f"  Re-run at the contrast-scaled threshold {th2}: {pct2:.2f}% over, {len(bands2)} bands")
            for y0, y1, peak in bands2:
                print(f"      y {y0:>4}–{y1:<4}  ({y1 - y0 + 1:>3} rows, peak {peak:.1f}%)")
            hidden = len(bands2) - len(band_list)
            if hidden > 0:
                print(
                    f"\n  ⚠⚠ {hidden} band(s) were INVISIBLE at threshold {args.threshold}."
                    "\n  This is the failure mode that once hid a 320px displacement behind a"
                    "\n  scrim at 0.32%. Judge this frame on the scaled run, not the first one."
                )

    if pct_over < 1.0 and widest >= 0.05 * fig.height:
        print(
            f"\n  ⚠ LOW SCORE, WIDE BAND — {pct_over:.2f}% over {widest} rows."
            "\n  A small number spread over a large area is not a small error."
        )

    print("\n  Scores from different versions of this script are not comparable.")

    if args.out:
        heat = np.zeros_like(a)
        heat[..., 0] = np.where(over, 255, 0)
        blend = (0.6 * b + 0.4 * heat).astype(np.uint8)
        Image.fromarray(blend).save(args.out)
        print(f"  composite     : {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
