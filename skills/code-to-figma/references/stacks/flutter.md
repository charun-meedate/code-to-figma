# Flutter — the proven path

This is the stack the whole method was built on, so the guidance here is
evidence rather than extrapolation.

**"Proven" means proven on one project, not on the stack.** Two later Flutter
codebases each broke something written from the first: the colour preset
matched only the ThemeExtension constructor idiom and read 0 of 52 colours from
a `static const` holder class, and this page assumed a single-layer theme when
a three-layer palette/semantic split is common. Both are fixed. Expect the same
kind of narrowness anywhere this page states a shape rather than a principle —
check the shape against the project in front of you.

## Contents

- Catalog: load the bundled skills
- Token sources
- Icons
- Flutter-to-Figma semantics that do not map
- Reference images and the app
- Web builds compile but do not always run
- Flow tracing

---

## Catalog: load the bundled skills

Do not improvise. Two skills ship in this repo and cover it:

- **`flutter-widgetbook-catalog`** — building a catalog on an app that already
  exists. Most of that work is the harness, not the stories: theme, i18n,
  router and navigator scaffolding that real widgets expect. Prove the harness
  on one widget before writing any others.
- **`flutter-catalog-page-stories`** — full screens with no backend. Dependency
  matrix first, three tiers of stand-in in preference order, per-story locator
  scopes, and the three ways headless tests fail.

Budget them separately: a component is minutes, a screen is a day, a flow is
several.

## Token sources

| Family | Usually |
|---|---|
| Colour | a `ThemeExtension` subclass — `final Color name;` declarations, values in the constructor call. Also `ColorScheme(` |
| Spacing / size / radius | commonly **one** `ThemeExtension` with `final double name;` for all three. Do not assume three files |
| Typography | a `ThemeExtension` of `final TextStyle name;` |
| Component geometry | a theme-data holder — button, input and app-bar shapes |
| Shadow | **often absent.** Check before assuming; inline `BoxShadow` across many files is a finding, not a token layer |

Presets: `dart-color` for the constructor call, `dart-double` for numbers. Note
that declarations and values live in different places in a `ThemeExtension` —
extract from the **assignment**, not the declaration.

**A mature Flutter design system is often three layers, not one:**

| Layer | Shape | Preset |
|---|---|---|
| Primitives | `class AppPalette { static const neutralLevel00 = Color(0xFF0D0D0D); }` | `dart-color` |
| Theme-blind statics | `static const white = AppPalette.white;` | `dart-ref` |
| Semantic, per mode | `factory AppColorsTheme.light() => AppColorsTheme(textDefault: AppPalette.neutralLevel00, …)` | `dart-ref`, bounded to one factory with `between` |

The middle and outer layers hold **references, not values** — a Dart
identifier is an alias exactly as `var(--x)` is, and `--resolve-aliases`
follows both. Extract the palette in the same run or nothing resolves. One
field-tested codebase had 226 such references and read as 100% comparable once
the palette was included and the light factory bounded.

Bound the factory, not the file: `["factory AppColorsTheme\\.light\\(\\)",
"factory AppColorsTheme\\.dark\\(\\)"]`. Without it you get whichever mode
appears first, silently.

**Light and dark schemes normally sit in one file under the same token names**,
so bound the extraction or you silently take whichever comes first:

```json
{
  "color": [{
    "glob": "lib/**/styles/app_color_schemes.dart",
    "preset": "dart-color",
    "between": ["static const lightColors", "static const AppColors darkColors"]
  }],
  "spacing": [{ "glob": "lib/**/styles/app_theme_extension.dart", "preset": "dart-double" }],
  "shadow": []
}
```

That config, run against the codebase this method was proven on, yields **95
colours and 43 numbers — the same 138 tokens** that were verified value-exact
against Figma.

## Icons

Material icon fonts are already installed in Figma — `Material Icons`,
`Material Icons Round`, `Material Icons Sharp`, `Material Symbols Rounded`,
`Material Symbols Sharp`. Create a text node, type the **ligature name**
(`check` for `Icons.check_rounded`), set the size and line height to the code's
size. Match the family to the suffix in the code's icon name. You get the real
glyph — hand-drawing one was a mistake made and reversed on the proven run.

The app's own icons come from the asset directory as real files.

## Flutter-to-Figma semantics that do not map

- **`Expanded` still occupies space when its child is empty.** A hidden
  auto-layout child in Figma is removed from the flow and everything below
  moves up. Hide the inner child, never the slot.
- **`FittedBox(scaleDown)` has no Figma equivalent.** Rescaling the group
  reproduces the geometry but breaks the text-style binding — the node then
  shows as a style with an override. Log it.
- **`OutlineInputBorder` paints inside the box**, not straddling the edge.
- **Material inserts an 8px gap** between an icon and a label in a button
  child that no code line mentions. Measure the rendered result.

## Reference images and the app

The catalog's gallery export is the evidence base. Its export surface is
typically 390×844 at 2× — so **every measurement off an image is divided by 2.**

For comparing against the real app, drive it through the debug/VM channel from
inside the process rather than with `simctl openurl`: iOS shows a confirmation
dialog for externally-opened custom-scheme URLs, it lands in the screenshot,
and it survives an app restart. Read back where the router actually landed —
a redirect guard may have moved it.

## Web builds compile but do not always run

A catalog that builds for web can still show a blank frame at runtime:
`dart:io` members throw under dart2js, so any widget reaching `Platform.isX`
renders nothing. It compiles, it deploys, it is empty.

The corrected rule, measured: importing a widget that contains `dart:io` is
fine. What actually fails is handing a `dart:io` `File` to an image widget
that conditionally exports `File` per platform. Use `defaultTargetPlatform`
instead of `Platform.isX`, and the conditionally-exported `File`.

**Only screenshots catch a blank frame.** A build gate and a test suite both
pass. This is why the published artifact on the proven run was the rendered
gallery, not the web catalog.

## Flow tracing

Check which router the project actually uses before assuming:

| Router | Where the graph is |
|---|---|
| `go_router` | the route tree plus the redirect guard |
| `auto_route` | the generated router file |
| **GetX** (`package:get`) | a `app_pages.dart` / `getPages` list — a real route table; then `Get.to`/`Get.offNamed` call sites. GetX also supplies DI and state, so a GetX project needs none of the get_it or bloc harness advice above |
| plain `Navigator` | `onGenerateRoute`, plus `Navigator.push` call sites — the most work to trace, since there is no table |

**Two routers in one pubspec is common and is not a contradiction** — a field-tested project declared both `get` and `go_router`. Usually one is legacy or is pulled in for its non-routing features (GetX also supplies DI and state). Find which one actually builds the routes before tracing, and say which you traced.

For `go_router`, the route tree plus the redirect guard, plus the navigation
calls in each screen's state layer. The guard is worth its own node in
`flow-edges.json` with a `decisions` list — on the proven run guard edges and
self-failure edges together outnumbered plain user actions, which is a useful
thing for a design review to see.
