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
  --map    {"explicit":    {"codeName": "figma/name"},
            "ignore":      ["codeName"],        code-side: not expected in Figma
            "ignoreFigma": ["prefix/*"]}        Figma-side: variables this programme
                                                does not own. Needed whenever the file
                                                already holds variables — e.g. an org
                                                library — or the gate can never pass.

NAME MAPPING, in order:
  1. an explicit entry in --map                   (always wins)
  2. the family-qualified name, then the bare one (spacing.sm → spacing/sm, then sm)
  3. camelCase → group/leaf                       (textPrimaryInverse → text/primary-inverse)
     already-separated → every separator a slash  (color-text-primary → color/text/primary)
  4. loose compare — strip case and separators    (reported as a match that needs
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

def _hsl_to_rgb(h: float, s: float, light: float) -> tuple[int, int, int]:
    c = (1 - abs(2 * light - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = light - c / 2
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60) % 6]
    return tuple(round((v + m) * 255) for v in (r, g, b))


def norm_color(v) -> str | None:
    """Everything colour-shaped becomes #rrggbbaa lowercase, alpha included.

    Hex alone is not enough. Real token files ship rgb()/rgba()/hsl(), and a
    bare HSL triplet is how the most widely copied web token setup writes every
    colour. Anything not understood here comes back None and is reported as
    unsupported — never as a mismatch, which would send someone off to "fix" a
    Figma variable that was correct.
    """
    if isinstance(v, dict) and {"r", "g", "b"} <= set(v):
        r, g, b = (round(float(v[k]) * 255) for k in ("r", "g", "b"))
        a = round(float(v.get("a", 1)) * 255)
        return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
    if not isinstance(v, str):
        return None
    s = v.strip().lower()

    # rgb()/rgba()/hsl()/hsla(), comma- or space-separated, with optional /alpha
    fn = re.fullmatch(r"(rgba?|hsla?)\(([^)]+)\)", s)
    if fn:
        parts = re.split(r"[,\s/]+", fn.group(2).strip())
        nums = []
        for p in parts:
            if not p:
                continue
            pct = p.endswith("%")
            try:
                n = float(p.rstrip("%"))
            except ValueError:
                return None
            nums.append((n, pct))
        if len(nums) not in (3, 4):
            return None
        a = 1.0
        if len(nums) == 4:
            a = nums[3][0] / 100 if nums[3][1] else nums[3][0]
        if fn.group(1).startswith("rgb"):
            r, g, b = (round(n * 255 / 100) if pct else round(n) for n, pct in nums[:3])
        else:
            r, g, b = _hsl_to_rgb(nums[0][0], nums[1][0] / 100, nums[2][0] / 100)
        return f"#{r:02x}{g:02x}{b:02x}{round(a * 255):02x}"

    # A bare HSL triplet — how shadcn-style setups store colours.
    triplet = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)%\s+(-?\d+(?:\.\d+)?)%", s)
    if triplet:
        r, g, b = _hsl_to_rgb(float(triplet.group(1)), float(triplet.group(2)) / 100,
                              float(triplet.group(3)) / 100)
        return f"#{r:02x}{g:02x}{b:02x}ff"

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


_ALREADY_SEPARATED = re.compile(r"[-_.]")


