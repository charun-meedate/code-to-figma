# Figma plugin API — traps that already cost a day

Every row was hit for real — but "for real" has a date on it, and the plugin
API moves. **Re-probed live on 2026-08-13; four of the seven testable rows had
drifted.** Two no longer reproduce at all, two were overstated. They are marked
below.

**Probe before you trust this page.** A trap table is the most perishable thing
in this skill: it describes someone else's API at a moment in time, and acting
on a retired trap costs you a workaround you did not need. The probe script is
twenty lines — create a throwaway node, attempt the thing, catch the error,
delete the node — and it is the difference between knowing and remembering.

Several of the live ones **fail silently**: no exception, no warning, the
property simply does not take. Read this before the first Figma write.

| What was tried | What happened | What to do instead |
|---|---|---|
| `figma.saveVersionHistoryAsync()` | ❌ not a supported API here | Figma still autosaves, but a script cannot *name* a version. A human names them in the UI at each checkpoint. Recovery is the registry plus the checklist. |
| Variable scope `"STROKE"` | ❌ not a valid enum value | `"STROKE_COLOR"` for colour, `"STROKE_FLOAT"` for weight |
| `resize()` and moving on | ⚠️ still silently resets sizing — but on the **resized axis only**, not both. Probed 2026-08-13: an auto-layout frame at HUG/HUG became FIXED/HUG after `resize(200, 100)` | After every `resize()`, set `layoutSizingHorizontal` / `layoutSizingVertical` again. The advice is unchanged; only the blast radius was overstated |
| `LineNode.strokeCap = "ARROW_EQUILATERAL"` | ⚠️ puts an arrowhead on **both** ends | `createVector()` + `setVectorNetworkAsync()`, stroke cap set per vertex |
| `layoutSizingHorizontal = "FILL"` on a child of a plain frame | ❌ throws — only valid inside auto-layout | If the parent positions absolutely, just `resize()` |
| ~~A paint bound to a variable but left with `color: {0,0,0}`, on a node with opacity < 1~~ | ✅ **RETIRED 2026-08-13** — `setBoundVariableForPaint` now resolves the variable's value into the returned paint, so `color` is never left at zero. Probed: the paint came back holding the real value | Nothing needed. Still capture the returned paint — it is a new object, not a mutation |
| ~~`opacity` inside a paint object that is bound to a variable~~ | ✅ **RETIRED 2026-08-13** — probed `{...boundPaint, opacity: 0.4}`: both the opacity **and** the binding survived | Nothing needed |
| Setting `x`, `y`, `resize()` or `constraints` on a node **inside an instance** | ❌ still throws: `This property cannot be overridden in an instance: relative-transform`. **But `name` IS overridable** — the original row listed it and that was wrong (probed 2026-08-13) | Design masters so size flows: auto-layout plus grow. Anything that must genuinely change size becomes a **variant**. Overridable: text content, visibility, variant properties, fills/strokes, **and name** |
| `visible = false` on a node inside an instance | ⚠️ **one-way.** The node disappears from queries, from `.children`, and by-ID lookup returns null. You cannot turn it back on | Hide last, and hide from the inside out. If you hide the wrong thing, delete the instance and build it again |
| Hiding an auto-layout child to "make it empty" | ⚠️ auto-layout removes it from the flow and everything below shifts up — unlike a framework flex child, which still occupies its space when its content is empty | Hide the *inner* child only; never the layout slot itself |

## Things Figma already has — do not draw them

| What you need | Use this |
|---|---|
| Icons from a standard icon font | The font is very likely already installed. Create a text node and type the **ligature name** at the size the code specifies. You get the real glyph. On the proven run an icon was hand-drawn as vectors before anyone checked — and the correction became a deviation row |
| The product's own icons and images | Upload the real asset files and import as vector trees or image fills. Never redraw |

## Probe status

| Row | Last probed | Verdict |
|---|---|---|
| Variable scope `"STROKE"` | 2026-08-13 | reproduces — invalid enum, throws |
| `resize()` resets sizing | 2026-08-13 | reproduces, **one axis not both** |
| `FILL` on a plain-frame child | 2026-08-13 | reproduces — throws |
| `x`/`constraints` inside an instance | 2026-08-13 | reproduces · **`name` does not — it is overridable** |
| `visible = false` inside an instance | 2026-08-13 | reproduces — child count drops to 0, unreachable |
| Bound paint left at `{0,0,0}` | 2026-08-13 | **retired** |
| `opacity` spread into a bound paint | 2026-08-13 | **retired** |
| `saveVersionHistoryAsync` | not re-probed | inherited |
| `ARROW_EQUILATERAL` on both ends | not re-probed | inherited |
| Hiding an auto-layout child shifts siblings | not re-probed | inherited |

Three rows carry the original programme's date and nothing more. Treat them as
leads, not facts, and re-probe before designing around one.

## The structural lesson

Most of these are the same mistake in different clothes: **an instance is not a
free-form copy.** Figma's model is that a master defines structure and an
instance varies content. Anything you want to vary structurally has to be
designed as a variant up front.

That has a direct consequence for how you build masters. Auto-layout that
mirrors the real component tree, sized by its content, survives every
override you will later want. A master built with absolute positions and fixed
sizes has to be rebuilt the first time a state needs a different height.

And one that outlived the two traps it came from: **verify the write, do not
assume it.** Several of these fail without raising anything, so a script that
reports success is reporting that it finished, not that it worked. That is also
how the two retired rows were caught — by reading back what the API had
actually stored instead of trusting the note that said what it would store.
