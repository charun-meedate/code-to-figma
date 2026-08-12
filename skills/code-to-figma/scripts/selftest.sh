#!/usr/bin/env bash
# Hermetic checks for the code-to-figma skill. No Figma, no network, no project.
#
#   ./selftest.sh
#
# Every assertion below corresponds to a failure that actually happened on the
# programme this skill generalizes. If one goes red, read the case it names
# before changing the test.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$(cd "$HERE/.." && pwd)"
FIX="$HERE/fixtures"
PASS=0; FAIL=0; SKIP=0

ok()   { printf '  \033[32mok\033[0m   %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[31mFAIL\033[0m %s\n     %s\n' "$1" "${2:-}"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[33mskip\033[0m %s — %s\n' "$1" "$2"; SKIP=$((SKIP+1)); }
head_() { printf '\n\033[1m%s\033[0m\n' "$1"; }

py() { python3 "$@" 2>&1; }

# --------------------------------------------------------------- segment_text
head_ "segment_text.py — non-space-delimited scripts"

if ! python3 -c "import icu" 2>/dev/null && [[ "$OSTYPE" != darwin* ]]; then
  skip "segmentation" "no ICU break iterator (macOS, or pip install PyICU)"
else
  OUT=$(echo '["ออกไป"]' | py "$HERE/segment_text.py" --locale th_TH)
  if [[ "$OUT" == *$'​'* ]]; then
    ok "line breaking finds the break inside ออกไป (the C14 regression)"
  else
    bad "line breaking finds the break inside ออกไป" \
        "got: $OUT — word segmentation treats ออกไป as one word; line breaking must not. This is the fix that closed a whole deviation class."
  fi

  OUT=$(echo '["ออกไป"]' | py "$HERE/segment_text.py" --locale th_TH --words)
  [[ "$OUT" == "{}" ]] \
    && ok "--words reproduces the old, coarser behaviour (no break found)" \
    || bad "--words reproduces the old behaviour" "got: $OUT"

  OUT=$(echo '["hello world"]' | py "$HERE/segment_text.py" --locale th_TH)
  [[ "$OUT" == "{}" ]] \
    && ok "text with no Thai passes through untouched" \
    || bad "text with no Thai passes through untouched" "got: $OUT"

  ONCE=$(echo '["สวัสดีชาวโลก"]' | py "$HERE/segment_text.py" --locale th_TH | python3 -c 'import json,sys;print(list(json.load(sys.stdin).values())[0])')
  TWICE=$(python3 -c "import json,sys;print(json.dumps(['$ONCE']))" | py "$HERE/segment_text.py" --locale th_TH)
  [[ "$TWICE" == "{}" ]] \
    && ok "idempotent — already-segmented text is left alone" \
    || bad "idempotent" "second pass changed it again: $TWICE"
fi

# ------------------------------------------------------------------ image_diff
head_ "image_diff.py — where it differs, not how much"

if ! python3 -c "import numpy, PIL" 2>/dev/null; then
  skip "image diff" "needs pillow and numpy"
else
  [[ -f "$FIX/identical__ref.png" ]] || py "$FIX/make_image_fixtures.py" >/dev/null

  OUT=$(py "$HERE/image_diff.py" --ref "$FIX/identical__ref.png" --fig "$FIX/identical__fig.png")
  echo "$OUT" | grep -q "bands *: 0" \
    && ok "identical pair reports no bands (and infers the @2x scale)" \
    || bad "identical pair reports no bands" "$OUT"

  OUT=$(py "$HERE/image_diff.py" --ref "$FIX/textband__ref.png" --fig "$FIX/textband__fig.png")
  echo "$OUT" | grep -q "bands *: 1" \
    && ok "a differing text row produces exactly one band" \
    || bad "a differing text row produces one band" "$OUT"

  OUT=$(py "$HERE/image_diff.py" --ref "$FIX/structural__ref.png" --fig "$FIX/structural__fig.png")
  echo "$OUT" | grep -q "bands *: 2" \
    && ok "a displaced element produces bands at both positions" \
    || bad "a displaced element produces two bands" "$OUT"

  # The one that matters: the same displacement hidden behind a scrim scores
  # 0.00% at the default threshold. Judged on the number alone it passes.
  OUT=$(py "$HERE/image_diff.py" --ref "$FIX/scrim__ref.png" --fig "$FIX/scrim__fig.png")
  echo "$OUT" | grep -q "LOW CONTRAST FRAME" \
    && ok "low-contrast frame is detected" \
    || bad "low-contrast frame is detected" "$OUT"
  echo "$OUT" | grep -q "were INVISIBLE at threshold" \
    && ok "the escalated run surfaces bands the default threshold missed (the 0.32%/320px case)" \
    || bad "escalation surfaces the hidden bands" "$OUT"

  OUT=$(py "$HERE/image_diff.py" --ref "$FIX/identical__ref.png" --fig "$FIX/identical__fig.png")
  echo "$OUT" | grep -q "LOW CONTRAST" \
    && bad "no false low-contrast alarm on a normal frame" "$OUT" \
    || ok "no false low-contrast alarm on a normal frame"
fi

# ------------------------------------------------------------------ token_diff
head_ "token_diff.py — every value, never a count"

py "$HERE/token_diff.py" --code "$FIX/code-tokens.json" --figma "$FIX/figma-dump.json" >/dev/null
[[ $? -eq 0 ]] \
  && ok "a value-exact set exits 0" \
  || bad "a value-exact set exits 0" "$(py "$HERE/token_diff.py" --code "$FIX/code-tokens.json" --figma "$FIX/figma-dump.json")"

OUT=$(py "$HERE/token_diff.py" --code "$FIX/code-tokens.json" --figma "$FIX/figma-dump-count-trap.json")
RC=$?
[[ $RC -ne 0 ]] \
  && ok "THE COUNT TRAP — same token count, wrong values, exits non-zero" \
  || bad "the count trap exits non-zero" "$OUT"
echo "$OUT" | grep -q "spacing16" \
  && ok "the numeric mismatch is named with both values" \
  || bad "the numeric mismatch is named" "$OUT"
echo "$OUT" | grep -q "overlayScrim" \
  && ok "a lost alpha channel is caught (r,g,b were identical)" \
  || bad "a lost alpha channel is caught" "$OUT"

# Findings from the adversarial audit, 2026-08-13. Each of these was a real
# defect in this script; they are locked down here so they cannot come back.
python3 - "$HERE" <<'PY' && ok "audit: family-qualified keys — two families sharing a leaf name no longer eat each other" || bad "family collision" "spacing.sm and radius.sm collapsed to one token — silent loss in the script that exists to stop counts standing in for comparisons"
import sys, json, tempfile, os, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("td", sys.argv[1] + "/token_diff.py")
td = importlib.util.module_from_spec(spec); spec.loader.exec_module(td)
p = tempfile.mktemp(suffix=".json")
open(p, "w").write(json.dumps({"spacing": {"sm": {"value": "8px"}}, "radius": {"sm": {"value": "4px"}}}))
n = len(td.read_code(Path(p))); os.remove(p)
sys.exit(0 if n == 2 else 1)
PY

python3 - "$HERE" <<'PY' && ok "audit: already-separated names map every separator to a slash" || bad "rule_map on kebab/dot" "color-text-primary must become color/text/primary, as stacks/web.md promises"
import sys, importlib.util
spec = importlib.util.spec_from_file_location("td", sys.argv[1] + "/token_diff.py")
td = importlib.util.module_from_spec(spec); spec.loader.exec_module(td)
sys.exit(0 if (td.rule_map("color-text-primary") == "color/text/primary"
               and td.rule_map("color.text.primary") == "color/text/primary"
               and td.rule_map("textPrimaryInverse") == "text/primary-inverse"
               and td.rule_map("spacing16") == "spacing/16") else 1)
PY

python3 - "$HERE" <<'PY' && ok "audit: rgb() / rgba() / hsl() / bare-HSL all normalize like hex" || bad "colour formats" "web token files are mostly not hex; unparsed values were being reported as mismatches"
import sys, importlib.util
spec = importlib.util.spec_from_file_location("td", sys.argv[1] + "/token_diff.py")
td = importlib.util.module_from_spec(spec); spec.loader.exec_module(td)
ok = (td.normalize("rgb(59,110,245)") == td.normalize("#3b6ef5")
      and td.normalize("rgba(26,26,26,0.48)")[0] == "color"
      and td.normalize("hsl(220 90% 60%)")[0] == "color"
      and td.normalize("220 90% 60%")[0] == "color")
sys.exit(0 if ok else 1)
PY

TMP=$(mktemp -d)
echo '{"color":{"brand":{"value":"{color.base.500}"}}}' > "$TMP/code.json"
echo '{"color/brand":"#ff0000"}' > "$TMP/figma.json"
OUT=$(py "$HERE/token_diff.py" --code "$TMP/code.json" --figma "$TMP/figma.json")
echo "$OUT" | grep -q "UNCOMPARABLE" \
  && ok "audit: an unresolved DTCG alias is 'uncomparable', not a mismatch" \
  || bad "uncomparable bucket" "calling an alias a mismatch sends someone to change a correct Figma variable:
$OUT"

echo '{"color":{"brand":{"value":"#ff0000"}}}' > "$TMP/code.json"
echo '{"color/brand":"#ff0000","legacy/old":"#00ff00"}' > "$TMP/figma.json"
py "$HERE/token_diff.py" --code "$TMP/code.json" --figma "$TMP/figma.json" >/dev/null
[[ $? -ne 0 ]] && ok "audit: an unowned Figma variable fails the gate by default" || bad "extra-in-figma fails" ""
echo '{"ignoreFigma":["legacy/"]}' > "$TMP/map.json"
py "$HERE/token_diff.py" --code "$TMP/code.json" --figma "$TMP/figma.json" --map "$TMP/map.json" >/dev/null
[[ $? -eq 0 ]] \
  && ok "audit: ignoreFigma waives it explicitly, so a pre-existing library does not block P1 forever" \
  || bad "ignoreFigma waiver" ""
rm -rf "$TMP"

TMP=$(mktemp -d)
printf 'static let legacy = Color(UIColor(red: 0.1, green: 0.2, alpha: 1.0))\n' > "$TMP/C.swift"
echo '{"color":[{"glob":"*.swift","preset":"swift-color"}]}' > "$TMP/cfg.json"
OUT=$(py "$HERE/extract_tokens.py" --config "$TMP/cfg.json" --root "$TMP")
echo "$OUT" | grep -q "alpha: 1.0" \
  && ok "audit: swift-color balances nested parens instead of truncating the value" \
  || bad "swift-color truncation" "$OUT"
rm -rf "$TMP"

# 0xAARRGGBB from code must equal #RRGGBBAA from Figma.
python3 - "$HERE" <<'PY' && ok "0xAARRGGBB and Figma rgba normalize to the same value" || bad "alpha-first vs alpha-last normalization" "see token_diff.norm_color"
import sys, importlib.util
spec = importlib.util.spec_from_file_location("td", sys.argv[1] + "/token_diff.py")
td = importlib.util.module_from_spec(spec); spec.loader.exec_module(td)
a = td.normalize("0x1AFF5900")
b = td.normalize({"r": 1, "g": 0.34902, "b": 0, "a": 0.10196})
sys.exit(0 if a == b else 1)
PY

# --------------------------------------------------------------- extract_tokens
head_ "extract_tokens.py"

py "$HERE/extract_tokens.py" --list-presets | grep -q "dart-color" \
  && ok "presets are listed" || bad "presets are listed" ""

TMP=$(mktemp -d)
mkdir -p "$TMP/tok"
cat > "$TMP/tok/colors.dart" <<'EOF'
const c = AppColors(
  textPrimary: Color(0xFF1A1A1A),
  surfaceMain: const Color(0xFFFFFFFF),
);
EOF
cat > "$TMP/cfg.json" <<'EOF'
{ "color": [{ "glob": "tok/*.dart", "preset": "dart-color" }], "shadow": [] }
EOF
OUT=$(py "$HERE/extract_tokens.py" --config "$TMP/cfg.json" --root "$TMP")
echo "$OUT" | grep -q "color *2" \
  && ok "extracts names and values with a preset" || bad "extracts with a preset" "$OUT"
echo "$OUT" | grep -q "Families with no tokens found: shadow" \
  && ok "an absent family is reported as a finding, not filled in" \
  || bad "absent family is reported" "$OUT"
rm -rf "$TMP"

# Non-Flutter path. One CSS file holds every family at once, which is the norm
# on the web — nameFilter is what splits them, and without it every family
# silently captures every token.
REACT="$SKILL/evals/fixtures/react-mini"
TMP=$(mktemp -d)
cat > "$TMP/cfg.json" <<'EOF'
{
  "color":   [{ "glob": "src/styles/tokens.css", "preset": "css-custom-property", "nameFilter": "^color-", "prefixStrip": "color-" }],
  "spacing": [{ "glob": "src/styles/tokens.css", "preset": "css-custom-property", "nameFilter": "^spacing-" }],
  "shadow":  []
}
EOF
OUT=$(py "$HERE/extract_tokens.py" --config "$TMP/cfg.json" --root "$REACT")
echo "$OUT" | grep -qE "color +12" \
  && ok "CSS custom properties extract on the React fixture (no Flutter, no npm install)" \
  || bad "CSS custom property extraction" "$OUT"
echo "$OUT" | grep -qE "spacing +5" \
  && ok "nameFilter separates families sharing one file" \
  || bad "nameFilter separates families" "expected 5 spacing tokens, not all 23:
$OUT"
echo "$OUT" | grep -q "Families with no tokens found: shadow" \
  && ok "the React fixture's absent shadow family is reported too" \
  || bad "react absent family" "$OUT"
rm -rf "$TMP"

# Light and dark schemes normally share one file under the same token names.
# Without a bound you silently get whichever appears first.
TMP=$(mktemp -d); mkdir -p "$TMP/tok"
cat > "$TMP/tok/schemes.dart" <<'EOF'
static const lightColors = AppColors(
  textPrimary: Color(0xFF030712),
);
static const AppColors darkColors = AppColors(
  textPrimary: Color(0xFFFAFAFA),
);
EOF
cat > "$TMP/ok.json" <<'EOF'
{ "color": [{ "glob": "tok/*.dart", "preset": "dart-color",
              "between": ["static const lightColors", "static const AppColors darkColors"] }] }
EOF
OUT=$(py "$HERE/extract_tokens.py" --config "$TMP/ok.json" --root "$TMP")
{ echo "$OUT" | grep -q "0xFF030712" && ! echo "$OUT" | grep -q "declared twice"; } \
  && ok "between: scopes extraction to one theme mode" \
  || bad "between scopes to one mode" "$OUT"

cat > "$TMP/badend.json" <<'EOF'
{ "color": [{ "glob": "tok/*.dart", "preset": "dart-color",
              "between": ["static const lightColors", "NO SUCH MARKER"] }] }
EOF
OUT=$(py "$HERE/extract_tokens.py" --config "$TMP/badend.json" --root "$TMP")
echo "$OUT" | grep -q "end pattern" \
  && ok "between: an unmatched end pattern errors instead of silently mixing modes" \
  || bad "unmatched end pattern errors" "$OUT"
rm -rf "$TMP"

# ------------------------------------------------------------------- templates
head_ "templates"

for f in "$SKILL"/templates/*.json; do
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" \
    && ok "$(basename "$f") parses" || bad "$(basename "$f") parses" ""
done

python3 - "$SKILL" <<'PY' && ok "flow-edges template declares all six edge kinds" || bad "flow-edges edge kinds" ""
import json, sys
k = json.load(open(sys.argv[1] + "/templates/flow-edges.template.json"))["meta"]["edgeKinds"]
need = {"action", "guard", "auto", "failure", "selfFailure", "back"}
sys.exit(0 if need <= set(k) else 1)
PY

python3 - "$SKILL" <<'PY' && ok "registry template has every section the ritual reads" || bad "registry sections" ""
import json, sys
r = json.load(open(sys.argv[1] + "/templates/figma-node-registry.template.json"))
need = {"_readme", "file", "pages", "variableCollections", "variableKeyIndex", "textStyles",
        "effectStyles", "components", "screenMasters", "stateFrames", "flowInstances",
        "namedVersions", "log", "nextSession"}
sys.exit(0 if need <= set(r) else 1)
PY

python3 - "$SKILL" <<'PY' && ok "profile template forces provenance and honest absence" || bad "profile schema" ""
import json, sys
p = json.load(open(sys.argv[1] + "/templates/project-profile.template.json"))
color = p["tokens"]["families"]["color"]
sys.exit(0 if ("evidence" in p and "absenceEvidence" in color and "finding" in color
               and p["screenshots"]["scaleCalibrated"] is False) else 1)
PY

grep -q "Signatures" "$SKILL/templates/acceptance-criteria.template.md" \
  && ok "acceptance criteria template keeps the signature block" \
  || bad "signature block" "without it, nothing gates the first drawing"

for section in "## A." "## B." "## C." "## D."; do
  grep -q "^$section" "$SKILL/templates/acceptance-criteria.template.md" \
    && ok "acceptance criteria has $section" || bad "acceptance criteria has $section" ""
done

grep -q "Session-start ritual" "$SKILL/templates/GROUND-TRUTH-RULES.template.md" \
  && ok "ground-truth template keeps the session ritual" || bad "session ritual" ""

# ------------------------------------------------------------------ frontmatter
head_ "skill frontmatter"

for skilldir in "$SKILL"/../*/; do
  name=$(basename "$skilldir")
  f="$skilldir/SKILL.md"
  [[ -f "$f" ]] || { bad "$name has a SKILL.md" ""; continue; }
  python3 - "$f" "$name" <<'PY' && ok "$name frontmatter" || bad "$name frontmatter" "name+description only; description must contain 'Use when'"
import sys, re
text = open(sys.argv[1]).read()
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
if not m: sys.exit(1)
keys = set(re.findall(r"^(\w[\w-]*):", m.group(1), re.M))
body = m.group(1)
namematch = re.search(r"^name:\s*(\S+)", body, re.M)
sys.exit(0 if keys == {"name", "description"}
         and namematch and namematch.group(1) == sys.argv[2]
         and "Use when" in body else 1)
PY
done

# ----------------------------------------------------------------------- report
printf '\n\033[1m%d passed, %d failed, %d skipped\033[0m\n' "$PASS" "$FAIL" "$SKIP"
[[ $FAIL -eq 0 ]] || exit 1
echo "Run it twice. A suite that is green once has not been proven green."
