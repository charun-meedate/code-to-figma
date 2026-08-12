#!/usr/bin/env python3
"""Insert zero-width spaces at legal line-break points, for scripts Figma
cannot break by itself.

Figma ships no line-break dictionary for Thai, Lao, Khmer or Burmese. Raw text
in those scripts breaks mid-word, which reads as a typo. A zero-width space
(U+200B) marks a legal break point without changing any measured width, so
layout and the image diff are unaffected.

Contract (unchanged from the original this generalizes):
    stdin  : a JSON array of strings
    stdout : a JSON object {original: segmented}, containing ONLY the strings
             that changed
Anything with no character in the target script is passed through untouched,
and a string that already contains ZWSP is left alone, so the script is
idempotent and safe to run over a whole file's worth of copy.

    echo '["…","…"]' | python3 segment_text.py --locale th_TH

Line breaking, not word segmentation. The original used ICU *word*
segmentation and it left a whole class of mismatches open: layout engines
break Thai using ICU *line breaking*, which permits breaks inside what word
segmentation calls one word. On the proven run, paragraphs came out one line
too long and pushed those frames from 1–3% diff to 5–8%. `--words` restores
the old behaviour if you ever need to compare.

DO NOT segment text that is deliberately unbreakable. A fixture that exists to
demonstrate a layout bug loses the bug the moment it gains a break point. Use
this on paragraphs that should wrap, not on single-line text the real product
clips.

Provenance: generalized from poppa-notes/uxui-50/thai_seg.py.
"""
from __future__ import annotations

import argparse
import json
import sys

ZWSP = "​"

# Scripts with no spaces between words, where a layout engine needs a
# dictionary to find break points. CJK is deliberately absent: Figma breaks it
# acceptably without help.
SCRIPT_RANGES = {
    "thai": (0x0E00, 0x0E7F),
    "lao": (0x0E80, 0x0EFF),
    "khmer": (0x1780, 0x17FF),
    "myanmar": (0x1000, 0x109F),
}

LOCALE_SCRIPT = {
    "th": "thai",
    "lo": "lao",
    "km": "khmer",
    "my": "myanmar",
}


def script_for_locale(locale: str) -> str:
    lang = locale.split("_")[0].split("-")[0].lower()
    if lang not in LOCALE_SCRIPT:
        raise SystemExit(
            f"No break-point handling needed (or known) for locale {locale!r}. "
            f"Known: {', '.join(sorted(LOCALE_SCRIPT))}."
        )
    return LOCALE_SCRIPT[lang]


def has_script(s: str, script: str) -> bool:
    lo, hi = SCRIPT_RANGES[script]
    return any(lo <= ord(c) <= hi for c in s)


def _break_points_coreforundation(s: str, locale: str, unit: str) -> list[int]:
    """Break offsets via macOS ICU. No third-party install needed."""
    import CoreFoundation as CF  # noqa: PLC0415  (optional, platform-specific)

    units = {
        "line": CF.kCFStringTokenizerUnitLineBreak,
        "word": CF.kCFStringTokenizerUnitWordBoundary,
    }
    cfs = CF.CFStringCreateWithCString(None, s.encode("utf-8"), CF.kCFStringEncodingUTF8)
    loc = CF.CFLocaleCreate(None, locale)
    tok = CF.CFStringTokenizerCreate(
        None, cfs, CF.CFRangeMake(0, CF.CFStringGetLength(cfs)), units[unit], loc
    )
    offsets = []
    while CF.CFStringTokenizerAdvanceToNextToken(tok) != 0:
        r = CF.CFStringTokenizerGetCurrentTokenRange(tok)
        offsets.append(r.location)
    return offsets


def _break_points_pyicu(s: str, locale: str, unit: str) -> list[int]:
    """Break offsets via PyICU — the cross-platform path."""
    import icu  # noqa: PLC0415  (optional dependency)

    make = icu.BreakIterator.createLineInstance if unit == "line" else icu.BreakIterator.createWordInstance
    bi = make(icu.Locale(locale))
    bi.setText(s)
    return [o for o in bi if 0 < o < len(s)]


def break_points(s: str, locale: str, unit: str) -> list[int]:
    try:
        return _break_points_pyicu(s, locale, unit)
    except ImportError:
        pass
    if sys.platform == "darwin":
        try:
            return _break_points_coreforundation(s, locale, unit)
        except ImportError:
            pass
    raise SystemExit(
        "No ICU break iterator available.\n"
        "  macOS : should have worked via CoreFoundation — check that pyobjc-core is present\n"
        "  other : pip install PyICU\n"
        "Do not fall back to a hand-written rule. A wrong break point looks like a typo "
        "in a design review and nobody will know it came from here."
    )


def segment(s: str, locale: str, script: str, unit: str) -> str:
    if not has_script(s, script):
        return s
    if ZWSP in s:
        return s

    out, prev = "", 0
    for offset in break_points(s, locale, unit):
        if offset <= prev or offset >= len(s):
            continue
        out += s[prev:offset]
        # Never stack a ZWSP on top of an existing break opportunity.
        if out and out[-1] not in (" ", "\n", "\t", ZWSP):
            out += ZWSP
        prev = offset
    return out + s[prev:]


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--locale", default="th_TH", help="ICU locale, e.g. th_TH, lo_LA, km_KH, my_MM")
    p.add_argument(
        "--words",
        action="store_true",
        help="use word segmentation instead of line breaking (the old, coarser behaviour)",
    )
    p.add_argument("--all", action="store_true", help="emit every string, not only the changed ones")
    args = p.parse_args()

    script = script_for_locale(args.locale)
    unit = "word" if args.words else "line"

    src = json.load(sys.stdin)
    if not isinstance(src, list):
        raise SystemExit("stdin must be a JSON array of strings")

    out = {s: segment(s, args.locale, script, unit) for s in src}
    if not args.all:
        out = {k: v for k, v in out.items() if k != v}
    json.dump(out, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
