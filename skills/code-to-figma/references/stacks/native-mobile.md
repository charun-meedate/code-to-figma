# SwiftUI and Jetpack Compose

**Status: contract-level, not proven.** The extraction points and capture
mechanics below are correct for these platforms, but no full programme has run
on them from this skill. Treat the specifics as a starting position to confirm
against the project, and say so to whoever is relying on the result. The
invariants — criteria first, one approved pilot, registry as truth, values
from source — hold regardless.

## The hard part is the catalog, and it is mostly missing

**SwiftUI previews cannot be exported in bulk.** `#Preview` renders in Xcode's
canvas; there is no supported way to walk every preview and write a PNG per
state. Treat a project with previews as **no catalog** and read
`evidence-without-storybook.md`.

What does exist, in rough order of cost:

- **Snapshot tests** (`swift-snapshot-testing`, Paparazzi on Android) render a
  view to an image in a test. This is the closest thing to a gallery export
  and is the recommended path when screens are in scope: a snapshot test per
  state gives exactly the reference images the method wants, and Paparazzi in
  particular renders Compose without a device.
- **Compose previews** are better served than SwiftUI: `@Preview` plus
  Paparazzi or Showkase gets you an enumerable catalog with screenshots.
- **Simulator/emulator capture** for whatever is left.

If a project already runs snapshot tests, the evidence base exists and nobody
has called it a catalog. Check before proposing to build one.

## Token sources

**SwiftUI**

| Family | Where |
|---|---|
| Colour | `*.xcassets/**/Contents.json` colour sets — JSON, with `components` per appearance (light/dark/high-contrast). Also `extension Color { static let … }` |
| Typography | `Font.custom(` / `.system(` call sites; often no central definition |
| Spacing | frequently **absent** — literals at call sites. Verify before assuming |

Asset-catalogue colours are the one place native beats most stacks: the JSON
already carries light and dark as separate components, which maps onto Figma
variable modes directly. Note the colour space — `srgb` with float components
is common, `display-p3` appears too, and they are not the same value.

**Compose**

| Family | Where |
|---|---|
| Colour | `val Name = Color(0xFF…)` in a `Color.kt`; then `lightColorScheme(`/`darkColorScheme(` mapping primitives to roles |
| Typography | `Typography(` with `TextStyle(` per role |
| Spacing | a `Dimens` object or `val`s; often absent |

Compose has the same two-layer structure as a good web system: primitives,
then a semantic scheme referencing them. Model both in Figma and resolve the
aliases before diffing.

Presets: `swift-color`, `compose-color`. For asset catalogues use a small
custom walk over the JSON rather than a regex — the values are structured, and
parsing structured data with a regex is how you lose the alpha channel.

## Capture

```bash
# iOS
xcrun simctl list devices booted
xcrun simctl io booted screenshot out.png

# Android
adb exec-out screencap -p > out.png
```

Both capture at device scale, so `referenceScale` is 2 or 3 and the ÷ rule
applies. Calibrate on a known element before measuring anything.

Driving: prefer in-process navigation over external deep links, for the reason
in `evidence-without-storybook.md` — iOS puts a confirmation dialog in front of
an externally-opened custom-scheme URL, it lands in the screenshot, and it
outlives an app restart. UI-test targets (XCUITest, Espresso) can drive
navigation from inside the process and are the better channel where they exist.

## Flow tracing

- **SwiftUI**: `NavigationStack` paths and `navigationDestination`, sheet and
  fullScreenCover presentations, and any coordinator or router type the project
  has added. Presentation-driven navigation is often scattered across views —
  expect the trace to take longer than a centralized route table.
- **Compose**: the `NavHost` composable is a real route table; start there,
  then find `navController.navigate(` call sites.
- **UIKit remnants**: storyboard segues are XML and greppable, but a mixed
  project has two graphs. Trace both or scope one out explicitly.

Presented sheets and dialogs are edges too — `auto` when the system presents
them, `action` when a tap does.

## Icons

SF Symbols is a real font and Figma can use it if it is installed locally, but
it is licensed for Apple platforms — check before making it a dependency of a
shared design file. Material Symbols on the Compose side is already present in
Figma. Either way: the product's own assets come from the asset catalogue or
the drawable resources as real files, never redrawn.

## What to tell the team

Native has a harder evidence problem than web or Flutter, and the honest
consequence is that **the screens tier costs more here** or lands on the
code-only path. The tokens tier is unaffected and just as exact — asset
catalogues and Compose colour files parse cleanly. If budget is limited on a
native project, tokens plus a flow map is the highest-value combination.
