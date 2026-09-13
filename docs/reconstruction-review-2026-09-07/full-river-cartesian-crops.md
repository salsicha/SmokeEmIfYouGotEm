# Cartesian live-water crop boundaries — September 12

Runtime implementation rebuilt; seventeen native runtime checks pass. This is
an integration prerequisite, not a delivered full-river scene or visual acceptance.
South Fork remains the scenario; Troublemaker remains a rapid inside that run.

## Explicit cooked-source contract

`FRaftSimLiveWaterWindow::CreateFromCookedFields` now recognizes
`solver.runtime_cartesian_coupled_config=true` only with root
`coordinate_system="cartesian_east_north_m"`. It retains the source lattice,
second-order MUSCL/HLL evolution, authored Manning roughness, bed-slope source,
and unforced/no-mass-correction settings. The caller's Manning must match the
manifest. Hydraulic-crux relocation, survey-replay configuration, and whole-river
west discharge on an internal crop are rejected.

Each west/east/south/north boundary receives TWO exact source-cell layers, nearest
first, with signed h/u/v and bed in the crop's internal vertical datum. Incomplete
halos fail closed. All source bed/depth/velocity values are checked, including
cells outside the initial crop. Absolute source elevation is restored when
sampling; no legacy travelling bake-wave is added to this Cartesian surface.

These are fixed ghost states from the eventual accepted cooked snapshot, not
live bidirectional simulation of all 826 tiles during gameplay. A settled source
and actual runtime drift/handoff checks remain necessary. Do not use the evolving
warm-start state as an accepted steady boundary.

The separate `runtime_replay_offline_config` full-grid/discharge guard is retained.
Legacy first-order sources and their existing crop behavior are unchanged.
No new physical `discharge_profile` runtime package is enabled: the installed
archive's existing plain `ghost` implementation supplies this crop path.

Streaming manifests can explicitly declare `source_context_cells=3` (or larger
integer): two ghost layers plus one cell of outward crop rounding. Native source
selection reserves this margin on all sides. Omitted context retains the legacy
one-cell behavior; an explicitly undersized/nonintegral margin is rejected.

## Regressions and rebuild

`physics/scripts/prepare_cartesian_runtime_fixture.py` generates five hashed NPY
arrays and nine analytic manifest variants in `tmp/cartesian-runtime-crop-fixture-v1`.
It requires only Python's standard library. This fixture is not river geometry,
measured flow, settled water, or a visual-quality reference; it is not staged.

New native `RaftSim.M3.CartesianCropBoundaries` checks exact two-layer state,
signed westward/northward velocities, internal/absolute datum, all initial
numerical face fluxes against the uncropped MUSCL source, and ten runtime steps
against an explicitly configured reference solver. It also checks all four
missing-halo directions, crux relocation, wrong frame/roughness, first order,
forcing, mass correction, physical-inlet/replay conflicts and legacy behavior.
The existing full-route source-selector regression now requests three context
cells over all 52,689 actual river-axis/side probes.

Initial restricted build session 34134 stalled before compilation; its owned
dotnet PID 716 was stopped, session terminal exit 1. Approved rebuild session
34086 completed all 36 actions, exit 0, 232.73 seconds; log:
`unreal/Saved/Logs/south-fork-cartesian-crop-build-escalated-20260912.log`.
Two existing C4305 damping-literal warnings remain in the measurement runner;
this is not a clean release gate.

Native runtime session66261 completed exit 0 at 09:27:51 UTC. Exported report
`unreal/Saved/RaftSimValidation/south-fork-cartesian-crops-v1-20260912/index.json`
records 17 successes, zero failures, zero test warnings/errors and no tests left
running. The crop test verifies 96 exact ghost cells, ZERO difference for every
initial face flux and ZERO ten-step state difference. Full-route selection passes
52,689 probes / 5,603 source selections with maximum round-trip error
2.03369197834e-12 m. Both menu/catalog and progression migration pass, as do the
existing XY handoff, carrier, spray and water-support/presentation regressions.
Engine startup platform-SDK/Toolsets/Python/NullRHI diagnostics remain separate
from this zero-test-warning result.

Actual-game crew/scoring regression session80963 completed exit 0 at 09:29:18
UTC under `-game -NullRHI -RaftSimEphemeralProfile`. Exported report
`unreal/Saved/RaftSimValidation/south-fork-cartesian-crops-gameplay-20260912/index.json`
records two successes and zero test errors/warnings: crew commands 6.518 seconds,
scoring/saving 28.427 seconds including setup. No visual acceptance is inferred
from a NullRHI test. Both editor processes and the rebuild are terminal.

At 09:29 UTC the installed native archive remains e69772d2..., the normal map
remains e77da92b..., and the user's saved game remains 181d1e57... (unchanged
SHA256s). Free space is 3,793,698,816 bytes. No data deletion or commit occurred.
The same full-river cook is alive at step1200 / 60 simulated seconds, max depth
4.223701 m, speed12.167506 m/s, max step mass residual1.0942824e-8 m3. Inlet
45.3069545472 m3/s versus outlet24.929496 m3/s remains transient, not settled.

## Remaining flow-direction integration

Code inspection identifies actual X-as-downstream assumptions still requiring
conversion before normal Cartesian-map delivery:

- Carrier hydraulic-curvature sampling uses +/- X instead of local current.
- Breaking detection finds the upstream Froude transition only at smaller X;
  tailwater lift walks only toward larger X.
- Shore/edge coverage and candidate bucketing are organized by X columns.
- Plunge, boil, roller and boulder-eddy presentation interprets relative XY as
  along/across; their support/presentation must share a local flow frame.
- The runtime adapter's matching hydraulic-relief support samples +/- X too.
- Refined crest atlas currently stores site position/dimensions without local
  orientation; shader/CPU reconstruction must agree if enabled on this frame.

Do not rotate just the visible lip and leave support or foam in the old frame.
Retain signed-current/rotation-equivalence tests and real game comparison gates.

The existing full-river solve remains session63136/PID36216, output
`tmp/south-fork-coupled-flow-600s-v2-20260912`; do not duplicate/restart it or
overwrite its executable. Its eventual completion is not automatic settling
acceptance. Source export/coverage, coherent normal FullReach terrain/material/
route/start/section/finish integration, breaking/froth realism and performance
remain open, as do all later items in the active goal.
