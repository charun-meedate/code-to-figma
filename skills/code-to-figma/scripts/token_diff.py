#!/usr/bin/env python3
"""Compare token values in code against variable values in Figma — every
value, one at a time.

    python3 token_diff.py --code code-tokens.json --figma figma-dump.json
    python3 token_diff.py --code c.json --figma f.json --map name-map.json

This is the script behind a claim like "138/138 value-exact". Making that claim
by counting is the defect it exists to prevent: two sets can have the same
number of tokens, the same names, and different values, and a count check
passes every time. So does a check that only reads r, g and b — on the proven
run a first pass reported five overlay alphas as missing when every one of
them was present and correct. Alpha is compared here.

Exit code is 0 only when every token in code has a Figma variable with an
identical value. Anything else is non-zero, so this can gate a pipeline.

INPUTS

  --code   {family: {name: {value, file, line}}}   (what extract_tokens.py emits)
           or the flat form {name: value}
  --figma  any of:
           · the plugin API dump: [{name, resolvedType, valuesByMode: {...}}]
           · {"variables": [ ...same... ]}
           · the MCP get_variable_defs shape: {"text/primary": "#1A1A1A"}
  --map    {"explicit": {"codeName": "figma/name"}, "ignore": ["codeName"]}

NAME MAPPING, in order:
  1. an explicit entry in --map                   (always wins)
  2. camelCase → group/kebab-case                 (textPrimaryInverse → text/primary-inverse,
                                                   spacing16 → spacing/16)
  3. loose compare — strip case and separators    (reported as a match that needs
                                                   an explicit entry, never silent)

Provenance: the method proven on the reference programme (dump every variable from Figma, parse
the same values out of the source files, diff by script), made permanent — the
original was written once and thrown away.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERSION = "token_diff/1.0"


# ---------------------------------------------------------------- value model

def norm_color(v) -> str | None:
    """Everything colour-shaped becomes #rrggbbaa lowercase, alpha included."""
    if isinstance(v, dict) and {"r", "g", "b"} <= set(v):
        r, g, b = (round(float(v[k]) * 255) for k in ("r", "g", "b"))
        a = round(float(v.get("a", 1)) * 255)
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
    if not isinstance(v, str):
        return None
    s = v.strip().lower()
    m = re.fullmatch(r"(?:#|0x)([0-9a-f]{3,8})", s)
    if not m:
        m = re.fullmatch(r"(?:const\s+)?color\(0x([0-9a-f]{8})\)", s)
        if not m:
            return None
    h = m.group(1)
    if len(h) == 3:                       # #abc
        h = "".join(c * 2 for c in h) + "ff"
    elif len(h) == 4:                     # #abcd
        h = "".join(c * 2 for c in h)
    elif len(h) == 6:                     # #rrggbb
        h = h + "ff"
    elif len(h) == 8:
        # 0xAARRGGBB (Dart/Android) vs #RRGGBBAA (CSS). A literal written 0x…
        # is alpha-first; one written #… is alpha-last.
        if s.startswith("0x") or s.startswith("color("):
            h = h[2:] + h[:2]
    else:
        return None
    return "#" + h


def norm_number(v) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 4)
    if isinstance(v, str):
        m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*(px|dp|pt|rem|em)?\s*", v)
        if m:
            n = float(m.group(1))
            if m.group(2) == "rem":       # only safe with the default root size
                n *= 16
            return round(n, 4)
    return None


def normalize(v):
    """(kind, value) so a colour never compares equal to a number."""
    c = norm_color(v)
    if c is not None:
        return ("color", c)
    n = norm_number(v)
    if n is not None:
        return ("number", n)
    if isinstance(v, str):
        return ("string", v.strip())
    return ("raw", json.dumps(v, sort_keys=True))


# ----------------------------------------------------------------- name model

_SPLIT = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Za-z])(?=[0-9])|[_\-.\s]+")


def rule_map(code_name: str) -> str:
    parts = [p for p in _SPLIT.split(code_name) if p]
    if not parts:
        return code_name
    group = parts[0].lower()
    rest = "-".join(p.lower() for p in parts[1:])
    return f"{group}/{rest}" if rest else group


