#!/usr/bin/env python3
"""Pull design-token names and values out of source code, into the canonical
JSON that token_diff.py compares against Figma.

    python3 extract_tokens.py --config tokens-extract.json --root ~/dev/my-app
    python3 extract_tokens.py --config c.json --root . --out code-tokens.json
    python3 extract_tokens.py --list-presets

The config is a small map of families to sources. Each source names either a
built-in preset or its own regex, so a stack nobody has written a playbook for
is still one confirmed regex away from working:

{
  "color": [
    { "glob": "lib/tokens/*.dart", "preset": "dart-color" }
  ],
  "spacing": [
    { "glob": "lib/tokens/app_dimens.dart", "preset": "dart-double" }
  ],
  "typography": [
    { "glob": "src/theme.ts", "pattern": "(?P<name>\\\\w+):\\\\s*'(?P<value>[^']+)'" }
  ]
}

A custom `pattern` must have named groups `name` and `value`. Optional keys:

  nameFilter    a regex the raw name must match. One CSS file or one theme
                object usually holds every family at once, so this is how you
                split them: "^color-" for colour, "^(spacing|radius)-" for
                numbers. Applied BEFORE prefixStrip.
  between       ["startRegex", "endRegex"] — read only the text between them.
                Light and dark schemes normally live in one file under the
                same token names, so without this you silently get whichever
                appears first. Pass the end regex as "" to read to the end.
  prefixStrip   drop a leading string from every name after filtering
  skip          names to leave out — be able to justify each one

WHAT THIS DELIBERATELY DOES NOT DO

It does not guess. If a family has no source in the config, it is reported as
absent and that absence is a finding to write down — on the proven run the
product had no shadow-token layer at all, with shadows written inline across
twenty files. The correct output there was "absent, here is the evidence",
never a set of plausible shadow values invented to fill the gap.

Provenance: generalizes the regex-per-family parameterization used by the
token drift test on the proven run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERSION = "extract_tokens/1.0"

PRESETS: dict[str, dict[str, str]] = {
    "dart-color": {
        "pattern": r"(?P<name>\w+)\s*:\s*(?:const\s+)?Color\(\s*(?P<value>0x[0-9A-Fa-f]{8})\s*\)",
        "about": "Dart: `textPrimary: Color(0xFF1A1A1A)` inside a ThemeExtension constructor call",
    },
    "dart-double": {
        "pattern": r"(?P<name>\w+)\s*:\s*(?P<value>-?\d+(?:\.\d+)?)\s*[,)]",
        "about": "Dart: `spacing16: 16,` — spacing, sizes and radii usually share one file",
    },
    "css-custom-property": {
        "pattern": r"--(?P<name>[\w-]+)\s*:\s*(?P<value>[^;]+);",
        "about": "CSS/SCSS: `--text-primary: #1a1a1a;` in a :root block",
    },
    "js-object-string": {
        "pattern": r"['\"]?(?P<name>[\w-]+)['\"]?\s*:\s*['\"](?P<value>#[0-9a-fA-F]{3,8}|[^'\"]+)['\"]",
        "about": "FLAT JS/TS theme object only: `textPrimary: '#1A1A1A'`. A NESTED object "
                 "(tailwind, MUI, Chakra) loses its key path — dump the resolved theme to JSON instead",
    },
    "js-object-number": {
        "pattern": r"['\"]?(?P<name>[\w-]+)['\"]?\s*:\s*(?P<value>-?\d+(?:\.\d+)?)\s*[,}]",
        "about": "FLAT JS/TS theme object only: `spacing16: 16,`",
    },
    "swift-color": {
        "pattern": r"static\s+let\s+(?P<name>\w+)\s*(?::\s*Color)?\s*=\s*Color\((?P<value>[^()]*(?:\([^()]*\)[^()]*)*)\)",
        "about": "SwiftUI: `static let textPrimary = Color(red:green:blue:)`. Color(\"Name\") is an "
                 "asset-catalogue reference, not a value — read the xcassets JSON for those",
    },
    "compose-color": {
        "pattern": r"val\s+(?P<name>\w+)\s*(?::\s*Color)?\s*=\s*Color\(\s*(?P<value>0x[0-9A-Fa-f]{8})\s*\)",
        "about": "Compose: `val TextPrimary = Color(0xFF1A1A1A)`",
    },
    "dtcg-json": {
        "format": "json",
        "about": "W3C DTCG tokens.json — walks the tree and reads every $value",
    },
    "json-tree": {
        "format": "json-tree",
        "about": "Any nested theme dumped to JSON (tailwind/MUI/Chakra) — joins the key "
                 "path with '/'. This is what a nested object needs instead of a regex",
    },
}


def walk_tree(node, trail: list[str], out: dict, file: str) -> None:
    """Walk a plain nested theme object, joining the key path.

    A regex over a nested object keeps only the leaf key, so `brand.500` and
    `accent.500` collide and one is lost. The path is the identity here.

    Arrays are a Tailwind convention rather than a value: `fontSize` entries are
    [size, lineHeight] or [size, {lineHeight, letterSpacing}]. Both parts are
    real tokens, so both are emitted rather than the second being dropped.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            walk_tree(v, trail + [str(k)], out, file)
    elif isinstance(node, list):
        if node:
            walk_tree(node[0], trail, out, file)
        for extra in node[1:]:
            if isinstance(extra, dict):
                for k, v in extra.items():
                    walk_tree(v, trail + [str(k)], out, file)
            else:
                walk_tree(extra, trail + ["line-height"], out, file)
    else:
        out["/".join(trail)] = {"value": node, "file": file, "line": None}


