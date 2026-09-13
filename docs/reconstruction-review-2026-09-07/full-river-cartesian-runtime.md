# South Fork Cartesian runtime integration prerequisites

2026-09-12. Previous turn PROGRESS; this turn PROGRESS. Full reconstruction,
normal-map integration, visual water acceptance and the overall goal remain open.

## Runtime changes

`FRaftSimLiveWaterWindow::TransferOverlapStateFrom` now copies native solver
values directly when both windows share an equal-resolution lattice. The old
path always passed through float-valued bilinear render sampling and its
0.0001 m wet threshold. That rounded depth/velocity and discarded momentum in
cells still wet under the solver's 0.000001 m threshold. Aligned transfers now
retain double-precision depth, both velocities and momentum; the receiving
solver recomputes stage in its own datum. Nonaligned legacy transfers retain
their existing interpolation. This change is installed in the existing normal
runtime, not hidden behind a scenario or diagnostic switch.

Native regression: 936 shared cells across signed X/Y moves retain exact state;
100 repeated handoffs retain total volume and shallow momentum; new cells keep
their seed, nonoverlapping windows do not inherit a clock, and a half-cell shift
still interpolates instead of snapping. Existing moving-window regression passes.

The runtime adapter now supports an explicit
`raftsim.cartesian_water_coordinate_map.v1` frame: hydraulic X=east, Y=north
relative to the common geographic world origin, with north reflected only at
the engine boundary and the NAVD88 datum applied once. It does not pretend that
easting is downstream progress or expose Cartesian bounds as a station range.
RunManager rejects Cartesian water coordinates as either an implicit fallback
or an explicit progress map; its separate geographic river axis remains the
scoring/checkpoint authority.

`FRaftSimCartesianWaterRegions` and the actual streaming actor now support
`raftsim.cartesian_water_streaming.v1`. Source selection requires the complete
requested XY crop plus one source-cell margin, retains the current source while
it still covers that crop, and fails closed outside coverage. Recenter tests
both signed axes and sends both coordinates to the solver. Manifest fields
explicitly supply extent, grid spacing, advance and Manning roughness; duplicate
sources and geometry-only manifests are rejected. Legacy station-based manifests
retain their original branch.

The common coordinate map is generated from the audited source-region bounds:
`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json`.
SHA256: `2b4cb3cb66c01c32dc2ec7171951e888a88fefdf5f76be1c8bf0c441131f9445`.
Its rectangle is only a broad-phase domain; it is not a claim of continuous wet
coverage or solved flow throughout that rectangle.

## Verification and retained failures

Builds completed with exit 0 in 135.50, 132.54, 38.25, 36.52 and 14.83 seconds.
The solver archive was not changed. Existing unrelated double-to-float warnings
in `RaftSimD6ChaosMeasuredRunner.cpp` remain, so this is not a clean release gate.

Initial `south-fork-exact-overlap-20260912/index.json`: four native checks pass.
The first full-route harness crashed in its duplicate-input test because UE
rejects adding an array's own element by reference. Fixed the harness by copying
the shared pointer before append. Crash log retained as
`unreal/Saved/Logs/south-fork-cartesian-regions-20260912.log`; no completed report
was emitted for that run.

`south-fork-cartesian-runtime-final-20260912/index.json` records SIX pass / ONE
fail, despite the command process returning 0. The controller fixture tried to
crop the bounded survey replay, which correctly requires its complete grid and
explicit MUSCL settings. That safeguard is unchanged. The controller regression
now uses the existing crop-compatible procedural gameplay fields strictly as
a controller test, NOT as reconstructed geography or full-river physics evidence.
The actual full-route selector test uses all 799 reconstructed source bounds and
all 52,689 axis/side probes: 3,567 source selections, maximum coordinate round-trip
error 2.03369197834e-12 m. Global progress still passes its 2,002-query 1 cm gate.

The corrected combined rerun completed at 07:43:59 UTC, terminal exit 0.
`south-fork-cartesian-runtime-v2-20260912/index.json` records SEVEN pass / ZERO
fail / ZERO test warnings. The actual controller creates crops at (120,0),
(120,12), and (108,12), preserves overlapping solver state and clock, and
avoids reloading on subthreshold motion. Both prior failures remain retained.
No owned editor/build/test process remains live. Python syntax checks pass and
the scoped diff whitespace check is clean. Normal-map and user-save hashes were
rechecked unchanged after verification.

## Hydraulic boundary evidence and next delivery work

`audit_south_fork_region_boundaries.py` verifies every geometry-packet hash and
examines captured water on each source edge. Of 799 regions:

- 577 have north/south-edge water; treating both edges as banks obstructs channels.
- 304 have no west-edge water; a universal west-edge inlet is not applicable.
- 137 have multiple wet segments on at least one edge.
- Wet-edge counts: west 495, east 512, south 415, north 429.

Evidence: `hydraulic_regions_context/boundary_geometry_audit.json`, SHA256
`074ada2dc06e02c7a54d833e1689ae3da85f67b01ea0d0c6fab0c19c49e0bcc1`.
Captured surface is not settled hydraulic stage, and this audit does not infer
boundary flow directions. Native `BoundaryCondition` currently has scalar
stage/depth/velocity per edge; the offline prescribed-discharge experiment is
west-only. Full geographic cooking needs suitable spatially varying / coupled
open-edge states and conservation/settling checks, not rotated terrain, bank
walls across real water, or bypassing the survey replay crop guard.

The normal map still uses the old terrain/flow. The new region packets contain
geometry, not solved velocity/discharge. No Cartesian streaming manifest has
been promoted, and no map or user save changed. The render carrier's
`RecenterCurvedGrid` still assumes one downstream axis and lateral center zero;
it also needs corresponding two-axis geometry and temporal-state handoff before
geographic Cartesian water can be displayed correctly. Do not mistake the new
solver-streaming branch for a completed render-carrier conversion.

Next delivery sequence: source-exact geographic hydraulic cooking with valid
edge treatment; two-axis render-carrier integration; coherent FullReach map,
material, global progress, start/sections/finish migration; inspect actual
gameplay motion and cost. Troublemaker stays inside South Fork and off the menu.
Breaking waves, convincing froth, all documented performance/robustness gates,
later rivers and final release/commit remain open.