def rule_map(code_name: str) -> str:
    """Map a code token name onto a Figma slash-grouped name.

    Two conventions, because they mean different things. camelCase carries one
    implicit boundary — the first hump is the group and the rest is the leaf
    (`textPrimaryInverse` -> `text/primary-inverse`). A name that is ALREADY
    separated states its own hierarchy, so every separator becomes a slash
    (`color-text-primary` -> `color/text/primary`, which is what the web
    playbook promises). Collapsing the second case to one slash left every web
    token matching only by loose comparison, i.e. the rule path contributed
    nothing off camelCase.
    """
    if _ALREADY_SEPARATED.search(code_name):
        parts = [p for p in re.split(r"[-_.\s]+", code_name) if p]
        return "/".join(p.lower() for p in parts)
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
    """Load code tokens, keyed so two families cannot silently eat each other.

    `sm`, `md` and `lg` recur across spacing, radius, shadow and font-size on
    almost every web project. Keying on the bare name meant the second family
    overwrote the first and the report then counted what survived — a silent
    loss inside the one script whose whole job is to stop a count from standing
    in for a comparison. The key is now family-qualified; matching still tries
    the bare name, so nothing that worked before stops working.
    """
    raw = json.loads(path.read_text())
    out: dict[str, dict] = {}
    nested = any(isinstance(v, dict) and not {"value"} & set(v) for v in raw.values())
    if nested:
        for family, tokens in raw.items():
            if family.startswith("_"):
                continue
            for name, entry in tokens.items():
                value = entry.get("value") if isinstance(entry, dict) else entry
                key = f"{family}.{name}"
                if key in out:
                    raise SystemExit(f"{key} declared twice in {path.name} — refusing to guess which wins.")
                out[key] = {
                    "value": value,
                    "family": family,
                    "bare": name,
                    "where": (entry or {}).get("file") if isinstance(entry, dict) else None,
                }
    else:
        for name, entry in raw.items():
            if name.startswith("_"):
                continue
            value = entry.get("value") if isinstance(entry, dict) else entry
            out[name] = {"value": value, "family": None, "bare": name, "where": None}
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

    matched, mismatched, missing_figma, loose_hits, unsupported = [], [], [], [], []
    used_figma: set[str] = set()

    for key, entry in sorted(code.items()):
        bare = entry.get("bare", key)
        if key in ignore or bare in ignore:
            continue
        # Try the family-qualified name first (spacing.sm -> spacing/sm), then
        # the bare one, so a flat Figma naming still matches.
        candidates_src = [key, bare] if bare != key else [key]
        target, how = None, None
        for cand in candidates_src:
            if cand in explicit:
                target, how = explicit[cand], "explicit"
                break
            if (r := rule_map(cand)) in figma:
                target, how = r, "rule"
                break
            if cand in figma:
                target, how = cand, "verbatim"
                break
        if target is None:
            for cand in candidates_src:
                cands = figma_loose.get(loose(rule_map(cand))) or figma_loose.get(loose(cand)) or []
                if len(cands) == 1:
                    target, how = cands[0], "loose"
                    break

        if target is None:
            missing_figma.append(key)
            continue

        used_figma.add(target)
        cv, fv = normalize(entry["value"]), normalize(figma[target])
        # If EITHER side did not parse into a comparable type, the two cannot be
        # compared at all — an unresolved DTCG alias, a var() reference or a
        # composite token against a real colour. Calling that a mismatch sends
        # someone off to change a Figma variable that was correct.
        unresolved = cv[0] in ("string", "raw") or fv[0] in ("string", "raw")
        if cv == fv:
            matched.append((key, target, cv[1], how))
            if how == "loose":
                loose_hits.append((key, target))
        elif unresolved:
            unsupported.append((key, target, cv[1], fv[1]))
        else:
            mismatched.append((key, target, cv, fv, entry.get("where")))

    ignore_figma = cfg.get("ignoreFigma", [])
    def waived(name: str) -> bool:
        return any(name == p or name.startswith(p.rstrip("*")) for p in ignore_figma)

    missing_code = [k for k in sorted(figma)
                    if k not in used_figma and not k.startswith("_") and not waived(k)]
    waived_figma = [k for k in sorted(figma) if k not in used_figma and waived(k)]

    total = len(matched) + len(mismatched) + len(missing_figma) + len(unsupported)
    print(f"{VERSION}  code={args.code.name}  figma={args.figma.name}")
    print(f"  in code       : {len(code)} tokens  (compared: {total})")
    print(f"  value-exact   : {len(matched)}")
    print(f"  MISMATCHED    : {len(mismatched)}")
    print(f"  uncomparable  : {len(unsupported)}")
    print(f"  missing in Figma : {len(missing_figma)}")
    print(f"  extra in Figma   : {len(missing_code)}" + (f"  ({len(waived_figma)} waived)" if waived_figma else ""))

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
    if unsupported:
        print("\n  UNCOMPARABLE — neither side parses into a comparable value. Usually a")
        print("  DTCG alias ({color.brand.500}), a composite token, or a var() reference.")
        print("  Resolve these before the diff; do NOT read them as mismatches:")
        for key, target, cv, fv in unsupported:
            print(f"    {key}  ->  {target}\n        code : {cv}\n        figma: {fv}")
    if loose_hits:
        print("\n  Matched only by loose comparison. Add an explicit entry to the map file")
        print("  so this does not depend on a spelling coincidence:")
        for c, f in loose_hits:
            print(f'    "{c}": "{f}"')
    if matched and not args.quiet_matches and not (mismatched or missing_figma or missing_code):
        print(f"\n  {len(matched)}/{len(matched)} value-exact. Colour comparisons include alpha.")

    ok = not (mismatched or missing_figma or missing_code or unsupported)
    if not ok:
        print("\n  NOT value-exact. Do not report this as done, and do not report a count —")
        print("  a count is what this script exists to stop you relying on.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
