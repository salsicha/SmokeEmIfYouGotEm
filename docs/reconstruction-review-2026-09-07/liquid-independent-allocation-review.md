# Explicit native XYZ allocation

September 10, 2026. The prior boundary-metric pass was progress. This pass
implements the allocator and connects it to the coupled-water path. South Fork
and the overall queue remain incomplete. No production scene promotion or commit.

## Implementation

Read the actual mounted `Grid3D_SetResolution` graph and its inputs in
[the focused module inspection](liquid-grid-allocation-modules.json). The engine
already provides an **Independent** mode with separate `Module.NumCellsX/Y/Z`.
The Max Axis branch computes near-isotropic cells and can round physical extents;
it cannot represent the prepared independent XYZ metric generally.

`RaftSimLiquidGridAllocation.h` now selects the existing Independent mode on the
one authoritative owned primary grid. It validates the input graph, sets XYZ
counts and a unit resolution multiplier, removes conflicting rapid-iteration
values, and preserves dependent Other Grid bindings. Engine scripts and saved
assets are not changed. The function rejects non-transient systems, invalid
dimensions, allocations beyond the existing 2,000,000 render-voxel cap, and
X dimensions incompatible with the current wide-stencil coloring.

The existing coupled-water halo path now calls this allocator for its exact
68 by 68 by 24 grid instead of setting only a maximum-axis count. Physical
extents, incoming sources, particles and terrain remain unchanged in that
regression path. Halo tests now check the explicit XYZ request rather than the
inactive maximum-axis setting.

## Actual rectangular allocation

[The v3 GPU check](liquid-independent-grid-allocation-v3/allocation.json) and
[capture record](liquid-independent-grid-allocation-v3/capture.json) verify:

- Five solver grids actually allocated at **68 by 36 by 24**, with matching
  game-thread and render-thread dimensions.
- One reconstruction grid and one render-target volume at **136 by 72 by 48**.
- The actual SDF material binds **3400 by 2700 by 800 cm** physical extents,
  correct unit axes and centre `(0,0,750)` cm for an actor at `(0,0,350)` cm.
- The Grid DI's own default 100 cm bbox is recorded but is not mistaken for the
  fluid's physical frame; that frame is checked from actual renderer bindings.
- Zero inlet, 30 callback frames, no engine errors. This is an allocation/frame
  test, not water physics, rapid appearance or a performance benchmark.

First capture failed on a Python capture-component accessor before simulation;
the report is retained. v2 verified allocation sizes; v3 added the physical-frame
check. The read-only module inspection editor ignored its quit command after
writing its report; that owned process (PID 31916) was explicitly closed, without
saving assets. One initial C++ build failed on TObjectPtr iteration syntax,
corrected before the successful builds.

## Coupled-water regression

[The actual 12-second replay](liquid-independent-coupled-regression/capture.json)
uses the installed allocator with water and RHI validation. Its
[clock](liquid-independent-coupled-regression/clock_audit.json),
[stage order](liquid-independent-coupled-regression/stage_order_audit.json),
[live pipeline](liquid-independent-coupled-regression/live_audit.json),
[affine transfer](liquid-independent-coupled-regression/affine_audit.json), and
[foam transport](liquid-independent-coupled-regression/current_foam_audit.json)
audits pass at unchanged tolerances. 757 reconstruction callbacks include 714
positive simulation-clock steps and 43 render-only callbacks. All 30 motion
frames differ. Final primary count 57,285, maximum live-position error 1.7594e-6 m,
affine error 3.4782e-6 per second against 0.001. No engine errors; the existing
SimCache volume warning remains. The 90.57 s blocking capture is not an FPS test.

Viewed `terrain_0720.png`: still a glossy/lumpy isolated water block, not a
convincing returning hole or breaking wave train. No realism acceptance.

190 liquid Python tests pass. Editor builds succeed. Five earlier headless
tests pass, and [six final actual-RHI tests](engine-liquid-independent-coupling/index.json)
pass without test warnings, including all fourteen coupling variants in the
grid-frame transfer test. Scoped diff whitespace check and capture-script syntax
check pass. Saved geographic-map SHA remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
All build, editor and audit processes from this pass are terminal.

## Next

The bounded v3 boundary decoder and allocator now exist, but v3 installation
still correctly refuses mismatched source/seed/frame state. Implement matching
bounded v2 source and initial-particle consumers with per-region coordinates,
then shared conservative particle/flow exchange and one continuous visible
surface across the complete source-aligned rapid. Do not truncate the final
region to satisfy coloring, relax capacity limits, reset water at internal
faces, or treat successful zero-inlet allocation as full-domain physics.
Whole-rapid GPU contacts, sources, wave/roller geometry, raft behavior, reference
motion and performance remain required before subsequent river work.