def walk_dtcg(node, trail: list[str], out: dict, file: str) -> None:
    if isinstance(node, dict):
        if "$value" in node:
            out["/".join(trail)] = {"value": node["$value"], "file": file, "line": None}
            return
        for k, v in node.items():
            if k.startswith("$"):
                continue
            walk_dtcg(v, trail + [k], out, file)


def extract_source(root: Path, src: dict, family: str) -> dict:
    preset_name = src.get("preset")
    preset = PRESETS.get(preset_name, {}) if preset_name else {}
    if preset_name and not preset:
        raise SystemExit(f"Unknown preset {preset_name!r}. Run --list-presets.")

    pattern = src.get("pattern") or preset.get("pattern")
    fmt = src.get("format") or preset.get("format") or "regex"
    if fmt == "regex" and not pattern:
        raise SystemExit(f"[{family}] source needs a `preset` or a `pattern`.")

    prefix_strip = src.get("prefixStrip")
    name_filter = re.compile(src["nameFilter"]) if src.get("nameFilter") else None
    skip = set(src.get("skip", []))
    found: dict[str, dict] = {}

    paths = sorted(root.glob(src["glob"]))
    if not paths:
        print(f"  ⚠ [{family}] no file matched {src['glob']}", file=sys.stderr)

    for path in paths:
        rel = str(path.relative_to(root))
        text = path.read_text(errors="replace")
        offset = 0

        if bounds := src.get("between"):
            start_rx, end_rx = bounds[0], (bounds[1] if len(bounds) > 1 else "")
            m0 = re.search(start_rx, text)
            if not m0:
                raise SystemExit(
                    f"[{family}] `between` start pattern {start_rx!r} not found in {rel}. "
                    "Do not drop the bound and take the whole file — that silently mixes modes."
                )
            offset = m0.end()
            rest = text[offset:]
            if end_rx:
                m1 = re.search(end_rx, rest)
                if not m1:
                    raise SystemExit(
                        f"[{family}] `between` end pattern {end_rx!r} not found after the start "
                        f"in {rel}. Falling back to the rest of the file would silently mix modes, "
                        "which is what this option exists to prevent. Fix the pattern, or pass \"\" "
                        "to read to the end deliberately."
                    )
                rest = rest[: m1.start()]
            text = rest

        if fmt == "json":
            walk_dtcg(json.loads(text), [], found, rel)
            continue

        if fmt == "json-tree":
            root = json.loads(text)
            for key in (src.get("rootKey") or "").split("."):
                if key:
                    root = root[key]
            walk_tree(root, [], found, rel)
            continue

        rx = re.compile(pattern)
        for m in rx.finditer(text):
            name = m.group("name")
            if name_filter and not name_filter.search(name):
                continue
            if prefix_strip and name.startswith(prefix_strip):
                name = name[len(prefix_strip):]
                name = name[0].lower() + name[1:] if name else name
            if name in skip:
                continue
            line = path.read_text(errors="replace").count("\n", 0, offset + m.start()) + 1
            value = m.group("value").strip()
            if re.fullmatch(r"[\"'].*[\"']", value):
                print(f"  ⚠ [{family}] {name} = {value} is a NAME, not a value — probably an "
                      f"asset-catalogue reference ({rel}:{line}). Read that catalogue instead.",
                      file=sys.stderr)
            if name in found:
                # Not harmless dedup: with a leaf-key regex on a nested object this
                # is silent data loss, and the diff downstream reports a partial set
                # as a clean comparison.
                print(f"  ⚠ [{family}] {name} declared twice — {found[name]['file']}:"
                      f"{found[name]['line']} and {rel}:{line}. Taking the first.\n"
                      f"      Usually one of two causes: the file holds LIGHT AND DARK under the "
                      f"same names (bound it with `between`, or you silently get one mode), or the "
                      f"source is a NESTED object and the pattern is losing the key path (dump the "
                      f"resolved theme to JSON and walk it instead).", file=sys.stderr)
                continue
            found[name] = {"value": value, "file": rel, "line": line}

    return found


_REF = re.compile(r"^\s*(?:var\(\s*--([\w-]+)\s*\)|\{([\w.-]+)\})\s*$")