def loose(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


# --------------------------------------------------------------- input readers

def read_code(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text())
    out: dict[str, dict] = {}
    nested = any(isinstance(v, dict) and not {"value"} & set(v) for v in raw.values())
    if nested:
        for family, tokens in raw.items():
            if family.startswith("_"):
                continue
            for name, entry in tokens.items():
                value = entry.get("value") if isinstance(entry, dict) else entry
                out[name] = {"value": value, "family": family,
                             "where": (entry or {}).get("file") if isinstance(entry, dict) else None}
    else:
        for name, entry in raw.items():
            if name.startswith("_"):
                continue
            value = entry.get("value") if isinstance(entry, dict) else entry
            out[name] = {"value": value, "family": None, "where": None}
    return out


def read_figma(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text())
    if isinstance(raw, dict) and "variables" in raw:
        raw = raw["variables"]

    if isinstance(raw, list):
        out = {}
        for v in raw:
            name = v.get("name")
            if not name:
                continue
            modes = v.get("valuesByMode") or {}
            if not modes:
                out[name] = v.get("value")
                continue
            if len(modes) > 1:
                # Ambiguous on purpose: pick the first and say so, rather than
                # quietly comparing a dark-mode value against a light token.
                print(f"  note: {name} has {len(modes)} modes; comparing the first", file=sys.stderr)
            out[name] = next(iter(modes.values()))
        return out

    return {k: v for k, v in raw.items() if not k.startswith("_")}


# ------------------------------------------------------------------- the diff

def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--code", required=True, type=Path)
    p.add_argument("--figma", required=True, type=Path)
    p.add_argument("--map", dest="mapfile", type=Path)
    p.add_argument("--quiet-matches", action="store_true")
    args = p.parse_args()

    code = read_code(args.code)
    figma = read_figma(args.figma)
    cfg = json.loads(args.mapfile.read_text()) if args.mapfile else {}
    explicit = cfg.get("explicit", {})
    ignore = set(cfg.get("ignore", []))

    figma_loose = {}
    for k in figma:
        figma_loose.setdefault(loose(k), []).append(k)

    matched, mismatched, missing_figma, loose_hits = [], [], [], []
    used_figma: set[str] = set()

    for name, entry in sorted(code.items()):
        if name in ignore:
            continue
        target, how = None, None
        if name in explicit:
            target, how = explicit[name], "explicit"
        elif (r := rule_map(name)) in figma:
            target, how = r, "rule"
        elif name in figma:
            target, how = name, "verbatim"
        else:
            cands = figma_loose.get(loose(rule_map(name))) or figma_loose.get(loose(name)) or []
            if len(cands) == 1:
                target, how = cands[0], "loose"

        if target is None:
            missing_figma.append(name)
            continue

        used_figma.add(target)
        cv, fv = normalize(entry["value"]), normalize(figma[target])
        if cv == fv:
            matched.append((name, target, cv[1], how))
            if how == "loose":
                loose_hits.append((name, target))
        else:
            mismatched.append((name, target, cv, fv, entry.get("where")))

    missing_code = [k for k in sorted(figma) if k not in used_figma and not k.startswith("_")]

    total = len(matched) + len(mismatched) + len(missing_figma)
    print(f"{VERSION}  code={args.code.name}  figma={args.figma.name}")
    print(f"  compared      : {total} tokens from code against {len(figma)} Figma variables")
    print(f"  value-exact   : {len(matched)}")
    print(f"  MISMATCHED    : {len(mismatched)}")
    print(f"  missing in Figma : {len(missing_figma)}")
    print(f"  extra in Figma   : {len(missing_code)}")

    if mismatched:
        print("\n  MISMATCHED — same name, different value:")
        for name, target, cv, fv, where in mismatched:
            print(f"    {name}  ->  {target}")
            print(f"        code  : {cv[1]}   ({where or 'source unknown'})")
            print(f"        figma : {fv[1]}")
    if missing_figma:
        print("\n  In code, no variable in Figma:")
        for n in missing_figma:
            print(f"    {n}  (expected {rule_map(n)})")
    if missing_code:
        print("\n  In Figma, no token in code — someone drew these by hand, or a family")
        print("  was renamed. Neither is harmless:")
        for n in missing_code:
            print(f"    {n}")
    if loose_hits:
        print("\n  Matched only by loose comparison. Add an explicit entry to the map file")
        print("  so this does not depend on a spelling coincidence:")
        for c, f in loose_hits:
            print(f'    "{c}": "{f}"')
    if matched and not args.quiet_matches and not (mismatched or missing_figma or missing_code):
        print(f"\n  {len(matched)}/{len(matched)} value-exact. Colour comparisons include alpha.")

    ok = not (mismatched or missing_figma or missing_code)
    if not ok:
        print("\n  NOT value-exact. Do not report this as done, and do not report a count —")
        print("  a count is what this script exists to stop you relying on.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
