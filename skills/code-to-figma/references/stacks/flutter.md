# Flutter — the proven path

This is the stack the whole method was built on, so the guidance here is
evidence rather than extrapolation.

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

`go_router` route trees plus the redirect guard, plus the navigation calls in
each screen's state layer. The guard is worth its own node in
`flow-edges.json` with a `decisions` list — on the proven run guard edges and
self-failure edges together outnumbered plain user actions, which is a useful
thing for a design review to see.