def resolve_aliases(result: dict, rounds: int = 8) -> tuple[int, list[str]]:
    """Follow `var(--x)` and `{a.b.c}` references to the value they end at.

    A semantic layer that aliases a primitive is the normal shape of a modern
    design system, not an edge case — on two real web codebases the majority of
    extracted entries were references rather than values. Left unresolved they
    are uncomparable, so the tokens tier reports most of itself as unverifiable.

    Matching is by last path segment as well as full name, because the alias
    writes the CSS custom-property name (`--primary-default`) while the entry
    may be filed under a path (`colors/primary/default`).
    """
    # Index concrete values BEFORE references. A path-named entry aliases onto
    # the same key as the primitive it points at — `colors/primary/DEFAULT`
    # normalizes to `primary-default`, which is exactly the custom property it
    # references. Indexed in file order it claims that key and then resolves to
    # itself, so every alias in the file silently stays unresolved.
    index: dict[str, tuple[str, str]] = {}
    for concrete_pass in (True, False):
        for family, tokens in result.items():
            for name, entry in tokens.items():
                v = entry["value"]
                is_ref = isinstance(v, str) and bool(_REF.match(v))
                if is_ref == concrete_pass:
                    continue
                for key in {name, name.split("/")[-1], name.replace("/", "-"), name.replace("/", ".")}:
                    index.setdefault(key.lower(), (family, name))

    unresolved: list[str] = []
    resolved = 0
    for _ in range(rounds):
        changed = 0
        for family, tokens in result.items():
            for name, entry in tokens.items():
                v = entry["value"]
                if not isinstance(v, str):
                    continue
                m = _REF.match(v)
                if not m:
                    continue
                ref = (m.group(1) or m.group(2) or "").lower()
                hit = index.get(ref) or index.get(ref.replace(".", "-")) or index.get(ref.split(".")[-1])
                if not hit or hit == (family, name):
                    continue
                target = result[hit[0]][hit[1]]["value"]
                if isinstance(target, str) and _REF.match(target):
                    continue  # still a reference; another round will get it
                entry["value"] = target
                entry["aliasOf"] = ref
                changed += 1
        resolved += changed
        if not changed:
            break

    for family, tokens in result.items():
        for name, entry in tokens.items():
            if isinstance(entry["value"], str) and _REF.match(entry["value"]):
                unresolved.append(f"{family}/{name} -> {entry['value']}")
    return resolved, unresolved


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--config", type=Path)
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--out", type=Path)
    p.add_argument("--resolve-aliases", action="store_true",
                   help="follow var(--x) / {a.b.c} references to their end value")
    p.add_argument("--list-presets", action="store_true")
    args = p.parse_args()

    if args.list_presets:
        print(f"{VERSION} presets:")
        for name, spec in PRESETS.items():
            print(f"  {name:<22} {spec['about']}")
        print("\nNone fitting? Write a `pattern` with named groups (?P<name>…) and (?P<value>…),")
        print("run this, and check the count and five samples against the file before trusting it.")
        return 0

    if not args.config:
        raise SystemExit("--config is required (or --list-presets)")

    config = json.loads(args.config.read_text())
    result: dict[str, dict] = {}
    absent: list[str] = []

    for family, sources in config.items():
        if family.startswith("_"):
            continue
        if not sources:
            absent.append(family)
            continue
        merged: dict[str, dict] = {}
        for src in sources:
            merged.update(extract_source(args.root, src, family))
        if merged:
            result[family] = merged
        else:
            absent.append(family)

    alias_note = ""
    if args.resolve_aliases:
        n, unresolved = resolve_aliases(result)
        alias_note = f"  resolved {n} alias reference(s)"
        if unresolved:
            alias_note += f"; {len(unresolved)} still unresolved"

    total = sum(len(v) for v in result.values())
    print(f"{VERSION}  root={args.root}")
    if alias_note:
        print(alias_note)
        if args.resolve_aliases and unresolved:
            print("  UNRESOLVED — the target is not in any configured source. Add the file that")
            print("  defines it, or these stay uncomparable:")
            for u in unresolved[:10]:
                print(f"    {u}")
            if len(unresolved) > 10:
                print(f"    … and {len(unresolved) - 10} more")
    for family, tokens in result.items():
        files = sorted({t["file"] for t in tokens.values()})
        print(f"  {family:<14} {len(tokens):>4}  from {', '.join(files)}")
        for name in list(tokens)[:5]:
            print(f"       e.g. {name} = {tokens[name]['value']}")
    print(f"  {'TOTAL':<14} {total:>4}")

    if absent:
        print("\n  Families with no tokens found: " + ", ".join(absent))
        print("  Before adding a source, check whether the family exists in the product at")
        print("  all. A family that is genuinely absent is a FINDING to record with its")
        print("  evidence — not a gap to fill with invented values.")

    print("\n  Check the count and the samples above against the source before using this.")

    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(payload + "\n")
        print(f"  wrote {args.out}")
    else:
        print()
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
