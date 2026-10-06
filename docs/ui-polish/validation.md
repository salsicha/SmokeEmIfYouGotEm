# Game-style front end and HUD — 2026-10-04

The menus and in-river interface were restyled as a game rather than a tool:

- **Painted art.** `RaftSimUIArt` paints an animated river valley in Slate geometry, with no
  textures or scene captures. It has a sky gradient and sun, hazy ridges with sunlit rims,
  forested foothills, a winding river with drifting highlights and flickering rapids, and
  birds. Each river has its own look: red-rock canyon, rainforest, glacial Patagonia,
  boreal volcanic Chilko, basalt Zambezi, foothill South Fork, and calm Guide School.
- **Main menu.** It has a branded title, Rivers / Expedition / Settings / Quit navigation,
  a guide-rank chip, and painted river cards with grade and region. A details strip names
  the focused river and its "set out" action, and a bottom bar shows keyboard and gamepad
  prompts. A narrow layout switches to two card columns.
- **Expedition and Settings.** Expedition shows a painted run card with mode, ready/locked
  status and previous/next/set-out actions. Every Settings row shows its live value.
- **Title and loading.** The title screen is cinematic, and the setting-out screen uses the
  chosen river's colours.
- **HUD.** It shows a river and clock card with a state chip, a route ribbon (raft marker
  and finish flag), a conditions card, and key prompts. Other panels: crew-call subtitles,
  a pulsing rescue banner, a "now running" title card, a painted crew-call wheel, a scout
  card, and a full-screen blurred pause menu.

Focus is as visible as pointer hover: each button switches to an amber frame when it has
keyboard or gamepad focus. Reduced motion freezes the painted scenes. Text scale and
colour-safe cues still apply.

Screens were captured from the editor build in `-game` mode with an ephemeral profile:
intro, rivers, expedition, settings, compact, and the South Fork HUD, pause, crew wheel,
title card and scout. The M6 and M7 shell and presentation automation suites were run
against this build.

# Intro and interface polish — 2026-10-04

## Delivered in the normal game

- A 3.2-second animated title, dismissible by click or key. Returning to the
  menu and the zero-motion preference skip it.
- Shared river/slate colors, original native vector contour artwork, readable
  typography, visible navigation focus, and responsive menu layout.
- Restyled river selection, career, settings, loading, and in-river panels.
- Real pause actions: resume, photo mode, restart checkpoint, return to rivers.
  Shell key bindings continue to work while the world is paused.
- A player/developer README with controls, build instructions, and a screenshot
  from the packaged game, not a mockup.

No river geometry, physics fields, or water solvers are changed by this work.

## Build and behavioral checks

The Unreal Engine 5.8 Windows Development editor and game compiled successfully.
A full BuildCookRun completed, including cooking and archiving. After the final
code-only pause-label and capture-timing fixes, the executable was rebuilt and
the package restaged using those cooked assets. Both packaging runs exited 0.

Final packaged game executable SHA-256:

```text
963DB515E3286F9500E81D9E901435553B8D87EC485CB7943A446FF974B7196B
```

All four native tests passed against the final editor build:

| Test | Result |
| --- | --- |
| `RaftSim.M6.MainMenuRender` | Success; intro dismissal, preserved run buttons, screen focus |
| `RaftSim.M6.RuntimeShell` | Success; actual world pause/resume, four action buttons, scout/photo controls |
| `RaftSim.M6.CareerCatalog` | Success |
| `RaftSim.M6.ProgressionMigration` | Success |

There were zero test errors. MainMenuRender reported one engine warning about
`r.MotionVectorSimulation` being read on the render thread without
`ECVF_RenderThreadSafe`; this warning is not represented as a clean warning-free
run. The other three tests had no warnings.

Local receipts: `tmp/ui-polish-final-tests/index.json`,
`tmp/ui-polish-final-editor.log`, `tmp/ui-polish-package.log`, and
`tmp/ui-polish-final-package.log`.

## Packaged visual review

Seven independent launches exited 0 and produced native UI-inclusive screenshots:
intro, rivers, career, settings, compact menu, South Fork pause, and South Fork
HUD. Standard captures were 1600×900; compact was 900×900. Each used an ephemeral
profile and no competing renderer. The front end used the normal boot map;
South Fork used its actual full-reach map and production game controller.

Screens were inspected for clipping, legibility, stable wrapping, focus styling,
and overlay placement. Pause capture now lets the real river initialize before
invoking the controller's pause action; it does not substitute a background.
No fatal/assert/ensure, GPU-crash, or video-memory-exhaustion messages appeared
in these capture logs. This is visual/UI validation, not an all-map frame-rate
or boat-physics acceptance claim.

Local screenshots, per-image hashes, and executable identity are in
`tmp/ui-polish-final-captures/index.json`. [main-menu.png](main-menu.png) is the
repository copy of the reviewed packaged river-selection screen, SHA-256:

```text
2684CD2CB54E7400F8A77A64185B0001C3E1052076EADE7FFC83E7BEF2FB9B72
```

To repeat the review, use `unreal/Scripts/capture_ui_polish.ps1` as documented
in the root README. Use a new capture prefix: existing evidence is preserved.
