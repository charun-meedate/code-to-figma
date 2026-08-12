# Figma plugin API — traps that already cost a day

Every row was hit for real. Several **fail silently**: no exception, no warning,
the property simply does not take. Read this before the first Figma write of
the programme.

| What was tried | What happened | What to do instead |
|---|---|---|
| `figma.saveVersionHistoryAsync()` | ❌ not a supported API here | Figma still autosaves, but a script cannot *name* a version. A human names them in the UI at each checkpoint. Recovery is the registry plus the checklist. |
| Variable scope `"STROKE"` | ❌ not a valid enum value | `"STROKE_COLOR"` for colour, `"STROKE_FLOAT"` for weight |
| `resize()` and moving on | ⚠️ silently resets sizing to FIXED on **both** axes, so auto-layout clips content and stops wrapping | After every `resize()`, set `layoutSizingHorizontal` / `layoutSizingVertical` again |
| `LineNode.strokeCap = "ARROW_EQUILATERAL"` | ⚠️ puts an arrowhead on **both** ends | `createVector()` + `setVectorNetworkAsync()`, stroke cap set per vertex |
| `layoutSizingHorizontal = "FILL"` on a child of a plain frame | ❌ throws — only valid inside auto-layout | If the parent positions absolutely, just `resize()` |
| A paint bound to a variable but left with `color: {0,0,0}`, on a node with opacity < 1 | ⚠️ renders **black** — the binding does not resolve. Cost a wrong grey on a highlight that should have been a brand colour at 10% | Write the token's real value into `color` as well, read from `variable.valuesByMode[modeId]` — never hand-typed — then bind over it |
| `opacity` inside a paint object that is bound to a variable | ⚠️ keeps the opacity, drops the binding. Spreading `{...paint, opacity}` keeps the binding and drops the opacity | Make the paint fully opaque; set transparency on `node.opacity` |
| Setting `x`, `y`, `resize()`, `constraints` or `name` on a node **inside an instance** | ❌ cannot be overridden — and some of them, `resize()` included, fail **silently** | Design masters so size flows: auto-layout plus grow. Anything that must genuinely change size becomes a **variant**. The only overridable things are text content, visibility, variant properties, and fills/strokes |
| `visible = false` on a node inside an instance | ⚠️ **one-way.** The node disappears from queries, from `.children`, and by-ID lookup returns null. You cannot turn it back on | Hide last, and hide from the inside out. If you hide the wrong thing, delete the instance and build it again |
| Hiding an auto-layout child to "make it empty" | ⚠️ auto-layout removes it from the flow and everything below shifts up — unlike a framework flex child, which still occupies its space when its content is empty | Hide the *inner* child only; never the layout slot itself |

## Things Figma already has — do not draw them

| What you need | Use this |
|---|---|
| Icons from a standard icon font | The font is very likely already installed. Create a text node and type the **ligature name** at the size the code specifies. You get the real glyph. On the proven run an icon was hand-drawn as vectors before anyone checked — and the correction became a deviation row |
| The product's own icons and images | Upload the real asset files and import as vector trees or image fills. Never redraw |

## The structural lesson

Most of these are the same mistake in different clothes: **an instance is not a
free-form copy.** Figma's model is that a master defines structure and an
instance varies content. Anything you want to vary structurally has to be
designed as a variant up front.

That has a direct consequence for how you build masters. Auto-layout that
mirrors the real component tree, sized by its content, survives every
override you will later want. A master built with absolute positions and fixed
sizes has to be rebuilt the first time a state needs a different height.

Two smaller ones worth internalizing: **write real values alongside bindings**,
because a binding is a reference and a reference can fail to resolve at render
time; and **verify the write, do not assume it.** Several of these traps fail
without raising anything at all, so a script that reports success is reporting
that it finished, not that it worked.
