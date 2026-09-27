# Troublemaker: discharge-based inferred bed candidate

September27,2026. Physical candidate under test, not a visible delivered change
or reconstruction acceptance. Normal playable v5 remains untouched.

## Why this changes the next action

The completed v5 crest check found four persistent waves with zero modeled
spilling, while the actual submitted mesh approximated its crest target within
8.25mm at the sampled instant. More tessellation is not the supported first fix.
The full-river v2 bed builder explicitly protects Troublemaker's registered
rectangle, retaining its old shore-distance depth prior after the earlier
uncalibrated shelf/plunge ablation. Neither v2 nor the450s v5 field update
replaces that local inferred bathymetry.

At the four diagnosed hydraulic XY locations, route progress is approximately
8310,8330,8330 and8359m. The v2 design's UNBIASED normal depth is0.448..0.690m;
pool weights are0..0.001874. Its fitted centreline depths reach the0.25m lower
clip here. This candidate deliberately does not use that simulated bias or
claim the unsteady flow used to fit it was settled.

## Source-preserving construction

`physics/scripts/prepare_troublemaker_conveyance_bed.py` extends the existing
strip-conveyance depth inference into the registered rapid. The authored
45.3069545472m3/s scenario flow, captured surface slope, effective width,
Manning n0.035, bank-shape length and2.2m pool prior come from the existing
full-river design. The flight-time discharge remains unknown. These assumptions
are NOT surveyed underwater shape or a calibrated reconstruction of the hole.

Only authority2 vertices change. All captured ground/rock, inferred rock
flanks, source surface, XY, connectivity, return indices and the registered
seam boundary remain exact. A30m smooth taper retains the boundary; no original
source file is overwritten. The same registered-triangle sampler validates
both mesh and hydraulic input. New tests reject unknown authority, invalid
designs, extrapolation and above-surface editable beds.

Candidate: `tmp/troublemaker-conveyance-bed-v1-20260927`.
Mesh SHA-256: `3fd9eef54ff243c09fe7c33aa69129a3496387d7d603012a543457fb1cf14542`.
Parent mesh SHA-256: `8edf8a7fbfb675a22ac6736db600a3300f018f1c9037b1c0674bc1c376cfcca7`.
Changed62,985 inferred vertices; height change min/median/max
-0.425195/+0.672117/+1.941739m. The amount of change is substantial: a fresh
flow solve and matching terrain/collision are mandatory, not optional.

The rock union is retained exactly. This does not resolve the separate
interpreted rock-envelope versus hydraulic-roof uncertainty. The new
`--geometry` argument in `prepare_south_fork_discharge_bed_cook.py` permits an
explicit registered revision while retaining the existing default unchanged.
The normal v2 coarse terrain is then applied everywhere it previously owned.

## Completed preparation and tests

Union preparation `tmp/troublemaker-conveyance-union-v1-20260927` checks all841
cores/5,382,400 cells and retains masks, captured stages and physical endpoint
faces. Its16,383 changed cells are relative to pre-union geometry, NOT v5.

The independent [comparison to current v2](runtime450-evidence/conveyance-input-comparison.json)
instead finds16,064 changed hydraulic cells in11 cores, all inside the
registered rapid. Every grid, timestep, roughness and physical boundary is
identical across all841 packages. This is source/input parity, not settled
hydraulics or actual native collision qualification.

Full-river fresh input:
`tmp/troublemaker-conveyance-full-input-v1-20260927/full/manifest.json`.
SHA-256: `b9c8cabadff5f72b396b389cd77b94193a530138d07a9dc1c5c5cbd96d26a0b9`.
Preparation session3094 completed with exit0. No old-bed evolved state was
transferred. Initial water uses the captured surface and inferred conveyance
velocity, so initial transients are expected and must not be called improvement.

Six new unit tests pass; the combined new/terrain-revision/rock-union suite
passes46 in3.48s. Fresh test directory:
`tmp/troublemaker-conveyance-tests-20260927`. Tests are not visual acceptance.

## Live bounded solve: continue the same job

Native solver PID33592, helper session30490, start17:43:36.9708347Z onSeptember27.
Process receipt: `tmp/troublemaker-conveyance-process-v1-20260927.json`.
Output: `tmp/troublemaker-conveyance-full150-v1-20260927`.
Wrapper: `tmp/cook-troublemaker-conveyance-v1-20260927.ps1`.
Qualified executable SHA-256:
`458a1fcd3f2f12391012032398d29a4b2eadb792df2e9ee09b88dff263abc8e4`.
Bounded3000 steps at0.05s,150s target, snapshots at0/75/150s,8 offline lanes.
No competing engine/build/solver was present at guarded launch. Do not start
another cook while this one is live. The wrapper performs a final state audit
after successful native completion, but this does not replace bank/storage or
playable checks.

Independent initial snapshot checks pass5,382,400 finite nonnegative cells,
max depth2.671577m and speed6m/s. All86,720 artificial-bank cells are exactly
dry. Reports: `tmp/troublemaker-conveyance-initial-state-v1-20260927.json` and
`tmp/troublemaker-conveyance-initial-banks-v1-20260927.json`. Initial outflow
exceeds inflow: no initial equilibrium claim. The same live process reached
step110/5.5s without a logged safety failure; this is not final validation.

## Required follow-through

1. Poll that exact process/helper to completion; preserve failures. Check final
   native state, dry-bank exclusion, signed flux/storage balance and temporal
   regional changes. Do not compare a fresh150s transient to a450s evolved
   baseline as if the runs differed only in bed shape.
2. Inspect actual local drop/jump/recirculation behavior and bed continuity;
   numerical safety alone cannot justify promotion. No lower Froude/shoreline
   gates, decorative extra foam sheets or broken alternative solver.
3. If physically defensible, use this SAME registered mesh for rendered ground
   and collision, resample matching runtime packets, then incrementally install
   the normal FullReach candidate with a versioned bundle and rebuild. Inspect
   real motion, shoreline, support/collision consistency and cost; do not leave
   the candidate as the final offline-only deliverable.
4. South Fork remains first unfinished, with20FPS/p95<=50ms and no frame>100ms,
   convincing single-surface breaking water and captured-reference fidelity
   still required. All later rivers and the wider goal remain open.
